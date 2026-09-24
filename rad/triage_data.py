"""Triage corpus — labeled (text, label, weight) rows mined from ~/.rad history.

Phase 1c of the Laya integration plan: supervised labels for the advisory
auto-vs-escalate classifier (`rad.triage`). Labels are derived only from what
actually happened in recorded objectives — never invented.

Label rules (agreed plan):
  escalate  SECURITY_DENIED, NEEDS_USER (event or status), BUDGET_EXCEEDED,
            recovery strategy ask_user/abort, task failure_class
            PERMISSION_FAILURE, task status NEEDS_USER.
  auto      objective/task reached VERIFIED (or objective completed +
            verified) with no human-intervention signal on that row.
  retry/repair/replan alone stays auto — the engine handled it autonomously.
  anything ambiguous (in-flight, cancelled, unverified) is skipped.

Output is plain JSONL — same trainer-agnostic contract as `rad.corpus`.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from rad.home import RadHome

LABELS = ("auto", "escalate")
MIN_TEXT = 10
MAX_TEXT = 8000
_ESCALATE_STRATEGIES = frozenset({"ask_user", "abort"})
_ESCALATE_TASK_STATUS = frozenset({"NEEDS_USER"})


def _row(
    text: str,
    label: str,
    kind: str,
    evidence: List[str],
    *,
    weight: float = 1.0,
    objective_id: str = "",
    task_id: str = "",
    source: str = "events",
) -> Optional[Dict[str, Any]]:
    body = (text or "").strip()[:MAX_TEXT]
    if len(body) < MIN_TEXT or label not in LABELS:
        return None
    return {
        "text": body,
        "label": label,
        "weight": float(weight),
        "kind": kind,
        "source": source,
        "objective_id": objective_id,
        "task_id": task_id,
        "evidence": evidence[:12],
    }


def _load_events(store, oid: str) -> List[Dict[str, Any]]:
    path = store.events_path(oid)
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return out


def _task_signals(events: Iterable[Dict[str, Any]], task_id: str) -> List[str]:
    """Human-intervention signals scoped to one task_id."""
    hits: List[str] = []
    for e in events:
        if e.get("task_id") != task_id:
            continue
        kind = e.get("kind") or ""
        data = e.get("data") or {}
        if kind == "SECURITY_DENIED":
            hits.append(f"SECURITY_DENIED:{data.get('tool') or '?'}")
        elif kind == "NEEDS_USER":
            hits.append("NEEDS_USER")
        elif kind == "RECOVERY_DECISION":
            strat = str(data.get("strategy") or "")
            if strat in _ESCALATE_STRATEGIES:
                hits.append(f"strategy:{strat}")
        elif kind == "TASK_STATUS" and str(data.get("status") or "") in _ESCALATE_TASK_STATUS:
            hits.append(f"task_status:{data.get('status')}")
    return hits


def _objective_signals(events: List[Dict[str, Any]]) -> List[str]:
    """Human-intervention signals for the whole objective (incl. empty task_id)."""
    hits: List[str] = []
    for e in events:
        kind = e.get("kind") or ""
        data = e.get("data") or {}
        if kind == "SECURITY_DENIED":
            hits.append(f"SECURITY_DENIED:{data.get('tool') or '?'}")
        elif kind == "NEEDS_USER":
            hits.append("NEEDS_USER")
        elif kind == "BUDGET_EXCEEDED":
            hits.append(f"BUDGET_EXCEEDED:{data.get('reason') or '?'}")
        elif kind == "OBJECTIVE_STATUS" and str(data.get("status") or "") == "needs_user":
            hits.append("objective_status:needs_user")
        elif kind == "RECOVERY_DECISION":
            strat = str(data.get("strategy") or "")
            if strat in _ESCALATE_STRATEGIES:
                hits.append(f"strategy:{strat}")
        elif kind == "TASK_STATUS" and str(data.get("status") or "") in _ESCALATE_TASK_STATUS:
            hits.append(f"task_status:{data.get('status')}")
    return hits


def _objective_verified(events: List[Dict[str, Any]], obj: Any) -> bool:
    ver = getattr(obj, "verification", None)
    if not isinstance(ver, dict):
        ver = {}
    if str(ver.get("status") or "") == "VERIFIED":
        return True
    for e in reversed(events):
        if e.get("kind") != "VERIFICATION_RESULT":
            continue
        data = e.get("data") or {}
        if data.get("scope") == "objective" or not e.get("task_id"):
            if str(data.get("status") or "") == "VERIFIED":
                return True
            return False
    # terminal completed with no explicit objective verification row still
    # requires a VERIFIED task set — refuse to invent an auto label.
    return False


def _task_verified(task: Dict[str, Any], events: List[Dict[str, Any]], task_id: str) -> bool:
    ver = task.get("verification") or {}
    if isinstance(ver, dict) and str(ver.get("status") or "") == "VERIFIED":
        return True
    for e in reversed(events):
        if e.get("kind") != "VERIFICATION_RESULT" or e.get("task_id") != task_id:
            continue
        data = e.get("data") or {}
        return str(data.get("status") or "") == "VERIFIED"
    return False


def _dedupe(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[Tuple[str, str]] = set()
    out: List[Dict[str, Any]] = []
    for r in rows:
        key = (hashlib.sha1(f"{r['label']}\n{r['text']}".encode("utf-8")).hexdigest(),
               r["label"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def mine(home: RadHome) -> List[Dict[str, Any]]:
    """Scan objectives history → labeled triage rows. No LLM required."""
    from rad.control.objectives import ObjectiveStatus, ObjectiveStore

    store = ObjectiveStore(home)
    rows: List[Dict[str, Any]] = []
    try:
        dirs = sorted(p for p in store.root.iterdir() if p.is_dir())
    except OSError:
        return []
    for d in dirs:
        oid = d.name
        obj = store.load(oid)
        if obj is None:
            continue
        events = _load_events(store, oid)
        tasks = store.load_tasks(oid) or []
        goal = obj.goal or ""
        esc_obj = _objective_signals(events)
        for t in tasks:
            if str(t.get("failure_class") or "") == "PERMISSION_FAILURE":
                esc_obj.append("task_failure_class:PERMISSION_FAILURE")
            elif str(t.get("status") or "") in _ESCALATE_TASK_STATUS:
                esc_obj.append(f"task_status:{t.get('status')}")
        # de-dupe evidence while preserving order
        esc_obj = list(dict.fromkeys(esc_obj))

        if esc_obj:
            r = _row(goal, "escalate", "objective", esc_obj, objective_id=oid)
            if r:
                rows.append(r)
        elif obj.status == ObjectiveStatus.COMPLETED and _objective_verified(events, obj):
            r = _row(goal, "auto", "objective", ["objective:VERIFIED"], objective_id=oid)
            if r:
                rows.append(r)
        elif str(obj.status or "") == ObjectiveStatus.NEEDS_USER:
            r = _row(goal, "escalate", "objective", ["objective_status:needs_user"],
                     objective_id=oid)
            if r:
                rows.append(r)

        for t in tasks:
            tid = str(t.get("id") or "")
            text = str(t.get("text") or "")
            if not tid:
                continue
            esc = _task_signals(events, tid)
            fc = str(t.get("failure_class") or "")
            if fc == "PERMISSION_FAILURE":
                esc.append("task_failure_class:PERMISSION_FAILURE")
            st = str(t.get("status") or "")
            if st in _ESCALATE_TASK_STATUS:
                esc.append(f"task_status:{st}")
            esc = list(dict.fromkeys(esc))
            if esc:
                r = _row(text, "escalate", "task", esc, objective_id=oid, task_id=tid)
                if r:
                    rows.append(r)
            elif _task_verified(t, events, tid):
                r = _row(text, "auto", "task", ["task:VERIFIED"],
                         objective_id=oid, task_id=tid)
                if r:
                    rows.append(r)
    return _dedupe(rows)


def stats(rows: Optional[List[Dict[str, Any]]] = None, home: Optional[RadHome] = None) -> Dict[str, int]:
    if rows is None:
        if home is None:
            raise ValueError("stats() needs rows or home")
        rows = mine(home)
    out = {"total": len(rows), "auto": 0, "escalate": 0, "objective": 0, "task": 0}
    for r in rows:
        out[r["label"]] = out.get(r["label"], 0) + 1
        out[r["kind"]] = out.get(r["kind"], 0) + 1
    return out


def export(home: RadHome, path: Optional[str] = None) -> str:
    rows = mine(home)
    dest = Path(path) if path else home.root / "corpus" / "triage-train.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return str(dest)


def show(home: RadHome) -> str:
    from rad.ui import col
    s = stats(home=home)
    return "\n".join([
        f"  total rows:   {s['total']}",
        f"  {col.green('auto')}          {s.get('auto', 0)}",
        f"  {col.yellow('escalate')}     {s.get('escalate', 0)}",
        f"  objective     {s.get('objective', 0)}",
        f"  task          {s.get('task', 0)}",
        col.dim("  export: rad triage-corpus export [--out file.jsonl]"),
    ])
