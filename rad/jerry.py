"""Jerry — operator / persona / interface layer (foundation only).

    User → Jerry → RAD Session / Objective → Existing Control Plane
         → Executor → Policy.decide → Tools

Jerry may converse, read authority state, propose objectives through the
Controller, and explain policy decisions. Jerry must NOT execute tools,
bypass Policy.decide, bypass the Executor, or own a private runner / verifier
/ memory / control plane.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from rad.authority import Authority
from rad.home import RadHome
from rad.policy import Policy

# Jerry is not a tool path. These names must never appear as callable surfaces.
_FORBIDDEN = ("run_tool", "execute_tool", "call_tool", "_run_tool", "tool_runner")


class Jerry:
    """Thin operator. All side effects go through Session or Controller."""

    def __init__(self, home: RadHome, *,
                 session_factory: Optional[Callable[..., Any]] = None,
                 controller_factory: Optional[Callable[[RadHome], Any]] = None) -> None:
        self.home = home
        self._session_factory = session_factory
        self._controller_factory = controller_factory

    def authority_state(self) -> Dict[str, Any]:
        return Authority(self.home).snapshot()

    def explain_decision(self, capability: str, resource: str, *,
                         auto: bool = False, path: Optional[str] = None) -> Dict[str, Any]:
        from pathlib import Path
        pol = Policy(self.home)
        d = pol.decide(capability, resource, auto=auto,
                       path=Path(path) if path else None)
        snap = Authority(self.home).snapshot()
        return {
            "effect": d.effect,
            "reason": d.reason,
            "by": d.by,
            "limits": d.limits,
            "denied": d.denied,
            "profile": snap["profile"],
            "confirmation": snap["confirmation"],
            "note": "Jerry explains Policy.decide; it does not override it.",
        }

    def chat(self, text: str, *, auto: bool = False) -> str:
        """One brain turn through Session. Tools still hit Policy.decide / run_tool."""
        text = (text or "").strip()
        if not text:
            raise ValueError("text required")
        if self._session_factory is not None:
            s = self._session_factory(self.home, auto=auto)
        else:
            from rad.session import Session
            s = Session(self.home, auto=auto)
        try:
            return s.think(text)
        finally:
            try:
                s.close()
            except Exception:
                pass

    def propose_objective(self, goal: str, *,
                          criteria: Optional[list] = None,
                          constraints: Optional[list] = None,
                          run: bool = False) -> Dict[str, Any]:
        """Create an objective on the existing control plane. Does not run tools."""
        goal = (goal or "").strip()
        if not goal:
            raise ValueError("goal required")
        if self._controller_factory is not None:
            ctl = self._controller_factory(self.home)
        else:
            from rad.control.controller import Controller
            ctl = Controller(self.home, quiet=True)
        obj = ctl.create(goal, success_criteria=list(criteria or []),
                         constraints=list(constraints or []))
        started = False
        if run:
            # Controller.run is the only drive loop. Jerry does not execute.
            from rad.authority import confirmation_is_automatic
            if self.home.cfg.get("auto") or confirmation_is_automatic(self.home):
                ctl.run(obj)
                started = True
        return {"id": obj.id, "goal": obj.goal, "status": obj.status, "started": started}

    def __getattr__(self, name: str) -> Any:
        if name in _FORBIDDEN:
            raise AttributeError(
                f"Jerry has no {name}: tools run only through the executor / Policy.decide")
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")
