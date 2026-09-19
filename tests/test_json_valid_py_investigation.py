"""RW-065 Class A probe: json_valid checks on .py paths.

Investigate-first. No product patch. Needle off, max_plan_tasks 16, default
Budget.tool_calls 60 — asserted, not changed. Package stays 0.3.0.

Question: does the planner/control plane incorrectly accept or emit
json_valid on .py (or non-JSON) paths, causing false FAILED verification
→ ENVIRONMENT_FAILURE repair noise?

Scenarios:
  A — json_valid on .json → OK (valid JSON) / fail (invalid JSON)
  B — json_valid on .py → evaluated as JSON (fails); recovery is VALIDATION
      coding repair, not ENVIRONMENT
  C — coding-goal inferred checks never attach json_valid to .py

Live RW-065 ENVIRONMENT_FAILURE is reconstructed as _ENV matching
"No such file" in shell observations (11B thrashing), the same designed
path as F-18 — not json_valid-on-py.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control import Controller
from rad.control import events as E
from rad.control.codingloop import infer_coding_checks
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observation, Observer
from rad.control.planner import PLAN_PROMPT, Planner, _checks
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Check, Task
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from rad.tools import ToolCtx, run_tool

RW065_GOAL = (
    "Create a word_counter project with these deliverables:\n"
    "1. word_counter.py — function that counts words in fixed string hello world "
    "and returns integer 2\n"
    "2. result.json — valid JSON object with key words equal to integer 2 (not 6)\n"
    "3. test_word_counter.py — tests asserting counter returns 2 and/or "
    "result.json has words==2\n"
    "4. Run the tests successfully so they pass\n"
    "5. Do not write a path/file body that is only a DONE: pollution claim"
)

VALID_PY = (
    "def count_words(text):\n"
    "    return len(text.split())\n"
)

JSON_VALID_ON_PY_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "Create word_counter.py with word counting function",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "word_counter.py"}},
            {"kind": "json_valid", "args": {"path": "word_counter.py"},
             "description": "word_counter.py is a valid Python file"},
        ],
    }],
    "objective_checks": [
        {"kind": "json_valid", "args": {"path": "result.json"}},
    ],
}


class ScriptedSession:
    script = []
    prompts = []

    def __init__(self, home, auto=False, **kw):
        self.home = home
        self.tool_runner = run_tool
        self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)

    def think(self, prompt: str) -> str:
        type(self).prompts.append(prompt)
        if not type(self).script:
            return "DONE: nothing left in script"
        step = type(self).script.pop(0)
        if isinstance(step, Exception):
            raise step
        actions, reply = step
        for tool, args in actions:
            self.tool_runner(tool, args, self.ctx)
        return reply

    def close(self):
        pass


def _plan_llm(plan):
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan)
        if "strict verifier" in prompt:
            return json.dumps({"pass": True, "reason": "looks fine"})
        return "YES"
    return llm


def _ctl(home, scripted, plan=None, llm=None):
    return Controller(home, session_factory=scripted, llm=llm or (_plan_llm(plan) if plan else None),
                      quiet=True)


def _ob(task: Task, out: str, status: str = "error", tool: str = "run_shell") -> Observation:
    return Observation.new(objective_id="o", task_id=task.id, action_id="a", tool=tool,
                           args={}, status=status, output=out, duration_ms=1)


def _ver(ws, home) -> Verifier:
    return Verifier(ws, Observer(home.root / "obs"), home=home)


# ---------------------------------------------------------------- architecture freeze

def test_json_valid_py_investigation_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.0"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_asks_json_valid_on_json_artifacts_not_py():
    assert "json_valid on every .json artifact" in PLAN_PROMPT
    assert "shell_ok" in PLAN_PROMPT
    assert "json_valid on every .py" not in PLAN_PROMPT


# ---------------------------------------------------------------- Scenario A — json_valid on .json

def test_scenario_a_json_valid_on_json_ok(home, tmp_path):
    ws = tmp_path / "ws_a"
    ws.mkdir()
    (ws / "result.json").write_text('{"words": 2}', encoding="utf-8")
    r = _ver(ws, home).run_check(Check("json_valid", {"path": "result.json"}))
    assert r["ok"] is True
    assert "valid JSON" in r["detail"]


def test_scenario_a_json_valid_on_invalid_json_fails(home, tmp_path):
    ws = tmp_path / "ws_a_bad"
    ws.mkdir()
    (ws / "result.json").write_text("{", encoding="utf-8")
    r = _ver(ws, home).run_check(Check("json_valid", {"path": "result.json"}))
    assert r["ok"] is False
    assert "invalid JSON" in r["detail"]


# ---------------------------------------------------------------- Scenario B — json_valid on .py

def test_scenario_b_json_valid_on_py_fails_as_not_json(home, tmp_path):
    """json_valid means parse-as-JSON. Valid Python is not JSON — fail is honest."""
    ws = tmp_path / "ws_b"
    ws.mkdir()
    (ws / "word_counter.py").write_text(VALID_PY, encoding="utf-8")
    r = _ver(ws, home).run_check(Check(
        "json_valid", {"path": "word_counter.py"},
        description="word_counter.py is a valid Python file",
    ))
    assert r["ok"] is False
    assert "invalid JSON" in r["detail"]


def test_scenario_b_json_valid_on_py_is_validation_repair_not_environment():
    """Isolated json_valid-on-py (no env-token in observations) is VALIDATION.

    Gen2 coding loop inserts a repair with the concrete json_valid failure.
    That is not ENVIRONMENT_FAILURE / 'missing dependency/file'.
    """
    t = Task.new("o", "Create word_counter.py with word counting function")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "json_valid",
         "detail": "word_counter.py invalid JSON: Expecting value: line 1 column 1 (char 0)"},
    ]}
    assert classify(t, [], verification=ver) == FailureClass.VALIDATION
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.failure_class == FailureClass.VALIDATION
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy == "repair"
    assert d.data.get("coding_repair") is True
    assert "json_valid" in d.hint or "invalid JSON" in d.hint
    assert "missing dependency/file" not in d.reason


def test_scenario_b_llm_plan_accepts_json_valid_on_py_without_remap(tmp_path):
    """Models propose. RAD keeps the emitted json_valid-on-py check; it does not
    silently rewrite it to shell_ok / py_compile. Evaluation stays 'is JSON?'."""
    plan = Planner(_plan_llm(JSON_VALID_ON_PY_PLAN), str(tmp_path)).plan(
        Objective.new("Implement word_counter.py and write result.json"))
    assert plan["source"] == "llm"
    kinds = [(c.kind, c.args.get("path")) for t in plan["graph"].tasks.values() for c in t.checks]
    assert ("json_valid", "word_counter.py") in kinds
    kept = _checks([{
        "kind": "json_valid",
        "args": {"path": "word_counter.py"},
        "description": "word_counter.py is a valid Python file",
    }])
    assert len(kept) == 1
    assert kept[0].kind == "json_valid"
    assert kept[0].args["path"] == "word_counter.py"


def test_scenario_b_scripted_json_valid_on_py_repair_is_not_environment(home, tmp_path):
    """Write valid Python under an LLM json_valid-on-py check.

    Verification FAILS (not JSON). Recovery is VALIDATION coding repair,
    not ENVIRONMENT / Repair prerequisite.
    """
    ws = tmp_path / "ws_b_e2e"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [
        ([("write_file", {"path": "word_counter.py", "content": VALID_PY}),
          ("write_file", {"path": "result.json", "content": '{"words": 2}'})],
         "DONE: wrote python"),
        ([("write_file", {"path": "word_counter.py", "content": VALID_PY})],
         "DONE: repaired"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, JSON_VALID_ON_PY_PLAN)
    obj = ctl.run(ctl.create(
        "Implement word_counter.py and write result.json.",
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert decisions, "expected a recovery after json_valid-on-py failed"
    assert decisions[0]["failure_class"] == FailureClass.VALIDATION
    assert decisions[0]["failure_class"] != FailureClass.ENVIRONMENT
    assert decisions[0]["strategy"] == "repair"
    g = ctl.load_graph(obj)
    texts = [t.text for t in g.tasks.values()]
    assert any(t.startswith("Repair so that machine checks pass") for t in texts)
    assert not any(t.startswith("Repair prerequisite") for t in texts)
    # Honest: json_valid-on-py cannot become VERIFIED from valid Python.
    py_tasks = [t for t in g.tasks.values() if any(
        c.kind == "json_valid" and str(c.args.get("path", "")).endswith(".py") for c in t.checks
    )]
    assert py_tasks
    # Honest evaluation: valid Python never satisfies json_valid. That is not a
    # rubber-stamp (false DONE 0). Remapping the check would be a new product
    # rule, not the current contract.
    assert all((t.verification or {}).get("status") != "VERIFIED" for t in py_tasks)


# ---------------------------------------------------------------- Scenario C — inferred checks

def test_scenario_c_inferred_checks_json_valid_only_on_json_not_py():
    checks = infer_coding_checks(RW065_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["result.json"]
    assert not any(str(p).endswith(".py") for p in json_paths)
    assert any(c.kind == "shell_ok" and "test_word_counter.py" in str(c.args.get("command", ""))
               for c in checks)


def test_scenario_c_fallback_objective_checks_match_infer(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW065_GOAL))
    assert res["source"] == "fallback"
    json_paths = [c.args.get("path") for c in res["objective_checks"] if c.kind == "json_valid"]
    assert json_paths == ["result.json"]
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- live RW-065 ENVIRONMENT reconstruction

def test_rw065_env_class_is_no_such_file_shell_errors_not_json_valid_kind():
    """Live RW-065: actions errors from shell before files existed.

    classify() reads observation text, not check kinds. json_valid-on-py in
    the verification payload does not drive ENVIRONMENT (F-26). Historically
    CPython `can't open file 'test_*.py'` matched _ENV (F-18 path). v0.4.5
    reclassifies that premature script invoke as TOOL (RW-079 / F-42); the
    json_valid fail still yields coding repair, not Repair-prerequisite.
    """
    t = Task.new("o", "Create word_counter.py with word counting function")
    t.attempts = 1
    ob = _ob(
        t,
        "python3: can't open file 'test_word_counter.py': "
        "[Errno 2] No such file or directory\n[exit=2]",
    )
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "8 actions, 3 errors"},
        {"ok": False, "kind": "json_valid",
         "detail": "word_counter.py invalid JSON: Expecting value"},
    ]}
    assert classify(t, [ob], verification=ver) != FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(t, [ob], verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy == "repair"
    assert d.data.get("coding_repair") is True


def test_json_valid_on_py_without_env_token_does_not_match_rw065_live_class():
    """Counterfactual: drop the shell no-such-file observations.

    Then json_valid-on-py is VALIDATION, not the live ENVIRONMENT_FAILURE row.
    """
    t = Task.new("o", "Create word_counter.py")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "json_valid", "detail": "word_counter.py invalid JSON"},
    ]}
    assert classify(t, [], verification=ver) == FailureClass.VALIDATION
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.data.get("coding_repair") is True
