"""The promotion protocol — verified evolution (weight/model/prompt loop).

A "brain candidate" is anything that answers: a provider+model, the same
provider with different settings, or a STAGED WEIGHT ADAPTER (LoRA trained
anywhere — your Mac, a rented GPU, wherever).

Nothing goes live on belief. Promotion = candidate beats the current brain on
the Capability Battery by a margin. Every promotion is a generation, rollback
always. This is the law that makes self-improvement safe.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome
from rad.ui import col


class Brains:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "brains"
        self.dir.mkdir(exist_ok=True)
        self.path = self.dir / "registry.json"

    # ------------------------------------------------------------ storage
    def data(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {"current": None, "candidates": {}}

    def save(self, d: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(d, indent=2, ensure_ascii=False))

    def candidates(self) -> Dict[str, Any]:
        return self.data().get("candidates", {})

    def current(self) -> Optional[Dict[str, Any]]:
        d = self.data()
        name = d.get("current")
        return d.get("candidates", {}).get(name) if name else None

    # ------------------------------------------------------------ lifecycle
    def add(self, name: str, provider: str, model: str = "",
            adapter: Optional[str] = None, temperature: float = 0.7,
            note: str = "") -> Dict[str, Any]:
        d = self.data()
        cand = {
            "name": name, "provider": provider, "model": model,
            "adapter": str(Path(adapter).expanduser()) if adapter else None,
            "temperature": temperature, "note": note,
            "created": time.time(), "generation": 0, "parent": None,
            "best_score": None, "history": [],
        }
        d.setdefault("candidates", {})[name] = cand
        if not d.get("current"):
            d["current"] = name  # first brain becomes current
        self.save(d)
        return cand

    def generations(self) -> int:
        gens = 0
        for c in self.candidates().values():
            gens = max(gens, c.get("generation", 0))
        return gens

    def promote(self, name: str, bench, margin: float = 0.0,
                categories: Optional[List[str]] = None,
                canary_tasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Benchmark the candidate against current. Promote iff it wins by margin."""
        from rad.battery import build_caller, CapabilityBattery
        from rad.integrate.hooks import promotion_gate, make_battery_fn
        d = self.data()
        cand = d["candidates"].get(name)
        if not cand:
            raise ValueError(f"no brain candidate named '{name}'")
        cur = self.current()
        cur_cfg = {"provider": cur.get("provider", "default"), "model": cur.get("model", "")} if cur else None

        # Fail-closed promotion gates: canary integrity check & contamination firewall
        battery_obj = bench if isinstance(bench, CapabilityBattery) else CapabilityBattery(home=self.home)
        promotion_gate(
            corpus_dir=self.home.root / "corpus",
            battery_dir=self.home.root / "battery",
            battery_fn=make_battery_fn(battery_obj) if (cur and canary_tasks) else None,
            current_config=cur_cfg,
            tasks=canary_tasks,
            results_dir=self.home.root / "battery",
            check_canary=bool(cur and canary_tasks),
            check_contamination=True,
        )

        def run(c: Dict[str, Any]):
            caller = build_caller(self.home, provider=c["provider"], model=c.get("model") or None,
                                  temperature=c.get("temperature", 0.7))
            label = f"{c['name']}" + (f" [{Path(c['adapter']).name}]" if c.get("adapter") else "")
            return bench.run(caller, label=label, provider=c["provider"], model=c.get("model", "?"),
                             categories=categories)

        new_rep = run(cand)
        old_rep = run(cur) if cur else {"score": 0.0, "label": "(no current brain)"}

        cand["history"].append({"at": time.time(), "score": new_rep["score"], "note": "battle"})
        cand["best_score"] = max(cand.get("best_score") or 0, new_rep["score"])
        won = new_rep["score"] >= old_rep["score"] + margin
        result = {"candidate": name, "new": new_rep["score"], "old": old_rep["score"],
                  "margin": margin, "promoted": won}
        if won:
            cand["parent"] = cur["name"] if cur else None
            cand["generation"] = self.generations() + 1
            d["current"] = name
            # integrate with the chat session: pin the winning brain
            self.home.update(force_provider=cand["provider"],
                             model=cand.get("model") or None)
        self.save(d)
        return result

    def rollback(self) -> Optional[str]:
        d = self.data()
        cur = self.current()
        if not cur or not cur.get("parent"):
            return None
        d["current"] = cur["parent"]
        self.save(d)
        return d["current"]

    # ------------------------------------------------------------ report
    def show(self) -> str:
        d = self.data()
        cands = d.get("candidates", {})
        if not cands:
            return "  no brain candidates — `rad brain add <name> --provider <p> [--model m] [--adapter f]`"
        out = []
        for name, c in cands.items():
            mark = col.green("● current") if d.get("current") == name else col.dim("○")
            best = f"  best {c['best_score']}" if c.get("best_score") is not None else ""
            adapter = f"  {col.dim('adapter: ' + str(Path(c['adapter']).name))}" if c.get("adapter") else ""
            out.append(f"  {mark} {name:<20} {c['provider']}/{c.get('model') or '?'}  "
                       f"gen {c.get('generation', 0)}{best}{adapter}")
        return "\n".join(out)
