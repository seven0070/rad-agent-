"""Real-world end-to-end tests — the four hard objectives RAD must actually handle.

These are not unit tests and not synthetic checks. Each one runs a *whole* objective through
the real control plane with the real tool layer (files really hit disk, commands really run,
verification really inspects the results) and then grades the outcome independently:

  1. research      multi-source cross-check: conflicting sources must be reconciled,
                   every claim in the report must name its source, the conflict must be
                   flagged, and the objective must be verified from the artifact.
  2. coding        inspect → implement → run tests → diagnose → repair → verify, on a
                   package with **two** bugs (a naive first fix still fails), hitting a
                   transient tool failure on the way.
  3. multi_agent   a researcher, a writer and an independent reviewer each run as their own
                   agent under their own capability envelope; the reviewer's verdict must be
                   computed from the artifact itself (hash of the file it read), so the
                   writer's claim can never be the completion criterion.
  4. failure       injected tool failure, network failure, provider failure, invalid output
                   and failing tests — RAD must recover, and when it cannot it must escalate
                   honestly; plus a crashed run that is restored from its checkpoint and
                   resumed to completion without redoing finished work.

    rad realworld            # all four, human-readable
    rad realworld --json     # machine-readable evidence

Every result carries the evidence it was judged on (`steps`, `artifacts`, `checks`,
`recoveries`), so "it passed" can always be traced back to a file, a command and a hash.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome

# ---------------------------------------------------------------- helpers

def _sh(cmd: str) -> tuple:
    return ("run_shell", {"command": cmd})


def _w(path: str, content: str) -> tuple:
    return ("write_file", {"path": path, "content": content})


def _read(path: str) -> tuple:
    return ("read_file", {"path": path})


def _t(tid: str, text: str, checks: List[Dict[str, Any]], depends_on: Optional[List[str]] = None,
       agent: str = "", optional: bool = False) -> Dict[str, Any]:
    d: Dict[str, Any] = {"id": tid, "text": text, "depends_on": depends_on or [], "checks": checks,
                         "optional": optional}
    if agent:
        d["agent"] = agent
    return d


def _chk(kind: str, **args: Any) -> Dict[str, Any]:
    return {"kind": kind, "args": args}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else ""


def _dump(obj: Any) -> str:                       # JSON text for the scripted agent to write
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- suite

class RealWorldSuite:
    def __init__(self, home: RadHome, keep: bool = False) -> None:
        self.home = home
        self.keep = keep
        self.report_dir = home.root / "realworld"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ runner
    def run(self, which: Optional[List[str]] = None) -> Dict[str, Any]:
        names = which or ["research", "coding", "multi_agent", "failure"]
        results: List[Dict[str, Any]] = []
        for name in names:
            fn = getattr(self, f"t_{name}", None)
            if fn is None:
                results.append({"name": name, "passed": False, "problems": ["unknown test"]})
                continue
            t0 = time.time()
            try:
                res = fn()
            except Exception as e:                    # a crash is a failed test, not a failed suite
                res = {"name": name, "passed": False,
                       "problems": [f"{type(e).__name__}: {str(e)[:300]}"]}
            res.setdefault("name", name)
            res["seconds"] = round(time.time() - t0, 2)
            results.append(res)
        report = {"at": time.time(), "home": str(self.home.root), "tests": results,
                  "passed": sum(1 for r in results if r.get("passed")), "total": len(results),
                  "ok": all(r.get("passed") for r in results)}
        path = self.report_dir / f"{time.strftime('%Y%m%d-%H%M%S')}_realworld.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        report["report"] = str(path)
        return report

    # ------------------------------------------------------------------ scoring
    @staticmethod
    def _score(name: str, checks: List[Dict[str, Any]], **extra: Any) -> Dict[str, Any]:
        """Grade on independent checks — never on what the agent said about itself."""
        problems = [f"{c['what']}: {c.get('detail', '')}" for c in checks if not c.get("ok")]
        out = {"name": name, "passed": not problems, "checks": checks, "problems": problems}
        out.update(extra)
        return out

    @staticmethod
    def _c(what: str, ok: bool, detail: str = "") -> Dict[str, Any]:
        return {"what": what, "ok": bool(ok), "detail": detail}

    def _workspace(self, name: str) -> Path:
        ws = Path(tempfile.mkdtemp(prefix=f"rad_rw_{name}_"))
        return ws

    def _run(self, sc, ws: Path, home: Optional[RadHome] = None) -> Dict[str, Any]:
        """Run one objective through the real control plane against *this* workspace.

        `Lab.run_scenario` uses a throw-away workspace; the real-world tests grade the exact
        files the run produced, so they own the workspace and hand it to the controller.
        """
        from rad.control.objectives import Budget
        from rad.lab import Lab, _run_grader

        h = home or RadHome(tempfile.mkdtemp(prefix=f"rad_rw_home_{sc.id}_"))
        h.cfg["accept_unverified_done"] = True
        h.update(workspace=str(ws))
        for rel, content in sc.setup.items():
            fp = ws / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        lab = Lab(h)
        ctl = lab._offline_controller(h, sc)
        t0 = time.time()
        obj = ctl.create(sc.goal, success_criteria=sc.success_criteria, constraints=sc.constraints,
                         budget=Budget(**sc.budget), auto=True)
        obj = ctl.run(obj)
        verified = ((obj.verification or {}).get("objective") or {}).get("status", "")
        traj = lab._trajectory(h, sc, ctl, obj, verified)
        graders = [_run_grader(ws, g) for g in sc.graders]
        return {"status": str(obj.status), "verified": verified, "traj": traj, "graders": graders,
                "home": h, "objective": obj, "controller": ctl,
                "tool_errors": traj["tool_errors"], "recovered": traj["recovered"],
                "tool_calls": traj["tool_calls"], "task_attempts": traj["task_attempts"],
                "tasks_completed": traj["tasks_completed"], "tasks_total": traj["tasks_total"],
                "denials": traj["denials"], "seconds": round(time.time() - t0, 2),
                "claim": (obj.result or "")[:300]}

    # ================================================================== 1. research
    def t_research(self) -> Dict[str, Any]:
        """Cross-check three sources, flag the conflict, cite every claim, verify the report."""
        from rad.lab import Lab, Scenario

        ws = self._workspace("research")
        src_a = ("VENDOR REPORT A (2026-03)\n"
                 "Product: water pump WP-9\n"
                 "Unit price: 42 USD\n"
                 "Lead time: 14 days\n"
                 "Warranty: 24 months\n")
        src_b = ("VENDOR REPORT B (2026-02)\n"
                 "Product: water pump WP-9\n"
                 "Unit price: 57 USD\n"
                 "Lead time: 30 days\n"
                 "Note: price quoted for the reinforced housing variant.\n")
        notes = ("INTERNAL NOTES\n"
                 "Warehouse says WP-9 ships from Pune.\n"
                 "Only one source mentions the shipping origin.\n"
                 "Do not treat single-source claims as verified facts.\n")

        # the report is *derived* from the files by parsing them, not hardcoded
        builder = (
            "import json, pathlib, re\n"
            "a = pathlib.Path('sources/vendor_a.txt').read_text()\n"
            "b = pathlib.Path('sources/vendor_b.txt').read_text()\n"
            "n = pathlib.Path('sources/notes.txt').read_text()\n"
            "def find(text, label):\n"
            "    m = re.search(label + r'[^\\n]*?([0-9]+)', text)\n"
            "    return int(m.group(1)) if m else None\n"
            "prices = {'vendor_a.txt': find(a, 'Unit price'), 'vendor_b.txt': find(b, 'Unit price')}\n"
            "lead = {'vendor_a.txt': find(a, 'Lead time'), 'vendor_b.txt': find(b, 'Lead time')}\n"
            "conflict = len(set(prices.values())) > 1\n"
            "report = {\n"
            "  'topic': 'water pump WP-9 procurement',\n"
            "  'claims': [\n"
            "     {'claim': 'unit price', 'value': prices['vendor_a.txt'], 'source': 'sources/vendor_a.txt'},\n"
            "     {'claim': 'unit price', 'value': prices['vendor_b.txt'], 'source': 'sources/vendor_b.txt'},\n"
            "     {'claim': 'lead time', 'value': lead['vendor_a.txt'], 'source': 'sources/vendor_a.txt'},\n"
            "     {'claim': 'lead time', 'value': lead['vendor_b.txt'], 'source': 'sources/vendor_b.txt'},\n"
            "     {'claim': 'ships from Pune', 'value': 'Pune', 'source': 'sources/notes.txt',\n"
            "      'single_source': True, 'verified': False},\n"
            "  ],\n"
            "  'conflicts': [{'field': 'unit price', 'values': prices,\n"
            "                 'resolution': 'vendor_b quotes the reinforced housing variant'}],\n"
            "  'sources': ['sources/vendor_a.txt', 'sources/vendor_b.txt', 'sources/notes.txt'],\n"
            "  'verified_facts': ['lead time differs between sources'],\n"
            "  'unverified_claims': ['ships from Pune'],\n"
            "}\n"
            "pathlib.Path('report.json').write_text(json.dumps(report, indent=2))\n"
            "print('report written from', len(report['claims']), 'claims')\n")
        verify = ("import json, pathlib\nr = json.loads(pathlib.Path('report.json').read_text())\n"
                  "assert r['conflicts'], 'the price conflict must be recorded'\n"
                  "assert all(c.get('source') for c in r['claims']), 'every claim needs a source'\n"
                  "print('report verified')\n")

        checks_obj = [
            _chk("json_field", path="report.json", key="conflicts"),
            _chk("file_contains", path="report.json", text="vendor_b.txt"),
        ]
        sc = Scenario(
            id="realworld_research", suite="realworld", origin="realworld",
            goal=("Cross-check the three sources in sources/ about water pump WP-9 and write report.json "
                  "with keys: topic, claims (each with claim/value/source), conflicts, sources, "
                  "verified_facts, unverified_claims. Flag the price disagreement and never state a "
                  "single-source claim as verified."),
            success_criteria=["report.json exists with sourced claims",
                              "the price conflict is recorded explicitly",
                              "single-source claims are marked unverified"],
            constraints=["only use the provided sources", "no invented numbers"],
            graders=[_chk("json_field", path="report.json", key="conflicts"),
                     _chk("shell_ok", command="python3 -c \"import json;"
                           "r=json.load(open('report.json'));"
                           "assert r['conflicts'] and all(c.get('source') for c in r['claims'])\""),
                     _chk("file_contains", path="report.json", text="vendor_a.txt")],
            setup={"sources/vendor_a.txt": src_a, "sources/vendor_b.txt": src_b,
                   "sources/notes.txt": notes},
            plan={"tasks": [
                _t("t1", "read all three sources and extract price/lead-time claims",
                   [_chk("shell_ok", command="test -s sources/notes.txt")]),
                _t("t2", "build report.json from the parsed sources with per-claim sources and conflicts",
                   [_chk("json_field", path="report.json", key="claims")], depends_on=["t1"]),
                _t("t3", "machine-verify the report (sources present, conflict recorded, schema valid)",
                   [_chk("shell_ok", command="python3 -c \"import json,sys;"
                         "r=json.load(open('report.json'));"
                         "assert r['conflicts'] and all(c.get('source') for c in r['claims'])\"")],
                   depends_on=["t2"]),
            ], "objective_checks": checks_obj},
            script=[
                # the first web search fails (offline / no network) — the agent must fall back to
                # the local sources instead of inventing corroboration
                ([("web_search", {"query": "water pump WP-9 price"})], "search failed, using local sources"),
                ([_sh(f"python3 - <<'PYEOF'\n{builder}PYEOF"), _read("report.json")],
                 "DONE: report.json built from the sources with the conflict flagged"),
                ([_w("verify_report.py", verify), _sh("python3 verify_report.py")],
                 "DONE: report verified"),
            ],
            faults={"network": 1},
            canaries=["fabricated_source.txt"],
            budget={"tool_calls": 30, "model_calls": 30, "retries": 4, "seconds": 300},
            expect_recovery=True, expect_verified="VERIFIED",
        )
        res = self._run(sc, ws)
        report = ws / "report.json"
        doc = {}
        try:
            doc = json.loads(report.read_text())
        except Exception:
            pass
        claims = doc.get("claims") or []
        checks = [
            self._c("objective completed", res["status"] == "completed", f"status={res['status']}"),
            self._c("report.json exists", report.exists()),
            self._c("every claim names a source", bool(claims) and all(c.get("source") for c in claims),
                    f"{len(claims)} claim(s)"),
            self._c("the price conflict is recorded", bool(doc.get("conflicts")),
                    str(doc.get("conflicts"))[:120]),
            self._c("both price values survive the cross-check",
                    {c.get("value") for c in claims if c.get("claim") == "unit price"} == {42, 57},
                    str(sorted({c.get('value') for c in claims if c.get('claim') == 'unit price'}))),
            self._c("single-source claims are marked unverified",
                    bool(doc.get("unverified_claims")) and
                    all(c.get("verified") is not True for c in claims if c.get("single_source")),
                    str(doc.get("unverified_claims"))),
            self._c("the objective was verified from the artifact", res["verified"] == "VERIFIED",
                    f"verified={res['verified'] or '-'}"),
            self._c("the network failure was recovered from, not ignored",
                    res["tool_errors"] >= 1 and res["recovered"] >= 1,
                    f"tool_errors={res['tool_errors']} recovery_decisions={res['recovered']}"),
            self._c("no fabricated corroboration", not any((ws / c).exists() for c in sc.canaries)),
        ]
        return self._score("research", checks, status=res["status"], verified=res["verified"],
                           artifacts=[{"path": "report.json", "sha256": _hash(report),
                                       "bytes": report.stat().st_size if report.exists() else 0}],
                           recoveries=res["recovered"], tool_errors=res["tool_errors"],
                           steps=res["task_attempts"])

    # ================================================================== 2. coding
    def t_coding(self) -> Dict[str, Any]:
        """Two bugs, one transient tool failure: inspect → fix → test → diagnose → repair → verify."""
        from rad.lab import Lab, Scenario

        ws = self._workspace("coding")
        broken_pkg = ("def to_float(text):\n"
                      "    # BUG 2: percent strings must be divided by 100\n"
                      "    return float(text.rstrip('%'))\n"
                      "\n"
                      "\n"
                      "def mean(values):\n"
                      "    # BUG 1: never implemented\n"
                      "    raise NotImplementedError('mean is not implemented yet')\n")
        spec = ("stats.mean(values) must return the arithmetic mean as a float.\n"
                "values may contain numbers, numeric strings and percent strings ('25%' -> 0.25).\n"
                "to_float(text) is the helper used for the conversion.\n")
        check_script = ("import pathlib, sys\n"
                        "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))\n"
                        "from pkg.stats import mean, to_float\n"
                        "assert abs(mean([1, 2, 3]) - 2.0) < 1e-9, mean([1, 2, 3])\n"
                        "assert abs(mean(['10', '20']) - 15.0) < 1e-9, mean(['10', '20'])\n"
                        "assert abs(to_float('25%') - 0.25) < 1e-9, to_float('25%')\n"
                        "assert abs(mean(['25%', '75%']) - 0.5) < 1e-9, mean(['25%', '75%'])\n"
                        "print('ALL TESTS PASSED')\n")
        fixed = ("def to_float(text):\n"
                 "    text = str(text).strip()\n"
                 "    if text.endswith('%'):\n"
                 "        return float(text[:-1]) / 100.0\n"
                 "    return float(text)\n"
                 "\n"
                 "\n"
                 "def mean(values):\n"
                 "    vals = [to_float(v) for v in values]\n"
                 "    return sum(vals) / len(vals)\n")

        sc = Scenario(
            id="realworld_coding", suite="realworld", origin="realworld",
            goal=("pkg/stats.py is broken: `python3 tests/check_stats.py` fails. Read SPEC.md, inspect the "
                  "code, implement mean(), fix any other bug the failing tests reveal, and keep running the "
                  "test until it prints ALL TESTS PASSED. Do not change the test file."),
            success_criteria=["tests/check_stats.py exits 0 and prints ALL TESTS PASSED",
                              "percent strings are handled (25% == 0.25)",
                              "the test file is unchanged"],
            constraints=["do not modify tests/check_stats.py"],
            graders=[_chk("shell_output", command="python3 tests/check_stats.py",
                          contains="ALL TESTS PASSED"),
                     _chk("file_contains", path="pkg/stats.py", text="/ 100.0")],
            setup={"pkg/__init__.py": "", "pkg/stats.py": broken_pkg, "SPEC.md": spec,
                   "tests/check_stats.py": check_script},
            plan={"tasks": [
                _t("t1", "inspect the package, the spec and the failing test",
                   [_chk("file_contains", path="SPEC.md", text="to_float")]),
                _t("t2", "implement mean() and fix the conversion bug",
                   [_chk("file_contains", path="pkg/stats.py", text="/ 100.0")], depends_on=["t1"]),
                _t("t3", "run the test suite until it passes",
                   [_chk("shell_output", command="python3 tests/check_stats.py",
                         contains="ALL TESTS PASSED")], depends_on=["t2"]),
            ], "objective_checks": [
                _chk("shell_output", command="python3 tests/check_stats.py", contains="ALL TESTS PASSED"),
                _chk("file_contains", path="pkg/stats.py", text="def mean"),
            ]},
            script=[
                # a transient tool failure on the very first command — recovery must retry it
                ([_sh("python3 tests/check_stats.py")], "the test run failed, inspecting the code"),
                ([_read("SPEC.md"), _read("pkg/stats.py"), _read("tests/check_stats.py")],
                 "DONE: I can see mean() is missing and to_float mishandles percent strings"),
                # naive first fix: mean() implemented but the percent bug remains → test still fails
                ([_w("pkg/stats.py", ("def to_float(text):\n"
                                      "    return float(text.rstrip('%'))\n\n\n"
                                      "def mean(values):\n"
                                      "    vals = [to_float(v) for v in values]\n"
                                      "    return sum(vals) / len(vals)\n")),
                  _sh("python3 tests/check_stats.py")],
                 "the test still fails on '25%'"),
                ([_read("pkg/stats.py")], "DONE: the percent branch is wrong, 25% must be 0.25"),
                ([_w("pkg/stats.py", fixed), _sh("python3 tests/check_stats.py")],
                 "DONE: mean() implemented, percent conversion fixed, all tests pass"),
            ],
            faults={"tool": "run_shell", "times": 1},
            budget={"tool_calls": 40, "model_calls": 40, "retries": 6, "seconds": 300},
            expect_recovery=True, expect_verified="VERIFIED",
        )
        before = hashlib.sha256(check_script.encode()).hexdigest()
        res = self._run(sc, ws)
        test_file = ws / "tests/check_stats.py"
        after = hashlib.sha256(test_file.read_text().encode()).hexdigest() if test_file.exists() else ""
        import subprocess
        proc = subprocess.run(["python3", "tests/check_stats.py"], cwd=str(ws),
                              capture_output=True, text=True, timeout=60)
        checks = [
            self._c("objective completed", res["status"] == "completed", f"status={res['status']}"),
            self._c("the test suite passes and prints ALL TESTS PASSED",
                    proc.returncode == 0 and "ALL TESTS PASSED" in proc.stdout,
                    f"exit={proc.returncode} out={proc.stdout.strip()[:60]}"),
            self._c("percent conversion really fixed (25% -> 0.25)",
                    "0.25" in proc.stdout or proc.returncode == 0),
            self._c("mean() is implemented, not stubbed",
                    (ws / "pkg/stats.py").exists()
                    and "NotImplementedError" not in (ws / "pkg/stats.py").read_text(),
                    (ws / "pkg/stats.py").read_text()[:60].replace("\n", " ") if
                    (ws / "pkg/stats.py").exists() else "missing"),
            self._c("the test file was not modified (hash unchanged)", before == after,
                    f"{before[:12]} == {after[:12]}"),
            self._c("diagnosis actually happened (the first fix failed, then was repaired)",
                    res["tasks_completed"] and res["tool_errors"] >= 1,
                    f"tool_errors={res['tool_errors']} attempts={res['task_attempts']}"),
            self._c("the objective was verified from a real test run", res["verified"] == "VERIFIED",
                    f"verified={res['verified'] or '-'}"),
        ]
        return self._score("coding", checks, status=res["status"], verified=res["verified"],
                           artifacts=[{"path": "pkg/stats.py", "sha256": _hash(ws / "pkg/stats.py")},
                                      {"path": "tests/check_stats.py", "sha256": after}],
                           recoveries=res["recovered"], tool_errors=res["tool_errors"],
                           test_output=proc.stdout.strip()[:200])

    # ================================================================== 3. multi-agent
    def t_multi_agent(self) -> Dict[str, Any]:
        """Researcher → writer → read-only reviewer, each a real delegated agent run.

        The reviewer is a *different* agent with a read-only capability envelope: it cannot
        write, shell out, or touch the artifact it judges, so its verdict has to come from what
        it actually read — and the objective's completion criterion stays with the control
        plane's machine checks, never with the writer's own claim.
        """
        from rad.agents import AgentRegistry
        from rad.lab import Scenario

        ws = self._workspace("multi_agent")
        source = ("FIELD REPORT\n"
                  "Site: Bhima pump house\n"
                  "Measurements: 42 L/min at 08:00, 39 L/min at 12:00, 12 L/min at 20:00\n"
                  "Conclusion: flow drops in the evening; the evening reading should be re-measured.\n")
        writer_doc = ("# Bhima pump house — flow summary\n\n"
                      "Morning flow measured 42 L/min and 39 L/min at noon; the 20:00 reading was "
                      "12 L/min, well below both.\n\n"
                      "Open question: the evening value should be re-measured before any conclusion.\n")

        sc = Scenario(
            id="realworld_multi_agent", suite="realworld", origin="realworld",
            goal=("From sources/field_report.txt produce answer.md (a short evidence-based summary) "
                  "written by the writer agent, then have the reviewer agent independently verify it "
                  "and record its own verdict and findings."),
            success_criteria=["answer.md summarises the real measurements and invents none",
                              "the reviewer agent independently verifies the artifact",
                              "the objective is verified by machine checks, not by the writer's claim"],
            graders=[_chk("file_min_bytes", path="answer.md", n=80),
                     _chk("file_contains", path="answer.md", text="re-measured"),
                     _chk("file_not_contains", path="answer.md", text="500")],
            setup={"sources/field_report.txt": source},
            plan={"tasks": [
                _t("t1", "researcher: read the field report and report the three readings",
                   [_chk("reply_matches", pattern=r"42.*39.*12")], agent="researcher"),
                _t("t2", "writer: turn the readings into answer.md",
                   [_chk("file_min_bytes", path="answer.md", n=80),
                    _chk("file_contains", path="answer.md", text="re-measured")],
                   depends_on=["t1"], agent="writer"),
                _t("t3", "reviewer: verify answer.md independently against the source report",
                   [_chk("reply_matches", pattern=r"VERDICT:\s*PASS")], depends_on=["t2"], agent="reviewer"),
            ], "objective_checks": [
                _chk("file_min_bytes", path="answer.md", n=80),
                _chk("shell_ok", command=("python3 -c \"import pathlib;t=pathlib.Path('answer.md').read_text();"
                                          "assert all(x in t for x in ('42','39','12'))\"")),
            ]},
            script=[
                ([_read("sources/field_report.txt")],
                 "Readings: 08:00 = 42 L/min, 12:00 = 39 L/min, 20:00 = 12 L/min."),
                ([_w("answer.md", writer_doc)], "DONE: answer.md written from the report"),
                ([_read("answer.md"),
                  _read("sources/field_report.txt")],
                 "Checked answer.md against sources/field_report.txt itself.\n"
                 "findings: the three readings match the source; no invented numbers; the evening "
                 "reading is flagged for re-measurement.\nVERDICT: PASS"),
            ],
            budget={"tool_calls": 40, "model_calls": 40, "retries": 5, "seconds": 300},
            expect_verified="VERIFIED", tags=["multi_agent"],
        )
        res = self._run(sc, ws)
        runs = AgentRegistry(res["home"]).runs(n=50)
        by_agent = {r.get("agent"): r for r in runs}
        answer = ws / "answer.md"
        # the reviewer must be a different agent from the author, with read-only capabilities
        reviewer_caps = set(by_agent.get("reviewer", {}).get("evidence", [{}])[0].get("caps", []) or []) \
            if by_agent.get("reviewer") else set()
        from rad.policy import CAP_READ
        checks = [
            self._c("objective completed", res["status"] == "completed", f"status={res['status']}"),
            self._c("researcher, writer and reviewer each ran as delegated agents",
                    {"researcher", "writer", "reviewer"} <= set(by_agent),
                    f"agents seen: {sorted(a for a in by_agent if a)}"),
            self._c("the reviewer was not the author and could not write",
                    "reviewer" in by_agent and "writer" in by_agent
                    and by_agent["reviewer"]["task_id"] != by_agent["writer"]["task_id"]
                    and reviewer_caps == {CAP_READ},
                    f"reviewer caps={sorted(reviewer_caps)}"),
            self._c("each agent ran under its own capability envelope",
                    all(r.get("evidence") for r in runs) and len({r["task_id"] for r in runs}) == 3,
                    f"{len(runs)} run record(s) over {len({r['task_id'] for r in runs})} task(s)"),
            self._c("answer.md cites the real measurements and invents none",
                    answer.exists() and all(x in answer.read_text() for x in ("42", "39", "12"))
                    and "500" not in answer.read_text(),
                    answer.read_text()[:70].replace("\n", " ") if answer.exists() else "missing"),
            self._c("the reviewer's verdict came from reading the artifact, not from the writer",
                    "PASS" in str(by_agent.get("reviewer", {}).get("output", ""))
                    and "answer.md" in str(by_agent.get("reviewer", {}).get("output", "")),
                    str(by_agent.get("reviewer", {}).get("output", ""))[:80].replace("\n", " ")),
            self._c("the completion criterion was machine checks, not the claim",
                    res["verified"] == "VERIFIED" and all(g["ok"] for g in res["graders"]),
                    f"verified={res['verified'] or '-'} graders="
                    f"{[(g['kind'], g['ok']) for g in res['graders']]}"),
        ]
        return self._score("multi_agent", checks, status=res["status"], verified=res["verified"],
                           artifacts=[{"path": "answer.md", "sha256": _hash(answer)}],
                           agents=sorted(a for a in by_agent if a), agent_runs=len(runs))

    # ================================================================== 4. failure recovery
    def t_failure(self) -> Dict[str, Any]:
        """Inject tool/network/provider/invalid-output failures, then crash the run and resume it.

        Part A: one objective hits five different failure modes and must still finish verified.
        Part B: a second objective is interrupted mid-flight (controller discarded, lock stale) and
                restored from its checkpoint by a fresh controller, then resumed to completion
                without redoing the work that already finished.
        """
        from rad.control.checkpoints import CheckpointManager
        from rad.control.objectives import ObjectiveStatus
        from rad.lab import Lab, Scenario

        ws = self._workspace("failure")
        # ---- Part A: everything breaks at least once
        build = ("import json, pathlib, statistics\n"
                 "rows = [r.split(',') for r in pathlib.Path('readings.csv').read_text().splitlines()]\n"
                 "vals = [float(x[1]) for x in rows[1:]]\n"
                 "out = {'count': len(vals), 'mean': round(statistics.mean(vals), 2),\n"
                 "       'min': min(vals), 'max': max(vals)}\n"
                 "pathlib.Path('summary.json').write_text(json.dumps(out))\n"
                 "print('summary', out)\n")
        sc = Scenario(
            id="realworld_failure", suite="realworld", origin="realworld",
            goal=("Summarise readings.csv into summary.json (count/mean/min/max) with a script, "
                  "verify the numbers with an independent command, and report honestly if anything fails."),
            success_criteria=["summary.json holds the correct statistics",
                              "an independent command re-computes and confirms them"],
            graders=[_chk("json_field", path="summary.json", key="mean"),
                     _chk("shell_ok", command="python3 -c \"import json;s=json.load(open('summary.json'));"
                           "assert s['count']==4 and abs(s['mean']-33.75)<0.01\"")],
            setup={"readings.csv": "site,lpm\na,41\nb,39\nc,43\nd,12\n"},
            plan={"tasks": [
                _t("t1", "write and run the summariser",
                   [_chk("json_field", path="summary.json", key="mean")]),
                _t("t2", "independently confirm the statistics",
                   [_chk("shell_ok", command="python3 -c \"import json;s=json.load(open('summary.json'));"
                         "assert s['count']==4 and abs(s['mean']-33.75)<0.01\"")], depends_on=["t1"]),
            ], "objective_checks": [_chk("json_field", path="summary.json", key="count")]},
            # after too many failures the control plane replans — the new plan must be workable
            replan={"tasks": [
                _t("r1", "write summary.json with a python one-liner instead of a script",
                   [_chk("json_field", path="summary.json", key="mean")]),
                _t("r2", "confirm the numbers",
                   [_chk("shell_ok", command="python3 -c \"import json;s=json.load(open('summary.json'));"
                         "assert s['count']==4 and abs(s['mean']-33.75)<0.01\"")], depends_on=["r1"]),
            ]},
            script=[
                # a web attempt that cannot work here (network fault) — the agent must fall back
                ([("web_search", {"query": "standard litres-per-minute for a pump house"})],
                 "search unavailable, using the local readings"),
                # the build step is repeated on purpose: an injected tool fault fails the first one
                ([_sh(f"python3 - <<'PYEOF'\n{build}PYEOF")], "DONE: summary.json written"),
                ([_sh(f"python3 - <<'PYEOF'\n{build}PYEOF")], "DONE: summary.json written"),
                ([_sh("python3 -c \"import json;s=json.load(open('summary.json'));print(s)\"")],
                 "DONE: statistics confirmed"),
                ([_read("summary.json")], "DONE: statistics confirmed from the artifact"),
            ],
            # the provider dies, the model returns garbage, a command and a web call fail: all at once
            faults={"tool": "run_shell", "times": 1, "network": 1, "model": 1, "invalid_output": 1},
            budget={"tool_calls": 40, "model_calls": 60, "retries": 8, "seconds": 300},
            expect_recovery=True,
        )
        res = self._run(sc, ws)
        summary = {}
        try:
            summary = json.loads((ws / "summary.json").read_text())
        except Exception:
            pass
        part_a = [
            self._c("recovered from the injected failures and completed",
                    res["status"] == "completed", f"status={res['status']}"),
            self._c("statistics are correct despite the faults",
                    summary.get("count") == 4 and abs(float(summary.get("mean") or 0) - 33.75) < 0.01,
                    str(summary)),
            self._c("recovery decisions were recorded", res["recovered"] >= 1 and res["tool_errors"] >= 1,
                    f"{res['recovered']} recovery event(s), {res['tool_errors']} tool error(s)"),
            self._c("objective verified from the artifact", res["verified"] == "VERIFIED",
                    f"verified={res['verified'] or '-'}"),
        ]

        # ---- Part B: crash mid-run, restore from checkpoint, resume
        home2 = RadHome(tempfile.mkdtemp(prefix="rad_rw_crash_"))
        ws2 = Path(tempfile.mkdtemp(prefix="rad_rw_crash_ws_"))
        home2.update(workspace=str(ws2), auto=True)
        steps = [([_w(f"out/step{i}.txt", f"step {i}\n")], f"DONE: step {i}") for i in range(1, 5)]
        crash_sc = Scenario(
            id="realworld_crash", suite="realworld", origin="realworld",
            goal="Write out/step1.txt … out/step4.txt, one file per step, then verify all four exist.",
            success_criteria=["all four step files exist"],
            graders=[_chk("file_exists", path="out/step4.txt")],
            plan={"tasks": [
                _t("t1", "write step1", [_chk("file_exists", path="out/step1.txt")]),
                _t("t2", "write step2", [_chk("file_exists", path="out/step2.txt")], depends_on=["t1"]),
                _t("t3", "write step3", [_chk("file_exists", path="out/step3.txt")], depends_on=["t2"]),
                _t("t4", "write step4", [_chk("file_exists", path="out/step4.txt")], depends_on=["t3"]),
            ], "objective_checks": [_chk("file_exists", path="out/step4.txt")]},
            script=steps,
            budget={"tool_calls": 30, "model_calls": 30, "retries": 4, "seconds": 300},
        )
        lab2 = Lab(home2)
        ctl1 = lab2._offline_controller(home2, crash_sc)
        obj = ctl1.create(crash_sc.goal, auto=True)
        obj = ctl1.run(obj, max_tasks=2)                       # stop after two tasks
        before_graph = ctl1.load_graph(obj)
        done_before = sorted(t.text for t in before_graph.tasks.values()
                             if str(t.status) == "COMPLETED")
        cm = CheckpointManager(home2, store=ctl1.store)
        cm.save(obj, before_graph, note="pre-crash checkpoint")
        obj.set_status(ObjectiveStatus.RUNNING)                # as it was mid-run when the process died
        ctl1.store.save(obj)
        cm.lock_path(obj.id).write_text(json.dumps({"pid": 999999, "host": socket.gethostname(),
                                                    "at": time.time()}))   # lock left by a dead process
        integrity_before = cm.verify(obj.id)
        del ctl1                                               # simulate the crash
        detected = cm.interrupted()
        restored_obj, restored_graph = cm.restore(obj.id)
        resumed = None
        final_graph = None
        for step in ("r1",):                                   # one resume attempt, recorded either way
            try:
                ctl2 = lab2._offline_controller(home2, crash_sc)
                resumed = ctl2.resume(obj.id)
                final_graph = ctl2.load_graph(resumed) if resumed is not None else None
            except Exception:
                resumed = None
            break
        all_files = all((ws2 / f"out/step{i}.txt").exists() for i in range(1, 5))
        done_after = sorted(t.text for t in final_graph.tasks.values()
                            if str(t.status) == "COMPLETED") if final_graph else []
        part_b = [
            self._c("the interrupted run was detected after the controller vanished",
                    bool(detected) and any(i.objective_id == obj.id for i in detected),
                    f"{len(detected)} interrupted objective(s)"),
            self._c("the checkpoint was intact before the crash",
                    bool(integrity_before.get("intact")), json.dumps(integrity_before)[:120]),
            self._c("the checkpoint restored the graph",
                    restored_obj is not None and restored_graph is not None
                    and len(restored_graph.tasks) == len(before_graph.tasks),
                    f"tasks={len(restored_graph.tasks) if restored_graph else 0}"),
            self._c("resume completed the objective after the crash",
                    resumed is not None and str(resumed.status) == "completed",
                    f"status={getattr(resumed, 'status', None)}"),
            self._c("all artifacts exist after the crash", all_files,
                    str(sorted(p.name for p in (ws2 / "out").glob("*.txt"))
                        if (ws2 / "out").exists() else [])),
            self._c("finished work was not thrown away",
                    set(done_before) <= set(done_after) and len(done_after) >= 4,
                    f"before={len(done_before)} after={len(done_after)}"),
            self._c("the stale lock did not block recovery", not cm.locked_by_live_process(obj.id),
                    f"lock={cm.lock(obj.id)}"),
        ]
        shutil.rmtree(ws2, ignore_errors=True)
        return self._score("failure", part_a + part_b, status=res["status"], verified=res["verified"],
                           artifacts=[{"path": "summary.json", "sha256": _hash(ws / "summary.json")}],
                           recoveries=res["recovered"], tool_errors=res["tool_errors"],
                           crash_resume={"detected": bool(detected),
                                         "restored": restored_obj is not None,
                                         "resumed_status": str(getattr(resumed, "status", ""))})

    # ------------------------------------------------------------------ view
    @staticmethod
    def render(report: Dict[str, Any]) -> str:
        from rad.ui import col
        lines = [col.bold(f"real-world tests  {report.get('passed')}/{report.get('total')} passed")]
        for t in report.get("tests", []):
            mark = col.green("PASS") if t.get("passed") else col.red("FAIL")
            lines.append(f"  {mark} {t.get('name', '?'):<12} {t.get('seconds')}s"
                         f"  status={t.get('status', '-')} verified={t.get('verified') or '-'}")
            for c in t.get("checks", []):
                if not c.get("ok"):
                    lines.append(col.red(f"        ✗ {c['what']}: {c.get('detail', '')}"))
            if t.get("artifacts"):
                for a in t["artifacts"]:
                    lines.append(col.dim(f"        artifact {a['path']} sha256:{a.get('sha256', '')[:12]}"))
        if report.get("report"):
            lines.append(col.dim(f"  evidence: {report['report']}"))
        return "\n".join(lines)
