"""RadConnectome — fruit fly brain wiring mapped into Rad.

The male *Drosophila* CNS connectome (Google Research + HHMI Janelia + Cambridge,
166,000+ neurons, 50M+ synapses) is the blueprint. Rad's runtime maps onto it:

    swarm population  ->  neural population
    blackboard        ->  connectome (the wiring diagram itself)
    agents            ->  neurons (planner, coder, tester, ...)
    tools             ->  synapses (write_file, run_shell, recall, ...)
    memory HNSW       ->  vector connectome (semantic wiring)
    EvolveMem/MemSkill->  synaptic plasticity (STDP-like)
    verification      ->  no silent synapses (every edge must verify)
    trace/replay/why  ->  neuPrint (query any path, see lineage)
    sidecar           ->  ventral nerve cord (local loops survive restart)
    voice TEN         ->  auditory pathway
    vision roboflow   ->  optic lobes
    x402 marketplace  ->  neuromodulator economy (USDC = dopamine)

Design rules (same as the rest of Rad):
* The graph is *observed*, never invented: edges come from real tool calls
  recorded in objective events. No edge without evidence.
* Plasticity is Hebbian/STDP-like and bounded: verified success strengthens
  (+), failure weakens (-), everything decays toward a floor. Nothing explodes.
* Rich-club routing is advisory: hubs are *suggested* first, never forced.
  The control plane still decides; VERIFIED-only law holds.
* Sleep replay consolidates: `rad sleep` replays the day's edges, prunes weak
  synapses below threshold, archives (never deletes) the pruned ones.
* Everything is a human-readable JSON file under `~/.rad/connectome/`.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome, _read_json, _write_json

# ---------------------------------------------------------------- constants

# STDP-like plasticity bounds (kept small and safe by design)
LTP_STEP = 0.05      # long-term potentiation: verified success strengthens
LTD_STEP = 0.08      # long-term depression: failure weakens (stronger, safety-first)
DECAY_RATE = 0.01    # per-sleep decay toward floor
W_FLOOR = 0.05       # weakest a live synapse can be
W_CEIL = 1.0         # strongest a synapse can be
W_INIT = 0.5         # newborn synapse weight
PRUNE_BELOW = 0.10   # sleep replay prunes edges below this (archived, not deleted)

# Rich-club: top fraction of nodes by degree treated as hubs
RICH_CLUB_FRAC = 0.30

# Fly-brain region map: Rad modules grouped like Drosophila neuropils.
# The projectome is the region-to-region projection map.
REGIONS: Dict[str, List[str]] = {
    "mushroom_body": ["memory", "recall", "remember", "world"],      # learning/memory
    "central_complex": ["objective", "plan", "controller"],           # navigation/decision
    "optic_lobes": ["see_image", "vision", "browser"],                # vision
    "antennal_lobe": ["chat", "listen", "say", "voice"],              # smell/hearing ~ chat/voice
    "ventral_nerve_cord": ["sidecar", "serve", "desktop"],            # motor/local loops
    "neurosecretory": ["x402", "skills", "marketplace"],              # modulators/economy
}

NODE_KINDS = ("agent", "tool", "region", "memory")


# ---------------------------------------------------------------- data types

@dataclass
class Synapse:
    """One weighted edge: pre -> post. The fly-brain synapse."""
    pre: str
    post: str
    weight: float = W_INIT
    successes: int = 0
    failures: int = 0
    last_fire: float = 0.0
    verified: bool = False   # True only if a machine check confirmed this path

    def to_dict(self) -> Dict[str, Any]:
        return {"pre": self.pre, "post": self.post, "weight": self.weight,
                "successes": self.successes, "failures": self.failures,
                "last_fire": self.last_fire, "verified": self.verified}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Synapse":
        return cls(pre=d["pre"], post=d["post"], weight=float(d.get("weight", W_INIT)),
                   successes=int(d.get("successes", 0)), failures=int(d.get("failures", 0)),
                   last_fire=float(d.get("last_fire", 0.0)),
                   verified=bool(d.get("verified", False)))


@dataclass
class Neuron:
    """One node: an agent, tool, memory layer, or region."""
    name: str
    kind: str = "tool"
    region: str = ""
    fires: int = 0
    first_seen: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind, "region": self.region,
                "fires": self.fires, "first_seen": self.first_seen}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Neuron":
        return cls(name=d["name"], kind=d.get("kind", "tool"),
                   region=d.get("region", ""), fires=int(d.get("fires", 0)),
                   first_seen=float(d.get("first_seen", 0.0)))


def region_of(name: str) -> str:
    """Map a node name to its fly-brain region (projectome)."""
    low = name.lower()
    for region, members in REGIONS.items():
        for m in members:
            if m in low:
                return region
    return "central_complex"  # default: decision neuropil


def kind_of(name: str) -> str:
    low = name.lower()
    if low in ("planner", "researcher", "coder", "tester", "reviewer",
               "writer", "analyst", "security", "browser_agent"):
        return "agent"
    if low in ("episodic", "semantic", "procedural", "memory"):
        return "memory"
    if low in REGIONS:
        return "region"
    return "tool"


# ---------------------------------------------------------------- the connectome

class Connectome:
    """The wiring diagram. Observed from real runs, plastic via STDP, pruned in sleep.

    Persistence: `~/.rad/connectome/graph.json` (live) + `archive/` (pruned).
    """

    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.root = home.root / "connectome"
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "archive").mkdir(exist_ok=True)
        self.neurons: Dict[str, Neuron] = {}
        self.synapses: Dict[Tuple[str, str], Synapse] = {}
        self._load()

    # ---- persistence

    @property
    def graph_path(self) -> Path:
        return self.root / "graph.json"

    def _load(self) -> None:
        d = _read_json(self.graph_path, {})
        for nd in d.get("neurons", []):
            try:
                n = Neuron.from_dict(nd)
                self.neurons[n.name] = n
            except Exception:
                continue
        for sd in d.get("synapses", []):
            try:
                s = Synapse.from_dict(sd)
                self.synapses[(s.pre, s.post)] = s
            except Exception:
                continue

    def save(self) -> None:
        _write_json(self.graph_path, {
            "version": 1, "updated": time.time(),
            "neurons": [n.to_dict() for n in self.neurons.values()],
            "synapses": [s.to_dict() for s in self.synapses.values()],
        })

    # ---- recording (edges come from real tool calls, never invented)

    def ensure_neuron(self, name: str, kind: str = "") -> Neuron:
        if name not in self.neurons:
            self.neurons[name] = Neuron(name=name, kind=kind or kind_of(name),
                                        region=region_of(name), first_seen=time.time())
        return self.neurons[name]

    def fire(self, pre: str, post: str, verified: bool = False,
             success: Optional[bool] = None) -> Synapse:
        """Record one pre -> post firing. Applies STDP-like plasticity.

        success=True  -> LTP (strengthen, bounded by W_CEIL)
        success=False -> LTD (weaken, bounded by W_FLOOR)
        success=None  -> just record the firing, no weight change
        """
        self.ensure_neuron(pre)
        self.ensure_neuron(post)
        self.neurons[pre].fires += 1
        key = (pre, post)
        s = self.synapses.get(key)
        if s is None:
            s = Synapse(pre=pre, post=post)
            self.synapses[key] = s
        s.last_fire = time.time()
        if verified:
            s.verified = True
        if success is True:
            s.weight = min(W_CEIL, s.weight + LTP_STEP)
            s.successes += 1
        elif success is False:
            s.weight = max(W_FLOOR, s.weight - LTD_STEP)
            s.failures += 1
        return s

    def record_sequence(self, names: List[str], verified: bool = False,
                        success: Optional[bool] = None) -> int:
        """Record a chain a -> b -> c ... Returns edges recorded."""
        n = 0
        for a, b in zip(names, names[1:]):
            self.fire(a, b, verified=verified, success=success)
            n += 1
        self.save()
        return n

    # ---- neuPrint-like queries

    def neighbors(self, name: str, direction: str = "out",
                  limit: int = 20) -> List[Synapse]:
        """Upstream (in) or downstream (out) synapses, strongest first."""
        out = [s for (a, b), s in self.synapses.items()
               if (b == name if direction == "in" else a == name)]
        out.sort(key=lambda s: -s.weight)
        return out[:limit]

    def path(self, src: str, dst: str, max_hops: int = 4) -> Optional[List[str]]:
        """Shortest verified-first path src -> dst (BFS, strong edges first)."""
        if src == dst:
            return [src]
        adj: Dict[str, List[str]] = {}
        for (a, b), s in self.synapses.items():
            adj.setdefault(a, []).append(b)
        for v in adj:
            adj[v].sort(key=lambda x: -self.synapses[(v, x)].weight)
        seen = {src}
        queue: List[List[str]] = [[src]]
        while queue:
            cur = queue.pop(0)
            if len(cur) - 1 >= max_hops:
                continue
            for nxt in adj.get(cur[-1], []):
                if nxt in seen:
                    continue
                if nxt == dst:
                    return cur + [nxt]
                seen.add(nxt)
                queue.append(cur + [nxt])
        return None

    def rich_club(self, frac: float = RICH_CLUB_FRAC) -> List[str]:
        """Hub neurons: top fraction by total degree (like the fly's 30%)."""
        if not self.neurons:
            return []
        deg: Dict[str, int] = {n: 0 for n in self.neurons}
        for (a, b) in self.synapses:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        ranked = sorted(deg, key=lambda n: -deg[n])
        k = max(1, math.ceil(len(ranked) * frac))
        return ranked[:k]

    def projectome(self) -> Dict[str, Dict[str, int]]:
        """Region-to-region projection map (like the fly projectome)."""
        proj: Dict[str, Dict[str, int]] = {}
        for (a, b), s in self.synapses.items():
            ra = self.neurons.get(a).region if a in self.neurons else region_of(a)
            rb = self.neurons.get(b).region if b in self.neurons else region_of(b)
            proj.setdefault(ra, {}).setdefault(rb, 0)
            proj[ra][rb] += 1
        return proj

    def suggest_next(self, current: str, limit: int = 5) -> List[str]:
        """Advisory routing: strongest verified downstream first (never forced)."""
        outs = self.neighbors(current, "out", limit=limit * 2)
        outs.sort(key=lambda s: (not s.verified, -s.weight))
        return [s.post for s in outs[:limit]]

    # ---- sleep replay (consolidation, like Drosophila sleep)

    def sleep_replay(self) -> Dict[str, Any]:
        """Replay the day's edges: decay all, prune weak, archive pruned.

        Returns a summary dict. Pruned synapses go to archive/ (never deleted).
        """
        pruned: List[Dict[str, Any]] = []
        for key in list(self.synapses.keys()):
            s = self.synapses[key]
            s.weight = max(W_FLOOR, s.weight - DECAY_RATE)
            if s.weight <= PRUNE_BELOW and s.successes == 0:
                pruned.append(s.to_dict())
                del self.synapses[key]
        if pruned:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            _write_json(self.root / "archive" / f"pruned-{stamp}.json",
                        {"at": time.time(), "synapses": pruned})
        self.save()
        return {"decayed": len(self.synapses), "pruned": len(pruned),
                "neurons": len(self.neurons), "synapses": len(self.synapses)}

    # ---- stats

    def stats(self) -> Dict[str, Any]:
        verified = sum(1 for s in self.synapses.values() if s.verified)
        return {"neurons": len(self.neurons), "synapses": len(self.synapses),
                "verified_edges": verified,
                "rich_club": self.rich_club(),
                "regions": sorted({n.region for n in self.neurons.values() if n.region})}


# ---------------------------------------------------------------- event ingestion

def ingest_objective_events(home: RadHome, limit: int = 0) -> Dict[str, Any]:
    """Build connectome edges from real objective events on disk.

    Reads ~/.rad/objectives/*/events.jsonl, extracts TOOL_CALLED sequences
    per task, records them as verified or not based on task outcome.
    Returns a summary. Edges without evidence are never created.
    """
    import json as _json
    cx = Connectome(home)
    objs = home.root / "objectives"
    n_edges = n_tasks = 0
    if not objs.exists():
        return {"edges": 0, "tasks": 0, "note": "no objectives"}
    for d in sorted(objs.iterdir()):
        if limit and n_tasks >= limit:
            break
        ev = d / "events.jsonl"
        if not ev.exists():
            continue
        seq: List[str] = []
        ok: Optional[bool] = None
        try:
            lines = ev.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for ln in lines:
            try:
                e = _json.loads(ln)
            except Exception:
                continue
            kind = str(e.get("kind", ""))
            data = e.get("data", {}) if isinstance(e.get("data"), dict) else {}
            if kind == "TOOL_CALLED":
                tool = str(data.get("tool", ""))
                if tool:
                    seq.append(tool)
            elif kind in ("TASK_COMPLETED", "TASK_VERIFIED"):
                ok = True
            elif kind in ("TASK_FAILED",):
                ok = False
            elif kind == "TASK_END" and seq:
                cx.record_sequence(seq, verified=bool(ok), success=ok)
                n_edges += max(0, len(seq) - 1)
                n_tasks += 1
                seq, ok = [], None
        if seq:
            cx.record_sequence(seq, verified=bool(ok), success=ok)
            n_edges += max(0, len(seq) - 1)
            n_tasks += 1
    cx.save()
    return {"edges": n_edges, "tasks": n_tasks, "stats": cx.stats()}
