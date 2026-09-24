"""Agent Control Plane — RAD owns the state; the LLM is the intelligence component.

    Objective  →  TaskGraph  →  Scheduler  →  Executor  →  Observer  →  Verifier
                                    ▲                                        │
                                    └──────────── Recovery ◄─────────────────┘

Everything here is explicit, machine-readable, persisted under
``~/.rad/objectives/<id>/`` and replayable from the event log.

Heavy symbols (Controller, EventLog, …) load on first attribute access so
``import rad.control`` / ``from rad.control.cli import add_parsers`` stay cheap.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rad.control.controller import Controller
    from rad.control.events import Event, EventLog
    from rad.control.graph import TaskGraph
    from rad.control.objectives import Objective, ObjectiveStatus, ObjectiveStore
    from rad.control.tasks import Check, Task, TaskStatus

__all__ = ["Objective", "ObjectiveStatus", "ObjectiveStore", "Task", "TaskStatus", "Check",
           "TaskGraph", "EventLog", "Event", "Controller"]

_EXPORTS = {
    "Objective": "rad.control.objectives",
    "ObjectiveStatus": "rad.control.objectives",
    "ObjectiveStore": "rad.control.objectives",
    "Task": "rad.control.tasks",
    "TaskStatus": "rad.control.tasks",
    "Check": "rad.control.tasks",
    "TaskGraph": "rad.control.graph",
    "EventLog": "rad.control.events",
    "Event": "rad.control.events",
    "Controller": "rad.control.controller",
}


def __getattr__(name: str):
    mod = _EXPORTS.get(name)
    if mod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib
    val = getattr(importlib.import_module(mod), name)
    globals()[name] = val
    return val


def __dir__():
    return sorted(set(globals()) | set(__all__))
