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

from rad.control.codingloop import is_done_pollution_content, is_done_pollution_path
from rad.control.observer import Observation, Observer
from rad.control.tasks import Check, Task

VERIFIED = "VERIFIED"
FAILED = "FAILED"
UNVERIFIED = "UNVERIFIED"       # no machine checks available — do not treat as success


class Verifier:
    def __init__(self, workspace: Path, observer: Observer,
                 llm: Optional[Callable[[str], str]] = None, shell_timeout: int = 60, home=None,
                 provenance_dir: Optional[Path] = None) -> None:
        self.home = home
        self.ws = workspace
        self.observer = observer
        self.llm = llm
        self.shell_timeout = shell_timeout
        self.provenance_dir = Path(provenance_dir) if provenance_dir else None

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
                    if ok and (is_done_pollution_path(a["location"]) or
                               is_done_pollution_content(_read_text(p))):
                        ok = False
                    r = {"level": "artifact", "kind": "file_nonempty", "ok": ok, "detail": a["location"]}
                    results.append(r)
                    self.observer.mark_verified(aid, r)

        # level 4 — evidence: is what the model *said* backed by something we recorded?
        results.append(self._evidence_level(task, attempt_obs, reply))

        # level 5 — safety: were any actions denied or blocked by policy/sandbox?
        denied = [o for o in attempt_obs if o.status in ("blocked", "declined")]
        results.append({"level": "safety", "kind": "policy", "machine": False,
                        "ok": True,
                        "detail": (f"{len(denied)} action(s) denied by policy/sandbox"
                                   if denied else "no policy/sandbox denials")})

        machine = [r for r in results if r.get("machine", True)]
        hard_fail = any(not r["ok"] for r in machine)
        soft_fail = any(not r["ok"] for r in results if not r.get("machine", True))
        machine_checks = [r for r in machine if r["level"] == "check"]
        produced = [r for r in results if r["level"] == "artifact"]
        if hard_fail or soft_fail:
            status = FAILED
        elif machine_checks:
            status = VERIFIED            # at least one machine check passed, none failed
        elif produced and not errors:
            # no explicit checks, but the task demonstrably produced non-empty artifacts
            # (real files with hashes) and nothing errored — that is machine evidence
            status = VERIFIED
        else:
            status = UNVERIFIED
        return {"status": status, "results": results,
                "levels": sorted({r["level"] for r in results}),
                "denied": len(denied),
                "summary": "; ".join(f"{'✓' if r['ok'] else '✗'} {r['kind']}:{r['detail'][:80]}" for r in results)}

    def _evidence_level(self, task: Task, observations: List["Observation"], reply: str) -> Dict[str, Any]:
        """Record whether the reply's factual claims have recorded support.

        Advisory (machine=False by design): evidence *quality* is a judgement about
        untrusted external content, so it is reported to the human and to the
        objective-level verifier, never used to silently flip a task to FAILED.
        """
        claims = [ln.strip() for ln in (reply or "").splitlines()
                  if ln.strip() and not ln.strip().lower().startswith(("done:", "blocked:", "needs_user:"))]
        numbers = [c for c in claims if re.search(r"\d", c)][:6]
        trusted = [o for o in observations if o.status == "success"
                   and o.tool in ("read_file", "run_shell", "run_python", "list_dir", "verify_url")]
        untrusted = [o for o in observations if o.status == "success"
                     and o.tool in ("fetch_page", "web_search", "browse")]
        if not numbers:
            ok, detail = True, "no numeric/factual claims to source"
        elif trusted:
            ok, detail = True, f"{len(numbers)} claim(s), {len(trusted)} backed by local tools"
        elif untrusted:
            ok, detail = False, f"{len(numbers)} claim(s) rest only on untrusted web content"
        else:
            ok, detail = False, f"{len(numbers)} claim(s) with no recorded evidence"
        return {"level": "evidence", "kind": "claims_sourced", "ok": ok, "machine": False,
                "detail": detail, "claims": len(numbers), "trusted": len(trusted),
                "untrusted": len(untrusted)}

    def verify_objective(self, goal: str, criteria: List[str], checks: List[Check],
                         final_text: str, artifacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        results = [self.run_check(c, reply=final_text) for c in checks]
        latest: Dict[str, Dict[str, Any]] = {}
        for a in artifacts.values():
            if a["type"] == "file":
                cur = latest.get(a["location"])
                if cur is None or a.get("version", 1) > cur.get("version", 1):
                    latest[a["location"]] = a
        for a in latest.values():
            p = Path(a["location"])
            nonempty = p.exists() and p.stat().st_size > 0
            if nonempty and (is_done_pollution_path(a["location"]) or
                             is_done_pollution_content(_read_text(p))):
                nonempty = False
            results.append({"level": "artifact", "kind": "file_nonempty",
                            "ok": nonempty, "detail": a["location"]})
            # integrity: does the file still hash to what we recorded when we made it?
            if nonempty and a.get("sha256"):
                import hashlib as _h
                try:
                    now = _h.sha256(p.read_bytes()).hexdigest()
                    same = now == a["sha256"]
                except OSError:
                    same = False
                results.append({"level": "artifact", "kind": "hash_unchanged", "ok": same,
                                "detail": f"{Path(a['location']).name} "
                                          f"{'matches' if same else 'CHANGED since it was produced'}"})
        # safety summary: what did policy/sandbox refuse during this objective?
        denials: List[Dict[str, Any]] = []
        try:
            for p in sorted(self.observer.dir.glob("obs_*.json")):
                o = self.observer.load(p.stem)
                if o and o.status in ("blocked", "declined"):
                    denials.append({"tool": o.tool, "output": o.output[:200], "task": o.task_id})
        except Exception:
            pass
        results.append({"level": "safety", "kind": "policy", "ok": True, "machine": False,
                        "detail": f"{len(denials)} action(s) denied by policy/sandbox" if denials
                                  else "no denied actions"})
        # evidence: what support exists for the objective's claims?
        evidence = self._objective_evidence(goal, criteria)
        if evidence is not None:
            results.append({"level": "evidence", "kind": "claims_sourced", "machine": False,
                            "ok": evidence.get("verdict") == "supported",
                            "detail": f"{evidence.get('verdict')}: {len(evidence.get('support', []))} source(s)", 
                            "claim": evidence.get("claim", "")})
        machine = [r for r in results if r.get("machine", True)]
        machine_fail = any(not r["ok"] for r in machine)
        judge = None
        if self.llm and criteria:
            judge = self._llm_judge(goal, criteria, final_text, artifacts)
            results.append({"level": "goal", "kind": "llm_judge", "machine": False,
                            "ok": judge.get("pass", False), "detail": judge.get("reason", "")[:200]})
        if machine_fail:
            status = FAILED
        elif checks or machine:
            status = VERIFIED
        elif judge is not None:
            status = UNVERIFIED if judge.get("pass") else FAILED   # LLM-only opinion is never VERIFIED
        else:
            status = UNVERIFIED
        return {"status": status, "results": results, "denials": denials,
                "evidence": evidence, "artifacts": len(latest),
                "levels": sorted({r["level"] for r in results})}

    def _objective_evidence(self, goal: str, criteria: List[str]) -> Optional[Dict[str, Any]]:
        """Use recorded provenance to show *why* RAD believes the objective's claims."""
        if not self.provenance_dir:
            return None
        try:
            from rad.control.provenance import Provenance
            pv = Provenance(self.provenance_dir)
            claim = (criteria[0] if criteria else goal) or goal
            return pv.why(claim)
        except Exception:
            return None

    # ------------------------------------------------------------ checks
    def run_check(self, c: Check, reply: str = "") -> Dict[str, Any]:
        a = c.args
        base = {"level": "check", "kind": c.kind, "detail": c.description or json.dumps(a)[:120]}
        try:
            path = str(a.get("path", "")) if isinstance(a, dict) else ""
            if path and is_done_pollution_path(path):
                return {**base, "ok": False,
                        "detail": f"refused DONE: pollution path {path!r}"}
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
                if is_done_pollution_content(txt):
                    return {**base, "ok": False, "detail": f"{p} is a DONE: pollution file, not the artifact"}
                ok = str(a["text"]) in txt
                return {**base, "ok": ok, "detail": f"{p} contains {a['text']!r}={ok}"}
            if c.kind == "json_valid":
                p = self._p(a["path"])
                try:
                    raw = p.read_text(encoding="utf-8")
                    if is_done_pollution_content(raw):
                        return {**base, "ok": False, "detail": f"{p} is a DONE: pollution file, not JSON"}
                    json.loads(raw)
                    return {**base, "ok": True, "detail": f"{p} is valid JSON"}
                except Exception as e:
                    return {**base, "ok": False, "detail": f"{p} invalid JSON: {e}"}
            if c.kind in ("json_field", "json_min_len"):
                p = self._p(a["path"])
                doc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
                if doc is None:
                    return {**base, "ok": False, "detail": f"{p} missing or unreadable"}
                if c.kind == "json_min_len":
                    n = len(doc) if hasattr(doc, "__len__") else 0
                    want = int(a.get("n", 1))
                    return {**base, "ok": n >= want, "detail": f"{p} has {n} item(s), min {want}"}
                node = doc
                for part in str(a["key"]).split("."):
                    if isinstance(node, dict) and part in node:
                        node = node[part]
                    elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
                        node = node[int(part)]
                    else:
                        return {**base, "ok": False, "detail": f"{p}: key '{a['key']}' not found"}
                if "equals" in a:
                    ok = node == a["equals"]
                    return {**base, "ok": ok, "detail": f"{p}: {a['key']} == {a['equals']!r}: {ok}"}
                ok = bool(node) if a.get("truthy", True) else True
                return {**base, "ok": ok, "detail": f"{p}: {a['key']} = {str(node)[:80]}"}
            if c.kind == "shell_ok":
                code, out = self._sh(a["command"])
                return {**base, "ok": code == 0, "detail": f"exit={code} {out[-120:]}"}
            if c.kind == "shell_output":
                code, out = self._sh(a["command"])
                ok = str(a.get("contains", "")) in out
                return {**base, "ok": ok, "detail": f"exit={code} contains={ok}"}
            if c.kind == "file_equals":
                p = self._p(a["path"])
                got = p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else None
                ok = got == str(a.get("text", "")).strip()
                return {**base, "ok": ok, "detail": f"{p} == {str(a.get('text'))[:40]!r}: {ok}"}
            if c.kind == "file_absent":
                p = self._p(a["path"])
                return {**base, "ok": not p.exists(), "detail": f"{p} absent={not p.exists()}"}
            if c.kind == "dir_exists":
                p = self._p(a["path"])
                return {**base, "ok": p.is_dir(), "detail": f"{p} is_dir={p.is_dir()}"}
            if c.kind == "file_count_min":
                d = self._p(a.get("path", "."))
                n = sum(1 for _ in d.rglob(a.get("glob", "*"))) if d.is_dir() else 0
                want = int(a.get("n", 1))
                return {**base, "ok": n >= want, "detail": f"{d}: {n} files ≥ {want}"}
            if c.kind == "url_ok":
                return self._check_url(base, a)
            if c.kind == "reply_matches":
                ok = re.search(a["pattern"], reply or "", re.I | re.S) is not None
                return {**base, "ok": ok, "detail": f"reply matches /{a['pattern']}/={ok}"}
            if c.kind == "agent_review":
                from rad.agents import AgentRuntime
                rt = AgentRuntime(self.home, auto=True) if self.home else None
                if rt is None:
                    return {**base, "ok": False, "machine": False, "detail": "no home for agent runtime"}
                res = rt.review(a.get("subject") or reply or "", a.get("criteria") or [],
                                agent_id=a.get("agent", "reviewer"))
                grounded = res["tool_calls"] > 0 or bool(res["checked"])
                ok = res["pass"] and grounded
                detail = (f"reviewer {'passed' if res['pass'] else 'failed'}"
                          + ("" if grounded else " (ungrounded: read nothing)")
                          + (": " + "; ".join(res["issues"][:3]) if res["issues"] else ""))
                return {**base, "ok": ok, "machine": False, "detail": detail[:300], "run": res["run"]}
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

    def _check_url(self, base: Dict[str, Any], a: Dict[str, Any]) -> Dict[str, Any]:
        """Environment verification: is a URL really in the expected state?"""
        from rad.tools import html_to_text, http_get
        url = str(a.get("url", ""))
        try:
            code, raw, ctype = http_get(url, timeout=float(a.get("timeout", 20)))
        except Exception as e:
            return {**base, "ok": False, "detail": f"fetch failed: {e}"}
        want_status = int(a.get("status", 200))
        body = raw.decode("utf-8", "replace")
        text = html_to_text(body) if "html" in (ctype or "").lower() else body
        ok = code == want_status
        detail = f"status {code} (want {want_status})"
        if a.get("contains"):
            hit = str(a["contains"]).lower() in text.lower()
            ok = ok and hit
            detail += f", contains={hit}"
        if a.get("not_contains"):
            clean = str(a["not_contains"]).lower() not in text.lower()
            ok = ok and clean
            detail += f", not_contains={clean}"
        return {**base, "ok": ok, "detail": detail}

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


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
