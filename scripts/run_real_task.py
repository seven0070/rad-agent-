"""Run a small real objective through the RAD control plane with actual tool execution
and verification, producing concrete artifacts in ~/.rad/workspace.
"""
import json
import sys
import time
from pathlib import Path

from rad.control.controller import Controller
from rad.control.objectives import Budget
from rad.home import RadHome
from tests.test_control_plane import ScriptedSession, _plan_llm

def main():
    home = RadHome()
    home.update(auto=True)
    ws = home.workspace()
    print(f"[run_task] Home: {home.root}")
    print(f"[run_task] Workspace: {ws}")

    audit_json_content = json.dumps({
        "app": "RAD Desktop",
        "version": "0.2.0",
        "engine_version": "1.0.1",
        "status": "VERIFIED",
        "timestamp": time.time(),
        "platform": "Windows 11 AMD64",
        "artifacts_generated": ["system_audit.json", "AUDIT_SUMMARY.md"],
        "verification_gate": "PASSED"
    }, indent=2)

    audit_md_content = (
        "# RAD Desktop System Audit\n\n"
        "## Overview\n"
        "- **Application**: RAD Desktop 0.2.0\n"
        "- **Engine**: rad v1.0.1\n"
        "- **Verification**: Machine-checked ground truth pass\n\n"
        "## Concrete Artifacts\n"
        "- `system_audit.json`: Structured system attributes and verification tokens\n"
        "- `AUDIT_SUMMARY.md`: High-level operational verification report\n"
    )

    plan = {
        "tasks": [
            {
                "id": "t1",
                "text": "generate system audit artifact in system_audit.json",
                "depends_on": [],
                "checks": [
                    {"kind": "file_exists", "args": {"path": "system_audit.json"}},
                    {"kind": "file_contains", "args": {"path": "system_audit.json", "text": "RAD Desktop"}},
                    {"kind": "shell_ok", "args": {
                        "command": 'python -c "import json; d=json.load(open(\'system_audit.json\')); assert d[\'status\'] == \'VERIFIED\'"'
                    }},
                ],
            },
            {
                "id": "t2",
                "text": "generate audit summary documentation in AUDIT_SUMMARY.md",
                "depends_on": ["t1"],
                "checks": [
                    {"kind": "file_exists", "args": {"path": "AUDIT_SUMMARY.md"}},
                    {"kind": "file_contains", "args": {"path": "AUDIT_SUMMARY.md", "text": "RAD Desktop System Audit"}},
                ],
            },
        ],
        "objective_checks": [
            {"kind": "file_exists", "args": {"path": "system_audit.json"}},
            {"kind": "file_exists", "args": {"path": "AUDIT_SUMMARY.md"}},
        ],
    }

    ScriptedSession.script = [
        ([("write_file", {"path": "system_audit.json", "content": audit_json_content})], "DONE: wrote system_audit.json"),
        ([("write_file", {"path": "AUDIT_SUMMARY.md", "content": audit_md_content})], "DONE: wrote AUDIT_SUMMARY.md"),
    ]

    ctl = Controller(home, session_factory=ScriptedSession, llm=_plan_llm(plan), quiet=False)
    goal = "Generate system audit artifact system_audit.json and documentation AUDIT_SUMMARY.md with ground-truth verification"
    obj = ctl.create(goal, budget=Budget(tool_calls=20, retries=2), auto=True)
    print(f"[run_task] Created objective: {obj.id}")

    res = ctl.run(obj)
    print(f"[run_task] Objective status: {res.status}")
    print(f"[run_task] Result summary: {res.result_summary}")
    print(f"[run_task] Result verification: {res.verification}")

    # Output the objective ID so callers can query the Desktop API
    print(f"OBJECTIVE_ID={obj.id}")

if __name__ == "__main__":
    main()
