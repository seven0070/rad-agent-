"""Controller — owns an Objective's lifecycle end to end.

    create → plan → [schedule → execute → observe → verify → (recover)]* → verify objective → done

The LLM proposes; the Controller decides. Execution reuses the existing
`Session` brain loop (DNA + memory + tools + router) so nothing is duplicated —
the Controller wraps `run_tool` to observe every action and enforce budgets.
State is checkpointed to disk after every transition, so `resume()` after a
crash continues where it stopped.
"""
from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.control import events as E
from rad.control.events import EventLog
from rad.control.graph import TaskGraph
from rad.control.objectives import Budget, Objective, ObjectiveStatus, ObjectiveStore
from rad.control.observer import Observer
from rad.control.planner import Planner
from rad.control.recovery import Decision, RecoveryEngine
from rad.control.tasks import Check, Task, TaskStatus
from rad.control.verifier import FAILED, UNVERIFIED, VERIFIED, Verifier
from rad.home import RadHome

DONE_RE = re.compile(r"\bDONE:\s*(.+)", re.I)
BLOCKED_RE = re.compile(r"\bBLOCKED:\s*(.+)", re.I)
NEEDS_USER_RE = re.compile(r"\bNEEDS_USER:\s*(.+)", re.I)


class BudgetExceeded(Exception):
    pass


class Controller:
    def __init__(self, home: RadHome, session_factory: Optional[Callable[..., Any]] = None,
                 llm: Optional[Callable[[str], str]] = None, quiet: bool = False) -> None:
        self.home = home
        self.store = ObjectiveStore(home)
        self._session_factory = session_factory
        self._llm = llm
        self.quiet = quiet
        self.on_event: Optional[Callable[[E.Event], None]] = None

    # ------------------------------------------------------------ wiring
    def _make_session(self, obj: Objective):
        if self._session_factory:
            return self._session_factory(self.home, auto=obj.auto)
        from rad.session import Session
        return Session(self.home, auto=obj.auto)

    def _brain(self) -> Optional[Callable[[str], str]]:
        if self._llm is not None:
            return self._llm
        try:
            from rad.router import RouterState
            r = RouterState(self.home)
            if not r.build_chain():
                return None
            return lambda p: r.chat([{"role": "user", "content": p}], stream_cb=None, temperature=0.2).text
        except Exception:
            return None

    def _log(self, oid: str) -> EventLog:
        log = EventLog(self.store.events_path(oid))
        if self.on_event:
            log.subscribe(self.on_event)
        return log

    def _say(self, msg: str) -> None:
        if not self.quiet:
            from rad.ui import info
            info(msg)

    # ------------------------------------------------------------ lifecycle
    def create(self, goal: str, success_criteria: Optional[List[str]] = None,
               constraints: Optional[List[str]] = None, budget: Optional[Budget] = None,
               auto: bool = False, priority: str = "normal", deadline: Optional[float] = None) -> Objective:
        obj = Objective.new(goal, success_criteria=success_criteria or [], constraints=constraints or [],
                            budget=budget or Budget(), auto=auto, priority=priority, deadline=deadline)
        self.store.save(obj)
        self._log(obj.id).emit(E.OBJECTIVE_CREATED, obj.id, goal=goal, criteria=obj.success_criteria,
                               budget=obj.budget.to_dict())
        return obj

    def plan(self, obj: Objective) -> TaskGraph:
        log = self._log(obj.id)
        obj.set_status(ObjectiveStatus.PLANNING)
        self.store.save(obj)
        planner = Planner(self._brain(), str(self.home.workspace()))
        res = planner.plan(obj)
        graph: TaskGraph = res["graph"]
        obj.verification = {"objective_checks": [c.to_dict() for c in res["objective_checks"]]}
        self._checkpoint(obj, graph, log)
        log.emit(E.PLAN_CREATED, obj.id, source=res["source"], tasks=[
            {"id": t.id, "text": t.text, "depends_on": t.depends_on, "checks": len(t.checks)} for t in graph.tasks.values()])
        for t in graph.tasks.values():
            log.emit(E.TASK_CREATED, obj.id, t.id, text=t.text, depends_on=t.depends_on)
        return graph

    def run(self, obj: Objective, max_tasks: Optional[int] = None) -> Objective:
        """Plan if needed, then drive the graph to completion / failure / needs_user."""
        graph = self.load_graph(obj) if self.store.load_tasks(obj.id) else self.plan(obj)
        return self._drive(obj, graph, max_tasks)

    def resume(self, ref: str, max_tasks: Optional[int] = None) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if not obj:
            return None
        graph = self.load_graph(obj)
        # anything left RUNNING/OBSERVING/VERIFYING by a crash goes back to RETRYING
        for t in graph.tasks.values():
            if t.status in (TaskStatus.RUNNING, TaskStatus.OBSERVING, TaskStatus.VERIFYING):
                t.status = TaskStatus.FAILED
                t.history.append({"from": "crash", "to": "FAILED", "at": time.time(), "note": "interrupted"})
                t.transition(TaskStatus.RETRYING, "resumed after interruption")
        if obj.status in (ObjectiveStatus.PAUSED, ObjectiveStatus.NEEDS_USER):
            for t in graph.tasks.values():
                if t.status in (TaskStatus.NEEDS_USER, TaskStatus.BLOCKED):
                    t.transition(TaskStatus.READY, "user resumed")
        if obj.status in ObjectiveStatus.ACTIVE or obj.status == ObjectiveStatus.FAILED:
            obj.set_status(ObjectiveStatus.RUNNING)
        else:
            return obj
        self._log(obj.id).emit(E.OBJECTIVE_STATUS, obj.id, status="resumed")
        return self._drive(obj, graph, max_tasks)

    def pause(self, ref: str) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if obj and obj.status in ObjectiveStatus.ACTIVE:
            obj.set_status(ObjectiveStatus.PAUSED)
            self.store.save(obj)
            self._log(obj.id).emit(E.OBJECTIVE_STATUS, obj.id, status="paused")
        return obj

    def cancel(self, ref: str) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if obj and obj.status in ObjectiveStatus.ACTIVE:
            graph = self.load_graph(obj)
            for t in graph.tasks.values():
                if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                    try:
                        t.transition(TaskStatus.CANCELLED, "objective cancelled")
                    except Exception:
                        t.status = TaskStatus.CANCELLED
            obj.set_status(ObjectiveStatus.CANCELLED)
            log = self._log(obj.id)
            self._checkpoint(obj, graph, log)
            log.emit(E.OBJECTIVE_STATUS, obj.id, status="cancelled")
        return obj

    def load_graph(self, obj: Objective) -> TaskGraph:
        return TaskGraph.from_list(self.store.load_tasks(obj.id))

    # ------------------------------------------------------------ main loop
    def _drive(self, obj: Objective, graph: TaskGraph, max_tasks: Optional[int]) -> Objective:
        log = self._log(obj.id)
        obj.set_status(ObjectiveStatus.RUNNING)
        self.store.save(obj)
        obs_dir = self.store.dir(obj.id)
        observer = Observer(obs_dir)
        verifier = Verifier(self.home.workspace(), observer, llm=self._brain())
        recovery = RecoveryEngine()
        repairs: Dict[str, int] = {}
        lock = threading.RLock()
        parallel = max(1, int(self.home.cfg.get("objective_parallel", 1) or 1))
        if not obj.auto:
            parallel = 1                      # confirmations are interactive → never interleave
        started = time.time()
        base_seconds = obj.usage.seconds      # cumulative across resumes
        ran = 0
        sessions: List[Any] = []

        def tick() -> None:
            obj.usage.seconds = base_seconds + (time.time() - started)

        def one(task: Task) -> None:
            session = self._make_session(obj)
            sessions.append(session)
            self._wrap_tools(session, obj, observer, log, lock)
            try:
                self._run_task(obj, graph, task, session, observer, verifier, recovery, repairs, log, lock)
            finally:
                try:
                    session.close()
                except Exception:
                    pass

        try:
            while True:
                tick()
                over = obj.over_budget()
                if over:
                    log.emit(E.BUDGET_EXCEEDED, obj.id, reason=over)
                    return self._finish(obj, graph, log, ObjectiveStatus.NEEDS_USER, f"stopped: {over}")
                if obj.status == ObjectiveStatus.PAUSED:
                    return obj
                if graph.is_complete():
                    break
                ready = graph.ready()
                if not ready:
                    if graph.is_stuck():
                        why = self._stuck_reason(graph)
                        st = ObjectiveStatus.NEEDS_USER if "NEEDS_USER" in why or "BLOCKED" in why else ObjectiveStatus.FAILED
                        return self._finish(obj, graph, log, st, why)
                    break
                if max_tasks is not None and ran >= max_tasks:
                    self._checkpoint(obj, graph, log)
                    return obj
                batch = ready[:parallel]
                if max_tasks is not None:
                    batch = batch[:max(1, max_tasks - ran)]
                ran += len(batch)
                if len(batch) == 1:
                    one(batch[0])
                else:
                    log.emit(E.TASK_STATUS, obj.id, status="parallel", tasks=[t.id for t in batch])
                    with ThreadPoolExecutor(max_workers=len(batch), thread_name_prefix="rad-task") as pool:
                        futs = [pool.submit(one, t) for t in batch]
                        for f in as_completed(futs):
                            f.result()        # re-raise BudgetExceeded etc. in the driver
                tick()
                self._checkpoint(obj, graph, log)
                for t in graph.tasks.values():
                    if t.status in TaskStatus.OPEN and graph.deps_doomed(t):
                        t.transition(TaskStatus.BLOCKED, "a required dependency failed permanently")
                        log.emit(E.TASK_STATUS, obj.id, t.id, status=t.status, note=t.note)
        except BudgetExceeded as e:
            log.emit(E.BUDGET_EXCEEDED, obj.id, reason=str(e))
            tick()
            return self._finish(obj, graph, log, ObjectiveStatus.NEEDS_USER, f"stopped: {e}")

        tick()
        return self._verify_objective(obj, graph, verifier, observer, log)

    def _run_task(self, obj: Objective, graph: TaskGraph, task: Task, session, observer: Observer,
                  verifier: Verifier, recovery: RecoveryEngine, repairs: Dict[str, int], log: EventLog,
                  lock: Optional[threading.RLock] = None) -> None:
        lock = lock or threading.RLock()
        if task.status == TaskStatus.PENDING:
            task.transition(TaskStatus.READY)
        if task.status == TaskStatus.RETRYING:
            task.transition(TaskStatus.READY)
        hint = task.verification.get("hint", "") if task.verification else ""
        task.transition(TaskStatus.RUNNING)
        log.emit(E.TASK_STARTED, obj.id, task.id, attempt=task.attempts, text=task.text)
        self._say(f"  ▶ {task.text}  {'(retry %d)' % task.attempts if task.attempts > 1 else ''}")

        session._rad_current_task = task.id  # type: ignore[attr-defined]
        error = ""
        reply = ""
        prompt = self._task_prompt(obj, graph, task, hint)
        try:
            with lock:
                obj.usage.model_calls += 1
            log.emit(E.MODEL_CALLED, obj.id, task.id, purpose="execute", attempt=task.attempts)
            reply = session.think(prompt) or ""
        except BudgetExceeded:
            raise
        except Exception as e:
            error = str(e)
        task.reply = reply[-4000:]
        # transcript for replay: exact prompt + reply + provider (never inferred later)
        log.emit(E.TRANSCRIPT, obj.id, task.id, attempt=task.attempts, prompt=prompt, reply=reply[-12000:],
                 provider=getattr(session, "last_provider", ""), error=error[:500])

        # explicit signals from the model (advisory only — verification decides)
        nm = NEEDS_USER_RE.search(reply)
        bm = BLOCKED_RE.search(reply)
        if nm or bm:
            note = (nm or bm).group(1).strip()[:300]
            task.transition(TaskStatus.NEEDS_USER if nm else TaskStatus.FAILED, note)
            if bm:
                task.transition(TaskStatus.BLOCKED, note)
            log.emit(E.NEEDS_USER, obj.id, task.id, note=note)
            return

        if error:
            task.transition(TaskStatus.FAILED, error[:300])
            log.emit(E.TASK_FAILED, obj.id, task.id, error=error[:500])
            with lock:
                self._recover(obj, graph, task, observer, recovery, repairs, log, error=error)
            return

        task.transition(TaskStatus.OBSERVING)
        task.observations = [o.id for o in observer.for_task(task.id)]
        task.transition(TaskStatus.VERIFYING)
        log.emit(E.VERIFICATION_STARTED, obj.id, task.id, checks=len(task.checks))
        ver = verifier.verify_task(task, reply)
        task.verification = ver
        log.emit(E.VERIFICATION_RESULT, obj.id, task.id, status=ver["status"], summary=ver["summary"][:600])

        claimed_done = bool(DONE_RE.search(reply))
        if ver["status"] == VERIFIED or (ver["status"] == UNVERIFIED and claimed_done and not task.checks
                                          and self.home.cfg.get("accept_unverified_done", True)
                                          and not any(o.status == "error" for o in observer.for_task(task.id))):
            # VERIFIED, or: no checks were plannable, the model claimed DONE and no tool errored.
            # The latter is recorded honestly as UNVERIFIED on the task.
            task.transition(TaskStatus.COMPLETED, ver["summary"][:300] or "done")
            log.emit(E.TASK_COMPLETED, obj.id, task.id, verified=ver["status"] == VERIFIED)
            self._say(f"  ✓ {task.text}  [{ver['status']}]")
            return

        task.transition(TaskStatus.FAILED, f"verification {ver['status']}: {ver['summary'][:200]}")
        log.emit(E.TASK_FAILED, obj.id, task.id, verification=ver["status"], summary=ver["summary"][:400])
        with lock:
            self._recover(obj, graph, task, observer, recovery, repairs, log, verification=ver)

    def _recover(self, obj: Objective, graph: TaskGraph, task: Task, observer: Observer,
                 recovery: RecoveryEngine, repairs: Dict[str, int], log: EventLog,
                 error: str = "", verification: Optional[Dict[str, Any]] = None) -> None:
        log.emit(E.RECOVERY_STARTED, obj.id, task.id)
        d: Decision = recovery.decide(task, observer.for_task(task.id), error=error, verification=verification,
                                      repairs_so_far=repairs.get(task.id, 0),
                                      retries_left=obj.budget.retries - obj.usage.retries)
        task.failure_class = d.failure_class
        log.emit(E.RECOVERY_DECISION, obj.id, task.id, strategy=d.strategy, failure_class=d.failure_class,
                 reason=d.reason)
        self._say(f"  ↻ {d.failure_class} → {d.strategy}: {d.reason}")
        if d.strategy in ("retry", "retry_with_hint"):
            obj.usage.retries += 1
            task.verification = {**(task.verification or {}), "hint": d.hint}
            task.transition(TaskStatus.RETRYING, d.reason)
            return
        if d.strategy == "repair":
            repairs[task.id] = repairs.get(task.id, 0) + 1
            obj.usage.retries += 1
            fix = Task.new(obj.id, f"Repair prerequisite so that this can succeed: {task.text}. {d.hint}",
                           max_attempts=2)
            # repair runs before the failed task; failed task retries after it
            fix.depends_on = list(task.depends_on)
            graph.add(fix)
            task.depends_on = list(dict.fromkeys(task.depends_on + [fix.id]))
            task.transition(TaskStatus.RETRYING, "waiting on repair step")
            log.emit(E.TASK_CREATED, obj.id, fix.id, text=fix.text, repair_for=task.id)
            return
        if d.strategy == "replan":
            repairs[task.id] = repairs.get(task.id, 0) + 1
            planner = Planner(self._brain(), str(self.home.workspace()))
            new = planner.replan(obj, graph, task, d.hint or d.reason)
            if new:
                for t in graph.tasks.values():
                    if t.status in TaskStatus.OPEN and t.id != task.id:
                        t.transition(TaskStatus.CANCELLED, "superseded by replan")
                task.transition(TaskStatus.CANCELLED, "superseded by replan")
                for t in new:
                    graph.add(t)
                    log.emit(E.TASK_CREATED, obj.id, t.id, text=t.text, replan=True)
                log.emit(E.REPLAN, obj.id, task.id, new_tasks=[t.id for t in new])
                return
            d = Decision("ask_user", d.failure_class, "replan produced no usable plan — " + d.reason)
        if d.strategy == "ask_user":
            task.transition(TaskStatus.NEEDS_USER, d.reason)
            log.emit(E.NEEDS_USER, obj.id, task.id, note=d.reason, data=d.data)
            return
        task.transition(TaskStatus.BLOCKED, d.reason)

    # ------------------------------------------------------------ verification of the whole objective
    def _verify_objective(self, obj: Objective, graph: TaskGraph, verifier: Verifier,
                          observer: Observer, log: EventLog) -> Objective:
        log.emit(E.VERIFICATION_STARTED, obj.id, scope="objective")
        checks = [Check.from_dict(c) for c in (obj.verification or {}).get("objective_checks", [])]
        final = "\n\n".join(f"[{t.text}]\n{t.reply}" for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED)
        ver = verifier.verify_objective(obj.goal, obj.success_criteria, checks, final, observer.artifacts())
        task_unverified = [t.id for t in graph.tasks.values()
                           if t.status == TaskStatus.COMPLETED and t.verification.get("status") != VERIFIED]
        ver["tasks_unverified"] = task_unverified
        obj.verification = {**(obj.verification or {}), "objective": ver}
        log.emit(E.VERIFICATION_RESULT, obj.id, scope="objective", status=ver["status"],
                 tasks_unverified=task_unverified)
        if ver["status"] == FAILED:
            return self._finish(obj, graph, log, ObjectiveStatus.FAILED,
                                "objective verification failed: " + "; ".join(
                                    r["detail"][:80] for r in ver["results"] if not r["ok"]))
        obj.result = self._final_report(obj, graph, observer, ver)
        return self._finish(obj, graph, log, ObjectiveStatus.COMPLETED, "")

    def _final_report(self, obj: Objective, graph: TaskGraph, observer: Observer, ver: Dict[str, Any]) -> str:
        lines = [f"Objective: {obj.goal}", f"Verification: {ver['status']}"]
        if ver.get("tasks_unverified"):
            lines.append(f"Note: {len(ver['tasks_unverified'])} task(s) completed without machine verification.")
        arts = observer.artifacts()
        if arts:
            lines.append("Artifacts:")
            lines += [f"  - {a['location']} ({a.get('size', 0)} bytes, v{a['version']})" for a in arts.values()]
        lines.append("Tasks:")
        for t in graph.tasks.values():
            lines.append(f"  [{t.status}] {t.text}")
        return "\n".join(lines)

    # ------------------------------------------------------------ helpers
    def _finish(self, obj: Objective, graph: TaskGraph, log: EventLog, status: str, note: str) -> Objective:
        obj.set_status(status)
        if status == ObjectiveStatus.COMPLETED:
            obj.failure = ""
            log.emit(E.OBJECTIVE_COMPLETED, obj.id)
        elif status == ObjectiveStatus.FAILED:
            obj.failure = note
            log.emit(E.OBJECTIVE_FAILED, obj.id, reason=note)
        else:
            obj.failure = note
            log.emit(E.OBJECTIVE_STATUS, obj.id, status=status, note=note)
        self._checkpoint(obj, graph, log)
        return obj

    def _checkpoint(self, obj: Objective, graph: TaskGraph, log: EventLog) -> None:
        self.store.save(obj)
        self.store.save_tasks(obj.id, graph.to_list())
        log.emit(E.CHECKPOINT, obj.id, status=obj.status, tasks=graph.summary(), usage=obj.usage.to_dict())

    def _stuck_reason(self, graph: TaskGraph) -> str:
        bad = [t for t in graph.tasks.values() if t.status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER)]
        return "; ".join(f"{t.status} {t.text[:60]}: {t.note[:100]}" for t in bad) or "no runnable tasks"

    def _task_prompt(self, obj: Objective, graph: TaskGraph, task: Task, hint: str) -> str:
        lines = [f"OBJECTIVE: {obj.goal}"]
        if obj.success_criteria:
            lines.append("Success criteria: " + "; ".join(obj.success_criteria))
        done = [t for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED]
        if done:
            lines.append("Already completed: " + "; ".join(t.text[:80] for t in done))
        lines.append(f"\nCURRENT TASK: {task.text}")
        if task.checks:
            lines.append("This task will be VERIFIED by machine checks: " +
                         "; ".join(c.description or f"{c.kind} {c.args}" for c in task.checks))
        if hint:
            lines.append("\nFEEDBACK FROM PREVIOUS ATTEMPT: " + hint)
        lines.append("\nDo the actual work with your tools now. When finished end with one line "
                     "'DONE: <what was done>'. If impossible/unsafe: 'BLOCKED: <why>'. "
                     "If you need information only the user has: 'NEEDS_USER: <question>'.")
        return "\n".join(lines)

    def _wrap_tools(self, session, obj: Objective, observer: Observer, log: EventLog,
                    lock: Optional[threading.RLock] = None) -> None:
        """Intercept every tool call the Session makes: budget → execute → observe."""
        original = session.tool_runner
        ctl = self
        lock = lock or threading.RLock()

        def wrapped(name, args, ctx):
            with lock:
                if obj.budget.tool_calls and obj.usage.tool_calls >= obj.budget.tool_calls:
                    raise BudgetExceeded(f"tool-call budget {obj.budget.tool_calls} exhausted")
                obj.usage.tool_calls += 1
                aid = f"act_{obj.usage.tool_calls}"
            tid = getattr(session, "_rad_current_task", "")
            log.emit(E.TOOL_CALLED, obj.id, tid, action=aid, tool=name, args=args)
            before = observer.snapshot(ctl.home.workspace()) if name == "run_shell" else None
            t0 = time.time()
            out = original(name, args, ctx)
            ms = int((time.time() - t0) * 1000)
            ob = observer.record(obj.id, tid, aid, name, args or {}, out, ms, ctl.home.workspace(),
                                 before=before)
            log.emit(E.TOOL_RESULT, obj.id, tid, action=aid, tool=name, status=ob.status, ms=ms,
                     observation=ob.id, artifacts=ob.artifacts)
            for a in ob.artifacts:
                log.emit(E.ARTIFACT_CREATED, obj.id, tid, artifact=a)
            return out

        session.tool_runner = wrapped
