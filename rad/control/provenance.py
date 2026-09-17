"""Provenance — answer "why do you believe this?" and "where did this file come from?"
from recorded state only (events, observations, artifacts). Nothing is inferred by a model.

    Artifact ──created_by──► action (tool call) ──in──► task ──in──► objective
                                  │
                                  └── evidence: web fetches / searches / files read
                                      *before* the action, in the same task
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.control import events as E
from rad.control.events import EventLog
from rad.control.observer import Observer

_TOKEN = re.compile(r"[a-z0-9]{4,}")


class Provenance:
    def __init__(self, objective_dir: Path) -> None:
        self.dir = objective_dir
        self.log = EventLog(objective_dir / "events.jsonl")
        self.observer = Observer(objective_dir)

    # ------------------------------------------------------------ artifact lineage
    def artifact(self, ref: str) -> Optional[Dict[str, Any]]:
        """Full chain for an artifact by id, path, or filename."""
        reg = self.observer.artifacts()
        art = reg.get(ref)
        if not art:
            hits = [a for a in reg.values() if a["location"] == ref or Path(a["location"]).name == ref]
            hits.sort(key=lambda a: -a["version"])
            art = hits[0] if hits else None
        if not art:
            return None
        obs = self._observation_for_artifact(art["id"])
        chain: List[Dict[str, Any]] = []
        cur = art
        while cur:
            chain.append(cur)
            cur = reg.get(cur["parent"]) if cur.get("parent") else None
        task_evs = list(self.log.read(task_id=art["task_id"]))
        started = [e for e in task_evs if e.kind == E.TASK_STARTED]
        return {
            "artifact": art,
            "versions": chain,
            "action": obs.to_dict() if obs else None,
            "task": {"id": art["task_id"], "text": started[-1].data.get("text", "") if started else "",
                     "attempt": started[-1].data.get("attempt") if started else None},
            "evidence": self.evidence_for_task(art["task_id"], before=obs.at if obs else None),
            "verification": art.get("verification") or {},
        }

    def _observation_for_artifact(self, art_id: str):
        for p in sorted(self.observer.dir.glob("obs_*.json")):
            o = self.observer.load(p.stem)
            if o and art_id in o.artifacts:
                return o
        return None

    # ------------------------------------------------------------ evidence
    def evidence_for_task(self, task_id: str, before: Optional[float] = None) -> List[Dict[str, Any]]:
        out = []
        for o in self.observer.for_task(task_id):
            if before is not None and o.at > before:
                continue
            for ev in o.evidence:
                out.append({**ev, "observation": o.id, "excerpt": o.output[:300]})
            if o.tool == "read_file" and o.status == "success":
                out.append({"source": f"file:{o.args.get('path', '')}", "tool": "read_file", "at": o.at,
                            "trusted": True, "observation": o.id, "excerpt": o.output[:300]})
        return out

    def why(self, claim: str, k: int = 5) -> Dict[str, Any]:
        """Search recorded observations for support of a claim (token overlap, deterministic)."""
        q = set(_TOKEN.findall(claim.lower()))
        scored = []
        for p in sorted(self.observer.dir.glob("obs_*.json")):
            o = self.observer.load(p.stem)
            if not o or o.status != "success":
                continue
            toks = set(_TOKEN.findall(o.output.lower()))
            if not q or not toks:
                continue
            overlap = len(q & toks) / len(q)
            if overlap > 0:
                scored.append((overlap, o))
        scored.sort(key=lambda x: -x[0])
        support = []
        for score, o in scored[:k]:
            src = o.args.get("url") or o.args.get("query") or o.args.get("path") or o.args.get("command", "")
            support.append({"score": round(score, 2), "tool": o.tool, "source": str(src)[:200],
                            "trusted": o.tool not in ("fetch_page", "web_search"),
                            "observation": o.id, "task": o.task_id, "at": o.at,
                            "excerpt": self._excerpt(o.output, q)})
        return {"claim": claim, "support": support,
                "verdict": ("supported" if support and support[0]["score"] >= 0.5 else
                            "weak" if support else "unsupported")}

    @staticmethod
    def _excerpt(text: str, q: set, width: int = 240) -> str:
        low = text.lower()
        best = 0
        for t in q:
            i = low.find(t)
            if i >= 0:
                best = i
                break
        s = max(0, best - width // 3)
        return text[s:s + width].replace("\n", " ")
