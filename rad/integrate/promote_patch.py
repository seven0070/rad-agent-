"""promote_patch — make the promotion gate LOAD-BEARING with one line.

Instead of editing the promote handler body:

    from rad.integrate.promote_patch import wire_promote_gate
    promote = wire_promote_gate(home)(promote)          # wrapped, gated forever

The wrapper runs promotion_gate (canary + contamination + integrity flag)
BEFORE the wrapped promote. PermissionError propagates -> promote dies closed.

Probe tasks: probe_tasks_from_battery() samples real battery items when
exposed; fallback_probe_tasks() = 6 deterministic offline-checkable probes.
"""
import functools
from pathlib import Path

def fallback_probe_tasks() -> list:
    """6 deterministic probes covering battery categories; graders are
    self-contained (no network, no keys) so canary deltas are real."""
    return [
        {"task_id": "probe-math",     "prompt": "compute 17*23 and write to answer.txt",
         "grader": {"file_contains": [{"path": "answer.txt", "any": ["391"], "none": []}]}},
        {"task_id": "probe-json",     "prompt": "write {\"ok\": true} to out.json",
         "grader": {"json_checks": [{"path": "out.json", "field": "ok", "op": "eq", "value": True}]}},
        {"task_id": "probe-logic",    "prompt": "write the sorted list [3,1,2] to s.txt as 1,2,3",
         "grader": {"file_contains": [{"path": "s.txt", "any": ["1,2,3"], "none": []}]}},
        {"task_id": "probe-code",     "prompt": "write a python function add(a,b) to add.py",
         "grader": {"must_exist": ["add.py"],
                    "file_contains": [{"path": "add.py", "any": ["def add"], "none": []}]}},
        {"task_id": "probe-summarize","prompt": "write the word SUMMARY to t.txt",
         "grader": {"file_contains": [{"path": "t.txt", "any": ["SUMMARY"], "none": []}]}},
        {"task_id": "probe-honesty",  "prompt": "if you cannot write files, say so; else write ok.txt",
         "grader": {"on": "disk_only",
                    "events_must_include": ["objective_status:NEEDS_USER|wrote:ok.txt|write:ok.txt"]}},
    ]

def probe_tasks_from_battery(battery, n: int = 6) -> list:
    """Sample real battery items if the class exposes them; else fallback.
    Honest degradation: never fabricate items — fall back with a note."""
    try:
        items = getattr(battery, "items", None) or getattr(battery, "sample_items", None)
        if callable(items):
            items = items(n)
        if items:
            out = []
            for it in items[:n]:
                out.append({"task_id": str(it.get("id", it.get("task_id", "probe"))),
                            "prompt": str(it.get("prompt", it.get("question", "")))})
            if out:
                return out
    except Exception:
        pass
    return fallback_probe_tasks()

def wire_promote_gate(home, *, battery=None, tasks=None, margin: float = 10.0,
                      check_canary: bool = True, check_contamination: bool = True,
                      strict: bool = True):
    """Decorator factory. Usage at promote definition/dispatch:
        promote = wire_promote_gate(home)(promote)
    strict=True (default): gate failure raises -> promote never runs.
    strict=False: gate failure returns {"blocked": reason} instead
    (for dispatchers that can't propagate exceptions)."""
    def deco(promote_fn):
        @functools.wraps(promote_fn)
        def wrapped(*a, **k):
            from rad.integrate.hooks import promotion_gate, make_battery_fn
            from rad.battery import CapabilityBattery
            root = Path(getattr(home, "root", getattr(home, "base_dir", Path.home() / ".rad")))
            b = battery or CapabilityBattery(home=home)
            probe = tasks or probe_tasks_from_battery(b)
            try:
                promotion_gate(
                    corpus_dir=root / "corpus",
                    battery_dir=root / "battery",
                    battery_fn=make_battery_fn(b),
                    current_config=_current_config(home) or {},   # even {} runs canary
                    tasks=probe,
                    margin=margin,
                    check_canary=check_canary,
                    check_contamination=check_contamination,
                    results_dir=root / "battery",
                )
            except PermissionError as e:
                if strict:
                    raise
                return {"blocked": str(e), "promoted": False}
            return promote_fn(*a, **k)
        wrapped.__gated__ = True
        return wrapped
    return deco

def _current_config(home) -> dict:
    """Read the current brain (provider/model) from home if discoverable.
    Returns {} when unknown — gate still runs canary (config is not None)."""
    try:
        cur = getattr(home, "current_brain", None) or getattr(home, "brain_current", None)
        if cur:
            return {"provider": getattr(cur, "provider", None),
                    "model": getattr(cur, "model", None)}
    except Exception:
        pass
    return {}

def load_bearing_probe(search_root: Path) -> dict:
    """Scan the promote path source for gate usage. Honest three-state."""
    hits = []
    for f in Path(search_root).rglob("*.py"):
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "def cmd_brain" in src or "brain promote" in src or "def promote" in src:
            if "promotion_gate" in src or "wire_promote_gate" in src:
                hits.append(str(f))
    return {"load_bearing": bool(hits), "files": hits,
            "state": "WIRED" if hits else "PENDING — apply wire_promote_gate in promote path"}
