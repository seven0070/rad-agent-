"""Recovery engine — classify a failure, pick a bounded strategy.

Failure classes:  TRANSIENT · TOOL_FAILURE · NETWORK_FAILURE · AUTH_FAILURE ·
                  PERMISSION_FAILURE · PLANNING_FAILURE · MODEL_FAILURE ·
                  VALIDATION_FAILURE · ENVIRONMENT_FAILURE · BUDGET · UNKNOWN
Strategies:       retry · retry_with_hint · switch_tool · switch_model · repair ·
                  rollback · replan · spawn_specialist · ask_user · abort

Policy is deterministic and testable; the LLM is only consulted to *write*
a repair step, never to decide whether to keep looping.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rad.control.codingloop import (
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_pip_requirements_file_missing,
    looks_like_broken_artifact,
    repair_hint,
)
from rad.control.observer import Observation
from rad.control.tasks import Task


class FailureClass:
    TRANSIENT = "TRANSIENT"
    TOOL = "TOOL_FAILURE"
    NETWORK = "NETWORK_FAILURE"
    AUTH = "AUTH_FAILURE"
    PERMISSION = "PERMISSION_FAILURE"
    PLANNING = "PLANNING_FAILURE"
    MODEL = "MODEL_FAILURE"
    VALIDATION = "VALIDATION_FAILURE"
    ENVIRONMENT = "ENVIRONMENT_FAILURE"
    BUDGET = "BUDGET"
    UNKNOWN = "UNKNOWN"


STRATEGIES = ("retry", "retry_with_hint", "switch_tool", "switch_model", "repair", "rollback",
              "replan", "spawn_specialist", "ask_user", "abort")


@dataclass
class Decision:
    strategy: str                    # one of STRATEGIES
    failure_class: str
    reason: str
    hint: str = ""                   # appended to the next prompt for retry_with_hint / repair
    data: Dict[str, Any] = field(default_factory=dict)


_NET = re.compile(r"network:|timed? ?out|connection (reset|refused)|temporar|HTTP 5\d\d|HTTP 429|rate limit", re.I)
_AUTH = re.compile(r"HTTP 401|HTTP 403|unauthori[sz]ed|invalid api key|forbidden", re.I)
_PERM = re.compile(r"blocked by safety policy|user declined|permission denied|outside the workspace", re.I)
_ENV = re.compile(r"command not found|: not found|no such file|not installed|ModuleNotFoundError|No module named|ENOENT", re.I)
_ALREADY_EXISTS = re.compile(r"already exists|FileExistsError|\bFile exists\b", re.I)
_MODEL = re.compile(r"all providers failed|no brain available|brain error|no model selected", re.I)


def classify(task: Task, observations: List[Observation], error: str = "",
             verification: Optional[Dict[str, Any]] = None) -> str:
    text = " ".join([error] + [o.output[-400:] for o in observations if o.status != "success"])
    if error and _MODEL.search(error):
        return FailureClass.MODEL
    if _AUTH.search(text):
        return FailureClass.AUTH
    if _PERM.search(text):
        return FailureClass.PERMISSION
    if _NET.search(text):
        return FailureClass.NETWORK if "network" in text.lower() or "connection" in text.lower() else FailureClass.TRANSIENT
    # mkdir / create "already exists" is not a missing environment (RW-071). Mixed
    # "File exists" + "no such file" check noise must not insert Repair prerequisite.
    # pip -r missing requirements.txt is not a missing env dependency (RW-075).
    if (_ENV.search(text) and not _ALREADY_EXISTS.search(text)
            and not _pip_requirements_missing(observations, text)):
        return FailureClass.ENVIRONMENT
    if any(o.status == "error" for o in observations):
        return FailureClass.TOOL          # a concrete tool error is more specific than "checks failed"
    if verification and verification.get("status") == "FAILED":
        return FailureClass.VALIDATION
    if verification and verification.get("status") == "UNVERIFIED":
        return FailureClass.VALIDATION
    if error:
        return FailureClass.UNKNOWN
    return FailureClass.PLANNING


class RecoveryEngine:
    def __init__(self, max_task_attempts: int = 3, max_repairs_per_task: int = 1) -> None:
        self.max_task_attempts = max_task_attempts
        self.max_repairs = max_repairs_per_task

    def decide(self, task: Task, observations: List[Observation], error: str = "",
               verification: Optional[Dict[str, Any]] = None, repairs_so_far: int = 0,
               retries_left: int = 99, artifacts: Optional[Dict[str, Dict[str, Any]]] = None) -> Decision:
        fc = classify(task, observations, error, verification)
        can_retry = task.can_retry and retries_left > 0
        failed_checks = [r for r in (verification or {}).get("results", []) if not r.get("ok")]
        detail = "; ".join(r.get("detail", "")[:100] for r in failed_checks)[:600]
        broken_verified = self._broken_verified(failed_checks, artifacts or {})

        if fc == FailureClass.AUTH:
            return Decision("ask_user", fc, "credentials rejected — a human must fix keys")
        if fc == FailureClass.PERMISSION:
            blocked = [o.output[:200] for o in observations if o.status in ("blocked", "declined")]
            if can_retry:
                # a refusal must never be retried blind: the hint names the refusal and demands
                # a permitted alternative. Repeated refusal exhausts the retry budget → ask_user.
                return Decision("retry_with_hint", fc,
                                "an action was blocked by policy — retrying with an explicit alternative",
                                hint=("A previous action was refused by RAD's security layer: "
                                      + " | ".join(blocked[:2])[:300]
                                      + " Do not repeat it. Reach the goal with a permitted approach: "
                                        "stay inside the workspace, never touch credentials, "
                                        "never run privileged or destructive commands."),
                                data={"blocked": blocked})
            return Decision("ask_user", fc, "an action was blocked or declined by policy",
                            data={"blocked": blocked})
        if fc == FailureClass.MODEL:
            if "no brain available" in (error or ""):
                return Decision("ask_user", fc, "no brain available — add a key or start a local engine")
            if can_retry:
                failed = _failed_providers(error or "", observations)
                return Decision("retry", fc, "model/provider failure — retry on another brain",
                                data={"switch_model": True, "avoid": failed})
            if repairs_so_far < self.max_repairs:
                return Decision("replan", fc, "provider kept failing — replan around it")
            return Decision("abort", fc, "no working brain after retries")
        if fc in (FailureClass.TRANSIENT, FailureClass.NETWORK):
            if can_retry:
                return Decision("retry", fc, "transient/network failure — retry")
            return Decision("abort", fc, "transient failure persisted past retry budget")
        if broken_verified and can_retry:
            return Decision("rollback", fc,
                            f"{broken_verified} was verified earlier and is now broken — restore it",
                            hint=f"the previous version of {broken_verified} was verified; "
                                 f"the current one fails: {detail[:200]}",
                            data={"path": broken_verified})
        if fc == FailureClass.ENVIRONMENT:
            if repairs_so_far < self.max_repairs:
                return Decision("repair", fc, "missing dependency/file — insert a repair step",
                                hint="A prerequisite was missing: " + detail[:300])
            if can_retry:
                return Decision("retry_with_hint", fc, "environment still broken — retry with hint",
                                hint="Previous attempt failed because the environment was missing something. "
                                     "Install/create the prerequisite first, then do the step.")
            return Decision("ask_user", fc, "environment problem persists")
        if (fc in (FailureClass.VALIDATION, FailureClass.TOOL, FailureClass.UNKNOWN)
                and looks_like_broken_artifact(failed_checks)
                and repairs_so_far < self.max_repairs
                and not _is_repair_task(task)):
            # Coding/verification loop: invalid JSON or failing tests get a repair
            # step with the concrete failure, not an unstructured retry (RW-058/062).
            # Missing-file lies (file_exists) still use retry_with_hint below.
            # Repair tasks themselves retry/ask_user — they do not spawn repair-of-repair.
            return Decision("repair", fc,
                            "machine checks failed on produced artifacts — insert a repair step",
                            hint=repair_hint(failed_checks),
                            data={"coding_repair": True,
                                  "failed_checks": [r.get("kind") for r in failed_checks]})
        if fc == FailureClass.TOOL and can_retry and task.attempts >= 2:
            bad_tool = _dominant_failing_tool(observations)
            if bad_tool and not is_done_protocol_tool(bad_tool):
                return Decision("switch_tool", fc, f"{bad_tool} keeps failing — try another way",
                                hint=f"the tool '{bad_tool}' failed twice (last: {detail[:200] or 'tool error'}). "
                                     f"Use a different tool or fix the precondition before calling it again.")
        if fc in (FailureClass.VALIDATION, FailureClass.TOOL, FailureClass.UNKNOWN, FailureClass.PLANNING):
            if can_retry:
                hint = ("Your previous attempt did NOT pass verification. Failed checks: "
                        + (detail or "no evidence of completion was produced")
                        + ". Fix the actual outcome (files/commands), don't just restate that it is done."
                        + _thrash_hint(observations))
                return Decision("retry_with_hint", fc, "verification failed — retry with explicit feedback", hint=hint)
            if repairs_so_far < self.max_repairs:
                return Decision("replan", fc, "attempts exhausted — replan remaining work",
                                hint="Approach so far failed verification: " + detail[:300])
            return Decision("ask_user", fc, "could not satisfy verification after retries and replan")
        return Decision("abort", fc, "unrecoverable")

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _broken_verified(failed_checks: List[Dict[str, Any]],
                         artifacts: Dict[str, Dict[str, Any]]) -> str:
        """Name a file that was VERIFIED earlier and now fails a check (→ rollback candidate)."""
        verified: Dict[str, Dict[str, Any]] = {}
        for a in artifacts.values():
            if a.get("verification", {}).get("ok") and a.get("type") == "file":
                verified[a.get("location", "")] = a
        for r in failed_checks:
            args = r.get("args") or {}
            path = str(args.get("path", ""))
            if not path:
                continue
            for loc, a in verified.items():
                if loc.endswith("/" + path) or loc == path:
                    return path
        return ""


def _is_repair_task(task: Task) -> bool:
    text = task.text or ""
    return text.startswith("Repair so that") or text.startswith("Repair prerequisite")


def _pip_requirements_missing(observations: List[Observation], text: str) -> bool:
    if is_pip_requirements_file_missing(text, ""):
        return True
    for o in observations:
        if o.status == "success":
            continue
        cmd = str((o.args or {}).get("command", ""))
        if is_pip_requirements_file_missing(o.output or "", cmd):
            return True
    return False


def _thrash_hint(observations: List[Observation]) -> str:
    bits: List[str] = []
    if any(is_done_protocol_tool(o.tool) for o in observations if o.status == "error"):
        bits.append("DONE is not a tool. Do not call a tool named DONE or DONE: …. "
                    "Write remaining files, then put DONE: in your reply text.")
    if any(is_pip_requirements_file_missing(o.output or "", str((o.args or {}).get("command", "")))
           for o in observations if o.status != "success"):
        bits.append("Do not pip install -r a missing requirements.txt for stdlib-only coding. "
                    "Use the workspace files; do not invent a requirements file.")
    if any(is_mkdir_already_exists(o.output or "", str((o.args or {}).get("command", "")))
           for o in observations if o.status != "success"):
        bits.append("Do not mkdir a directory that write_file already created. "
                    "write_file creates parent directories. Continue writing remaining files.")
    return (" " + " ".join(bits)) if bits else ""


def _failed_providers(error: str, observations: List[Observation]) -> List[str]:
    names = set(re.findall(r"([a-z0-9_.-]{3,20}):\s*(?:HTTP|error|rate|timeout|all providers)", error or "", re.I))
    for o in observations:
        if o.status != "success":
            names |= set(re.findall(r"([a-z0-9_.-]{3,20}):\s*(?:HTTP|error|timed out)", o.output[-300:], re.I))
    return sorted(n for n in names if n not in ("tool", "python"))


def _dominant_failing_tool(observations: List[Observation]) -> str:
    counts: Dict[str, int] = {}
    for o in observations:
        if o.status == "error":
            counts[o.tool] = counts.get(o.tool, 0) + 1
    if not counts:
        return ""
    tool, n = max(counts.items(), key=lambda kv: kv[1])
    return tool if n >= 2 else ""
