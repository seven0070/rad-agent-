"""Recovery engine — classify a failure, pick a bounded strategy.

Failure classes:  TRANSIENT · TOOL_FAILURE · NETWORK_FAILURE · AUTH_FAILURE ·
                  PERMISSION_FAILURE · PLANNING_FAILURE · MODEL_FAILURE ·
                  VALIDATION_FAILURE · ENVIRONMENT_FAILURE · BUDGET · UNKNOWN
Strategies:       retry · retry_with_hint · repair · replan · ask_user · abort

Policy is deterministic and testable; the LLM is only consulted to *write*
a repair step, never to decide whether to keep looping.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


@dataclass
class Decision:
    strategy: str                    # retry | retry_with_hint | repair | replan | ask_user | abort
    failure_class: str
    reason: str
    hint: str = ""                   # appended to the next prompt for retry_with_hint / repair
    data: Dict[str, Any] = field(default_factory=dict)


_NET = re.compile(r"network:|timed? ?out|connection (reset|refused)|temporar|HTTP 5\d\d|HTTP 429|rate limit", re.I)
_AUTH = re.compile(r"HTTP 401|HTTP 403|unauthori[sz]ed|invalid api key|forbidden", re.I)
_PERM = re.compile(r"blocked by safety policy|user declined|permission denied|outside the workspace", re.I)
_ENV = re.compile(r"command not found|: not found|no such file|not installed|ModuleNotFoundError|No module named|ENOENT", re.I)
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
    if _ENV.search(text):
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
               retries_left: int = 99) -> Decision:
        fc = classify(task, observations, error, verification)
        can_retry = task.can_retry and retries_left > 0
        failed_checks = [r for r in (verification or {}).get("results", []) if not r.get("ok")]
        detail = "; ".join(r.get("detail", "")[:100] for r in failed_checks)[:600]

        if fc == FailureClass.AUTH:
            return Decision("ask_user", fc, "credentials rejected — a human must fix keys")
        if fc == FailureClass.PERMISSION:
            return Decision("ask_user", fc, "an action was blocked or declined by policy",
                            data={"blocked": [o.output[:200] for o in observations if o.status in ("blocked", "declined")]})
        if fc == FailureClass.MODEL:
            if "no brain available" in (error or ""):
                return Decision("ask_user", fc, "no brain available — add a key or start a local engine")
            if can_retry:
                return Decision("retry", fc, "model/provider failure — retry (router will fall back)")
            return Decision("abort", fc, "no working brain after retries")
        if fc in (FailureClass.TRANSIENT, FailureClass.NETWORK):
            if can_retry:
                return Decision("retry", fc, "transient/network failure — retry")
            return Decision("abort", fc, "transient failure persisted past retry budget")
        if fc == FailureClass.ENVIRONMENT:
            if repairs_so_far < self.max_repairs:
                return Decision("repair", fc, "missing dependency/file — insert a repair step",
                                hint="A prerequisite was missing: " + detail[:300])
            if can_retry:
                return Decision("retry_with_hint", fc, "environment still broken — retry with hint",
                                hint="Previous attempt failed because the environment was missing something. "
                                     "Install/create the prerequisite first, then do the step.")
            return Decision("ask_user", fc, "environment problem persists")
        if fc in (FailureClass.VALIDATION, FailureClass.TOOL, FailureClass.UNKNOWN, FailureClass.PLANNING):
            if can_retry:
                hint = ("Your previous attempt did NOT pass verification. Failed checks: "
                        + (detail or "no evidence of completion was produced")
                        + ". Fix the actual outcome (files/commands), don't just restate that it is done.")
                return Decision("retry_with_hint", fc, "verification failed — retry with explicit feedback", hint=hint)
            if repairs_so_far < self.max_repairs:
                return Decision("replan", fc, "attempts exhausted — replan remaining work",
                                hint="Approach so far failed verification: " + detail[:300])
            return Decision("ask_user", fc, "could not satisfy verification after retries and replan")
        return Decision("abort", fc, "unrecoverable")
