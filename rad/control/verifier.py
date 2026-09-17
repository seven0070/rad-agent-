"""Verifier — never trust an LLM's declaration of completion by itself.

Levels, cheapest first:
  1. tool verification     — did the actions in this task succeed? (from observations)
  2. check verification    — the task's machine-checkable Checks (files, shell, regex)
  3. artifact verification — produced files still exist and are non-empty
  4. goal verification     — objective-level Checks and a *recorded* LLM judgement
                             that is explicitly labelled as not machine-verified

The result is a structured dict, persisted on the task/objective, never a bare bool.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.control.observer import Observation, Observer
from rad.control.tasks import Check, Task

VERIFIED = "VERIFIED"
FAILED = "FAILED"
UNVERIFIED = "UNVERIFIED"       # no machine checks available — do not treat as success


class Verifier:
    def __init__(self, workspace: Path, observer: Observer,
                 llm: Optional[Callable[[str], str]] = None, shell_timeout: int = 60) -> None:
        self.ws = workspace
        self.observer = observer
        self.llm = llm
        self.shell_timeout = shell_timeout

    # ------------------------------------------------------------ public
    def verify_task(self, task: Task, reply: str) -> Dict[str, Any]:
        obs = self.observer.for_task(task.id)
        results: List[Dict[str, Any]] = []

        # level 1 — tool outcomes of this attempt
        attempt_obs = [o for o in obs if o.at >= (task.started or 0)]
        errors = [o for o in attempt_obs if o.status == "error"]
        blocked = [o for o in attempt_obs if o.status in ("blocked", "declined")]
        results.append({"level": "tool", "kind": "actions",
                        "ok": not errors,
                        "detail": f"{len(attempt_obs)} actions, {len(errors)} errors, {len(blocked)} blocked/declined"})

        # level 2 — explicit checks
        for c in task.checks:
            results.append(self.run_check(c, reply=reply))

        # level 3 — artifacts of this task
        for o in attempt_obs:
            for aid in o.artifacts:
                a = self.observer.artifacts().get(aid)
                if a and a["type"] == "file":
                    p = Path(a["location"])
                    ok = p.exists() and p.stat().st_size > 0
                    r = {"level": "artifact", "kind": "file_nonempty", "ok": ok, "detail": a["location"]}
                    results.append(r)
                    self.observer.mark_verified(aid, r)

        machine = [r for r in results if r.get("machine", True)]
        hard_fail = any(not r["ok"] for r in machine)
        has_checks = bool(task.checks)
        if hard_fail:
            status = FAILED
        elif has_checks:
            status = VERIFIED
        elif attempt_obs and not errors:
            # actions ran cleanly but nothing asserted the outcome
            status = UNVERIFIED
        else:
            status = UNVERIFIED
        return {"status": status, "results": results,
                "summary": "; ".join(f"{'✓' if r['ok'] else '✗'} {r['kind']}:{r['detail'][:80]}" for r in results)}

    def verify_objective(self, goal: str, criteria: List[str], checks: List[Check],
                         final_text: str, artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        results = [self.run_check(c, reply=final_text) for c in checks]
        for a in artifacts.values():
            if a["type"] == "file":
                p = Path(a["location"])
                results.append({"level": "artifact", "kind": "file_nonempty",
                                "ok": p.exists() and p.stat().st_size > 0, "detail": a["location"]})
        machine_fail = any(not r["ok"] for r in results if r.get("machine", True))
        judge = None
        if self.llm and criteria:
            judge = self._llm_judge(goal, criteria, final_text, artifacts)
            results.append({"level": "goal", "kind": "llm_judge", "machine": False,
                            "ok": judge.get("pass", False), "detail": judge.get("reason", "")[:200]})
        if machine_fail:
            status = FAILED
        elif checks or (results and all(r.get("machine", True) for r in results)):
            status = VERIFIED if results else UNVERIFIED
        elif judge is not None:
            status = UNVERIFIED if judge.get("pass") else FAILED   # LLM-only opinion is never VERIFIED
        else:
            status = UNVERIFIED
        return {"status": status, "results": results}

    # ------------------------------------------------------------ checks
    def run_check(self, c: Check, reply: str = "") -> Dict[str, Any]:
        a = c.args
        base = {"level": "check", "kind": c.kind, "detail": c.description or json.dumps(a)[:120]}
        try:
            if c.kind == "file_exists":
                p = self._p(a["path"])
                return {**base, "ok": p.exists(), "detail": f"{p} exists={p.exists()}"}
            if c.kind == "file_min_bytes":
                p = self._p(a["path"])
                n = p.stat().st_size if p.exists() else -1
                return {**base, "ok": n >= int(a.get("n", 1)), "detail": f"{p} size={n} min={a.get('n', 1)}"}
            if c.kind == "file_contains":
                p = self._p(a["path"])
                txt = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
                ok = str(a["text"]) in txt
                return {**base, "ok": ok, "detail": f"{p} contains {a['text']!r}={ok}"}
            if c.kind == "json_valid":
                p = self._p(a["path"])
                try:
                    json.loads(p.read_text(encoding="utf-8"))
                    return {**base, "ok": True, "detail": f"{p} is valid JSON"}
                except Exception as e:
                    return {**base, "ok": False, "detail": f"{p} invalid JSON: {e}"}
            if c.kind == "shell_ok":
                code, out = self._sh(a["command"])
                return {**base, "ok": code == 0, "detail": f"exit={code} {out[-120:]}"}
            if c.kind == "shell_output":
                code, out = self._sh(a["command"])
                ok = str(a.get("contains", "")) in out
                return {**base, "ok": ok, "detail": f"exit={code} contains={ok}"}
            if c.kind == "reply_matches":
                ok = re.search(a["pattern"], reply or "", re.I | re.S) is not None
                return {**base, "ok": ok, "detail": f"reply matches /{a['pattern']}/={ok}"}
            if c.kind == "llm_judge":
                if not self.llm:
                    return {**base, "ok": False, "machine": False, "detail": "no model available to judge"}
                raw = self.llm(f"Answer strictly YES or NO, then one sentence.\nQuestion: {a['question']}\n\n"
                               f"Material:\n{(reply or '')[:6000]}")
                ok = bool(re.match(r"\s*yes\b", raw or "", re.I))
                return {**base, "ok": ok, "machine": False, "detail": (raw or "")[:160]}
            return {**base, "ok": False, "detail": f"unknown check kind {c.kind}"}
        except Exception as e:
            return {**base, "ok": False, "detail": f"check error: {e}"}

    # ------------------------------------------------------------ helpers
    def _p(self, path: str) -> Path:
        p = Path(path).expanduser()
        return p if p.is_absolute() else self.ws / p

    def _sh(self, cmd: str):
        shell = ["cmd", "/c"] if os.name == "nt" else ["sh", "-c"]
        try:
            pr = subprocess.run(shell + [cmd], cwd=str(self.ws), capture_output=True, text=True,
                                timeout=self.shell_timeout)
            return pr.returncode, (pr.stdout or "") + (pr.stderr or "")
        except subprocess.TimeoutExpired:
            return 124, "[timeout]"

    def _llm_judge(self, goal: str, criteria: List[str], final: str,
                   artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        arts = "\n".join(f"- {a['type']} {a['location']} ({a.get('size', 0)} bytes)" for a in artifacts.values())
        prompt = (
            "You are a strict verifier. Do not be charitable.\n"
            f"GOAL: {goal}\nSUCCESS CRITERIA:\n" + "\n".join(f"- {c}" for c in criteria) +
            f"\n\nARTIFACTS PRODUCED:\n{arts or '(none)'}\n\nFINAL REPORT FROM AGENT:\n{final[:6000]}\n\n"
            'Reply ONLY with JSON: {"pass": true|false, "reason": "<one sentence>", "unmet": ["..."]}'
        )
        try:
            raw = self.llm(prompt) or ""
            m = re.search(r"\{.*\}", raw, re.S)
            d = json.loads(m.group(0)) if m else {}
            return {"pass": bool(d.get("pass")), "reason": str(d.get("reason", ""))[:300],
                    "unmet": d.get("unmet", [])}
        except Exception as e:
            return {"pass": False, "reason": f"judge error: {e}", "unmet": []}
