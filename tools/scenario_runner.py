"""Offline scenario runner — executes pack scenarios against any agent callable.

Agent contract: agent_fn(task, workspace) -> {"events": [...], "message": str}
Grading: disk state + reported events ONLY. Model claims are not evidence.
Path mapping: "~/.rad/..." in setup/grader -> "<workspace>/.rad/..." sandbox.
Scenarios containing setup.inject -> honest SKIP (host_required).
"""
import hashlib, json, os, shutil, tempfile
from datetime import datetime, timezone
from pathlib import Path

def _resolve(p: str, ws: Path) -> Path:
    if p.startswith("~/.rad/"):
        return ws / ".rad" / p[len("~/.rad/"):]
    if p.startswith("~"):
        return Path(os.path.expanduser(p))
    return ws / p

def run_scenario(scenario: dict, agent_fn, keep_ws: bool = False) -> dict:
    sid = scenario.get("id", "?")
    rec = {"id": sid, "category": scenario.get("category", ""),
           "ran_at": datetime.now(timezone.utc).isoformat()}
    if "inject" in scenario.get("setup", {}):
        rec.update(status="SKIP",
                   reason="host_required: mid-run injection needs real harness")
        return rec
    ws = Path(tempfile.mkdtemp(prefix=f"rad-scen-{sid}-"))
    try:
        for rel, content in scenario.get("setup", {}).get("files", {}).items():
            f = _resolve(rel, ws)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        result = agent_fn(scenario["task"], ws)
        events = list(result.get("events", []))
        rec["message_sha16"] = hashlib.sha256(
            str(result.get("message", "")).encode()).hexdigest()[:16]
        checks = _grade(scenario.get("grader", {}), ws, events)
        rec["checks"] = checks
        failed = [c for c in checks if not c["passed"]]
        rec.update(status="PASS" if not failed else "FAIL",
                   failed_checks=[c["name"] for c in failed])
        rec["anti_goals_advisory"] = scenario.get("anti_goals", [])
        return rec
    finally:
        if keep_ws:
            rec["workspace"] = str(ws)
        else:
            shutil.rmtree(ws, ignore_errors=True)

def run_pack(scenario_dicts: list, agent_fn) -> dict:
    recs = [run_scenario(s, agent_fn) for s in scenario_dicts]
    passed = sum(1 for r in recs if r["status"] == "PASS")
    skipped = sum(1 for r in recs if r["status"] == "SKIP")
    return {"total": len(recs), "passed": passed,
            "failed": len(recs) - passed - skipped, "skipped": skipped,
            "results": recs}

def _grade(g: dict, ws: Path, events: list) -> list:
    out = []
    def add(name, passed, detail=""):
        out.append({"name": name, "passed": bool(passed), "detail": detail})
    for p in g.get("must_exist", []):
        add(f"exists:{p}", _resolve(p, ws).exists())
    for p in g.get("must_not_exist", []):
        add(f"absent:{p}", not _resolve(p, ws).exists())
    for spec in g.get("file_contains", []):
        f = _resolve(spec["path"], ws)
        text = f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        for needle in spec.get("any", []):
            add(f"contains:{spec['path']}::{str(needle)[:30]}", needle in text)
        for needle in spec.get("none", []):
            add(f"not_contains:{spec['path']}::{str(needle)[:30]}", needle not in text)
    for jc in g.get("json_checks", []):
        f = _resolve(jc["path"], ws)
        try:
            obj = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
            val = _dig(obj, jc["field"])
            op, want = jc["op"], jc.get("value")
            ok = {"eq": lambda: val == want,
                  "ge": lambda: val is not None and val >= want,
                  "le": lambda: val is not None and val <= want,
                  "exists": lambda: val is not None,
                  "not_contains": lambda: val is not None and want not in str(val),
                  }.get(op, lambda: False)()
            add(f"json:{jc['path']}.{jc['field']} {op}", ok, f"got={val!r}")
        except Exception as e:
            add(f"json:{jc['path']}.{jc['field']}", False, f"error:{e}")
    for ev in g.get("events_must_include", []):
        alts = [a.strip() for a in str(ev).split("|")]
        add(f"event:{str(ev)[:40]}", any(a in events for a in alts))
    for ev in g.get("events_must_not_include", []):
        add(f"no_event:{str(ev)[:40]}", ev not in events)
    return out

def _dig(obj, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur
