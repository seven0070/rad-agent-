"""Budget management — the control plane's hard limits.

An objective can never run away: every autonomous loop charges a budget and the
`BudgetManager` is the single place that decides whether work may continue.

Budgets (all optional; 0 = unlimited):
    tool_calls   number of tool executions
    model_calls  number of model round-trips
    retries      recovery attempts across the whole objective
    seconds      wall-clock time across resumes
    money_usd    paid provider spend
    tokens       prompt+completion tokens spent by models
    agents       number of sub-agent runs spawned

Charging is idempotent-ish and cheap; state lives on the Objective (`usage`) so
it survives crashes and resumes. When a budget crosses the warn threshold the
manager emits a warning event once per kind, so a human can intervene *before*
the hard stop.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

KINDS = ("tool_calls", "model_calls", "retries", "seconds", "money_usd", "tokens", "agents")
LABELS = {"tool_calls": "tool-call", "model_calls": "model-call", "retries": "retry",
          "seconds": "time", "money_usd": "money", "tokens": "token", "agents": "agent"}
WARN_AT = 0.8


class BudgetExceeded(Exception):
    """Raised (or returned as a reason) when an objective may not continue."""

    def __init__(self, reason: str, kind: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.kind = kind


class TaskYield(Exception):
    """Stop this in-flight task so leftover tool budget can reach later READY work.

    Distinct from ``BudgetExceeded``: the objective is not out of tools. The
    current task is checkpointed and the drive loop dispatches independent
    READY work under the same cap (Gen3 theme 3 slice E1).
    """

    def __init__(self, reason: str = "yield leftover-budget") -> None:
        super().__init__(reason)
        self.reason = reason
        self.kind = "tool_calls"


@dataclass
class BudgetSnapshot:
    account: Dict[str, Dict[str, float]]
    warnings: Dict[str, str]
    exceeded: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"account": self.account, "warnings": dict(self.warnings), "exceeded": self.exceeded}

    def render(self) -> str:
        parts = []
        for k, v in self.account.items():
            limit = v.get("limit") or 0
            used = v.get("used") or 0
            if limit:
                parts.append(f"{k} {used:g}/{limit:g}")
            elif used:
                parts.append(f"{k} {used:g}")
        return "  ".join(parts)


class BudgetManager:
    """Enforces an objective's budget. One instance per objective run."""

    def __init__(self, budget: Any, usage: Any, *,
                 events: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                 objective_id: str = "", deadline: Optional[float] = None,
                 clock: Callable[[], float] = time.time) -> None:
        self.budget = budget
        self.usage = usage
        self.events = events
        self.objective_id = objective_id
        self.deadline = deadline
        self.clock = clock
        self._warned: Dict[str, str] = {}
        self._started = clock()

    # ------------------------------------------------------------------ limits
    def limit(self, kind: str) -> float:
        return float(getattr(self.budget, kind, 0) or 0)

    def used(self, kind: str) -> float:
        if kind == "seconds":
            return max(float(getattr(self.usage, "seconds", 0) or 0), self.elapsed())
        return float(getattr(self.usage, kind, 0) or 0)

    def elapsed(self) -> float:
        return max(0.0, self.clock() - self._started)

    def remaining(self, kind: str) -> float:
        lim = self.limit(kind)
        return max(0.0, lim - self.used(kind)) if lim else float("inf")

    # ------------------------------------------------------------------ checks
    def check(self) -> Optional[BudgetExceeded]:
        """The first exhausted budget, or None. Never charges anything."""
        for kind in KINDS:
            lim = self.limit(kind)
            if lim and self.used(kind) >= lim:
                return BudgetExceeded(f"{LABELS.get(kind, kind)} budget {lim:g} exhausted", kind)
        if self.deadline and self.clock() > self.deadline:
            return BudgetExceeded("deadline passed", "seconds")
        return None

    def exceeded_reason(self) -> Optional[str]:
        ex = self.check()
        return ex.reason if ex else None

    def raise_if_exceeded(self) -> None:
        ex = self.check()
        if ex:
            raise ex

    # ------------------------------------------------------------------ charging
    def charge(self, kind: str, n: float = 1) -> None:
        if kind not in KINDS:
            raise ValueError(f"unknown budget kind {kind!r}")
        if kind == "seconds":
            return
        setattr(self.usage, kind, float(getattr(self.usage, kind, 0) or 0) + float(n))
        self._maybe_warn(kind)

    def charge_tool(self, n: int = 1) -> None:
        self.charge("tool_calls", n)

    def charge_retry(self, n: int = 1) -> None:
        self.charge("retries", n)

    def charge_agent(self, n: int = 1) -> None:
        self.charge("agents", n)

    def charge_model(self, tokens: int = 0, money: float = 0.0, calls: int = 1) -> None:
        self.charge("model_calls", calls)
        if tokens:
            self.charge("tokens", tokens)
        if money:
            self.usage.money_usd = float(getattr(self.usage, "money_usd", 0.0) or 0.0) + float(money)
            self._maybe_warn("money_usd")

    def tick(self, elapsed: Optional[float] = None) -> None:
        """Advance the cumulative wall-clock account (call once per driver loop)."""
        total = self.elapsed() if elapsed is None else elapsed
        self.usage.seconds = max(float(getattr(self.usage, "seconds", 0) or 0), total)
        self._maybe_warn("seconds")

    # ------------------------------------------------------------------ reporting
    def _maybe_warn(self, kind: str) -> None:
        lim = self.limit(kind)
        if not lim or not self.events:
            return
        frac = self.used(kind) / lim if lim else 0
        if frac >= WARN_AT and kind not in self._warned:
            self._warned[kind] = f"{kind} at {frac * 100:.0f}% of {lim:g}"
            try:
                self.events("BUDGET_WARNING", {"budget": kind, "used": self.used(kind), "limit": lim})
            except Exception:
                pass

    def snapshot(self) -> BudgetSnapshot:
        account: Dict[str, Dict[str, float]] = {}
        for kind in KINDS:
            lim = self.limit(kind)
            used = self.used(kind)
            if lim or used:
                account[kind] = {"limit": lim, "used": round(used, 4),
                                 "remaining": round(self.remaining(kind), 4) if lim else -1.0}
        ex = self.check()
        return BudgetSnapshot(account=account, warnings=dict(self._warned), exceeded=ex.reason if ex else None)

    def to_dict(self) -> Dict[str, Any]:
        return {"objective_id": self.objective_id, **self.snapshot().to_dict()}

    @staticmethod
    def estimate_cost(usage: Dict[str, Any], prices: Optional[List[float]] = None) -> float:
        """USD for a model response's usage dict ({'in': n, 'out': m}) given per-1k prices."""
        if not prices or len(prices) < 2:
            return 0.0
        tin = float((usage or {}).get("in", 0) or 0)
        tout = float((usage or {}).get("out", 0) or 0)
        return round(tin / 1000.0 * prices[0] + tout / 1000.0 * prices[1], 6)
