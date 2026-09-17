"""Agent Control Plane — RAD owns the state; the LLM is the intelligence component.

    Objective  →  TaskGraph  →  Scheduler  →  Executor  →  Observer  →  Verifier
                                    ▲                                        │
                                    └──────────── Recovery ◄─────────────────┘

Everything here is explicit, machine-readable, persisted under
``~/.rad/objectives/<id>/`` and replayable from the event log.
"""
from rad.control.objectives import Objective, ObjectiveStatus, ObjectiveStore
from rad.control.tasks import Task, TaskStatus, Check
from rad.control.graph import TaskGraph
from rad.control.events import EventLog, Event
from rad.control.controller import Controller

__all__ = ["Objective", "ObjectiveStatus", "ObjectiveStore", "Task", "TaskStatus", "Check",
           "TaskGraph", "EventLog", "Event", "Controller"]
