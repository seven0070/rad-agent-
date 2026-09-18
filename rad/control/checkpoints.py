"""Checkpoint manager — objectives survive crashes, restarts and provider failures.

Every state transition writes an atomic checkpoint:

    ~/.rad/objectives/<id>/objective.json    goal, criteria, budget, usage, status
    ~/.rad/objectives/<id>/tasks.json        the full task graph
    ~/.rad/objectives/<id>/checkpoint.json   seq, digest, status, task/usage summary
    ~/.rad/objectives/<id>/checkpoints/      rotating snapshots (rollback points)
    ~/.rad/objectives/<id>/lock.json         live run lock (pid + started)

On restart, `CheckpointManager.interrupted()` finds objectives that were mid-run
whose lock is dead (process gone), and `restore()` puts every in-flight task back
into a runnable state (`RETRYING`) and records that the run resumed after an
interruption — so `rad objective resume <id>` continues where it stopped instead
of silently forgetting work.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome, _write_json

from rad.control.graph import TaskGraph
from rad.control.objectives import Objective, ObjectiveStatus, ObjectiveStore
from rad.control.tasks import TaskStatus

INTERRUPTED_STATUSES = (ObjectiveStatus.PLANNING, ObjectiveStatus.RUNNING)
IN_FLIGHT = (TaskStatus.RUNNING, TaskStatus.OBSERVING, TaskStatus.VERIFYING)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@dataclass
class Interrupted:
    objective_id: str
    goal: str
    status: str
    tasks: Dict[str, int]
    lock_pid: int
    lock_host: str
    at: float

    def to_dict(self) -> Dict[str, Any]:
        return {"objective_id": self.objective_id, "goal": self.goal, "status": self.status,
                "tasks": self.tasks, "lock_pid": self.lock_pid, "lock_host": self.lock_host, "at": self.at}


class CheckpointManager:
    def __init__(self, home: RadHome, store: Optional[ObjectiveStore] = None, keep: int = 5) -> None:
        self.home = home
        self.store = store or ObjectiveStore(home)
        self.keep = keep

    # ------------------------------------------------------------------ paths
    def dir(self, oid: str) -> Path:
        return self.store.dir(oid)

    def cp_path(self, oid: str) -> Path:
        return self.dir(oid) / "checkpoint.json"

    def lock_path(self, oid: str) -> Path:
        return self.dir(oid) / "lock.json"

    # ------------------------------------------------------------------ save
    def save(self, obj: Objective, graph: TaskGraph, note: str = "") -> Dict[str, Any]:
        """Atomically persist objective + graph + checkpoint metadata."""
        self.store.save(obj)
        payload = graph.to_list()
        self.store.save_tasks(obj.id, payload)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
        prev = self.read_cp(obj.id)
        cp = {
            "objective_id": obj.id,
            "seq": int(prev.get("seq", 0)) + 1,
            "at": time.time(),
            "status": obj.status,
            "note": note[:300],
            "digest": digest,
            "tasks": graph.summary(),
            "usage": obj.usage.to_dict(),
            "budget": obj.budget.to_dict(),
        }
        _write_json(self.cp_path(obj.id), cp)
        if cp["seq"] % 5 == 0:
            self._rotate(obj.id, cp)
        return cp

    def _rotate(self, oid: str, cp: Dict[str, Any]) -> None:
        d = self.dir(oid) / "checkpoints"
        d.mkdir(parents=True, exist_ok=True)
        snap = dict(cp)
        try:
            snap["tasks_payload"] = self.store.load_tasks(oid)
            snap["objective"] = (self.store.load(oid) or Objective(id=oid, goal="")).to_dict()
        except Exception:
            pass
        _write_json(d / f"{cp['seq']:06d}.json", snap)
        snaps = sorted(d.glob("*.json"))
        for old in snaps[:-self.keep]:
            old.unlink(missing_ok=True)

    def read_cp(self, oid: str) -> Dict[str, Any]:
        try:
            return json.loads(self.cp_path(oid).read_text(encoding="utf-8"))
        except Exception:
            return {}

    def snapshots(self, oid: str) -> List[Path]:
        d = self.dir(oid) / "checkpoints"
        return sorted(d.glob("*.json")) if d.exists() else []

    # ------------------------------------------------------------------ load
    def load(self, oid: str) -> Tuple[Optional[Objective], TaskGraph]:
        obj = self.store.load(oid)
        graph = TaskGraph.from_list(self.store.load_tasks(oid))
        return obj, graph

    # ------------------------------------------------------------------ lock
    def acquire(self, oid: str) -> Dict[str, Any]:
        info = {"pid": os.getpid(), "host": socket.gethostname(), "at": time.time()}
        _write_json(self.lock_path(oid), info)
        return info

    def release(self, oid: str) -> None:
        try:
            self.lock_path(oid).unlink()
        except OSError:
            pass

    def lock(self, oid: str) -> Dict[str, Any]:
        try:
            return json.loads(self.lock_path(oid).read_text(encoding="utf-8"))
        except Exception:
            return {}

    def locked_by_live_process(self, oid: str) -> bool:
        lk = self.lock(oid)
        return bool(lk) and lk.get("host") == socket.gethostname() and _pid_alive(int(lk.get("pid", 0)))

    # ------------------------------------------------------------------ crash recovery
    def interrupted(self) -> List[Interrupted]:
        """Objectives that look mid-run but have no live lock (crash / kill / power loss)."""
        out: List[Interrupted] = []
        for obj in self.store.list():
            if obj.status not in INTERRUPTED_STATUSES:
                continue
            if self.locked_by_live_process(obj.id):
                continue
            lk = self.lock(obj.id)
            cp = self.read_cp(obj.id)
            out.append(Interrupted(objective_id=obj.id, goal=obj.goal, status=obj.status,
                                   tasks=cp.get("tasks", {}), lock_pid=int(lk.get("pid", 0) or 0),
                                   lock_host=str(lk.get("host", "")), at=float(cp.get("at", 0) or 0)))
        out.sort(key=lambda i: -i.at)
        return out

    def restore(self, oid: str, note: str = "resumed after interruption") -> Tuple[Optional[Objective], TaskGraph]:  # noqa: D401
        """Bring a checkpointed objective back to a runnable state (idempotent)."""
        obj, graph = self.load(oid)
        if obj is None:
            return None, graph
        changed = 0
        for t in graph.tasks.values():
            if t.status in IN_FLIGHT:
                t.status = TaskStatus.FAILED
                t.history.append({"from": "crash", "to": TaskStatus.FAILED,
                                  "at": time.time(), "note": "interrupted"})
                t.transition(TaskStatus.RETRYING, note)
                changed += 1
            elif t.status in (TaskStatus.NEEDS_USER, TaskStatus.BLOCKED):
                t.transition(TaskStatus.READY, "restored for resume")
                changed += 1
        if obj.status in INTERRUPTED_STATUSES:
            obj.set_status(ObjectiveStatus.RUNNING if obj.status == ObjectiveStatus.RUNNING else obj.status)
        self.save(obj, graph, note=f"{note} ({changed} task(s) recovered)")
        return obj, graph

    def digest(self, oid: str) -> str:
        return str(self.read_cp(oid).get("digest", ""))

    def verify(self, oid: str) -> Dict[str, Any]:
        """Does the on-disk task graph match the recorded checkpoint digest?"""
        cp = self.read_cp(oid)
        payload = self.store.load_tasks(oid)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]
        return {"objective_id": oid, "recorded": cp.get("digest", ""), "current": digest,
                "intact": bool(cp.get("digest")) and cp.get("digest") == digest,
                "seq": cp.get("seq", 0), "snapshots": len(self.snapshots(oid))}
