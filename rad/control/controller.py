"""Controller — owns an Objective's lifecycle end to end.

    create → plan → [schedule → execute → observe → verify → (recover)]* → verify objective → done

The LLM proposes; the Controller decides. Execution reuses the existing
`Session` brain loop (DNA + memory + tools + router) so nothing is duplicated —
but every action now passes through the `Executor` pipeline (capability →
sandbox → permission → budget → tool → observation), the ready-set is chosen by
the `Scheduler` (dependencies, priorities, branches), budgets are enforced by the
`BudgetManager` (tokens and money included), state is checkpointed after every
transition by the `CheckpointManager`, and status transitions go through the
`Lifecycle`.

Older behaviour is unchanged: a crash mid-task is recovered on `resume()`, a
false "DONE" is caught by the Verifier and retried with explicit feedback, and a
run that cannot make progress ends in NEEDS_USER with a reason instead of
pretending to be complete.
"""
from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.control import events as E
from rad.control.budgets import BudgetExceeded, BudgetManager
from rad.control.checkpoints import CheckpointManager
from rad.control.events import EventLog
from rad.control.executor import Executor
from rad.control.graph import TaskGraph
from rad.control.lifecycle import Lifecycle
from rad.control.objectives import Budget, Objective, ObjectiveStatus, ObjectiveStore
from rad.control.observer import Observer
from rad.control.planner import Planner
from rad.control.recovery import Decision, FailureClass, RecoveryEngine
from rad.control.scheduler import Scheduler
from rad.control.tasks import Check, Task, TaskStatus
from rad.control.verifier import FAILED, UNVERIFIED, VERIFIED, Verifier
from rad.home import RadHome
from rad.sandbox import Sandbox

DONE_RE = re.compile(r"\bDONE:\s*(.+)", re.I)
BLOCKED_RE = re.compile(r"\bBLOCKED:\s*(.+)", re.I)
NEEDS_USER_RE = re.compile(r"\bNEEDS_USER:\s*(.+)", re.I)


class Controller:
    def __init__(self, home: RadHome, session_factory: Optional[Callable[..., Any]] = None,
                 llm: Optional[Callable[[str], str]] = None, quiet: bool = False) -> None:
        self.home = home
        self.store = ObjectiveStore(home)
        self.checkpoints = CheckpointManager(home, self.store)
        self.lifecycle = Lifecycle(home, self.store, self.checkpoints)
        self._session_factory = session_factory
        self._llm = llm
        self.quiet = quiet
        self.on_event: Optional[Callable[[E.Event], None]] = None
        #: hook invoked after planning — lets callers re-tag tasks (agents, priorities, budgets)
        self.on_plan: Optional[Callable[[Objective, TaskGraph], None]] = None
        self._avoid_providers: List[str] = []      # model-failure recovery feedback
        self.last_run: Dict[str, Any] = {}

    # ------------------------------------------------------------ wiring
    def _make_session(self, obj: Objective, task: Optional[Task] = None):
        """One session per task attempt, scoped for its agent and its task kind."""
        agent = self._agent_spec(task)
        if self._session_factory:
            session = self._session_factory(self.home, auto=obj.auto)
        else:
            from rad.session import Session
            session = Session(self.home, auto=obj.auto, quiet=self.quiet,
                              actor=f"agent:{agent.id}" if agent else f"control:{obj.id}",
                              memory_scope=agent.id if (agent and agent.memory_scope == "isolated") else None,
                              system_prefix=self._task_system(task))
        ctx = getattr(session, "ctx", None)
        if ctx is not None:
            if agent is not None:
                ctx.agent_caps = list(agent.caps)
                ctx.actor = f"agent:{agent.id}"
            elif not str(getattr(ctx, "actor", "")).startswith("agent:"):
                ctx.actor = f"control:{obj.id}"
        try:
            from rad.modelselect import Requirements
            req = Requirements.for_task_text(task.text if task else obj.goal, label=f"{obj.id}")
            if agent is not None and agent.role == "coder":
                req.kind = "code"
            elif agent is not None and agent.role == "researcher":
                req.kind = "research"
            req.avoid = list(self._avoid_providers)
            session.requirements = req
        except Exception:
            pass
        if agent is not None and hasattr(session, "memory_scope"):
            session.memory_scope = agent.id if agent.memory_scope == "isolated" else None
        return session

    def _task_system(self, task: Optional[Task]) -> str:
        if task is None or not task.agent:
            return ""
        try:
            spec = self._agent_spec(task)
            if spec:
                return (f"You are acting as RAD's '{spec.role}' specialist for this task. {spec.prompt}\n"
                        f"Capabilities granted: {', '.join(spec.caps)}. Anything outside them will be denied.")
        except Exception:
            pass
        return ""

    def _agent_spec(self, task: Optional[Task]):
        if task is None or not getattr(task, "agent", ""):
            return None
        try:
            from rad.agents import AgentRegistry
            return AgentRegistry(self.home).get(task.agent)
        except Exception:
            return None

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
        log = EventLog(self.store.events_path(oid), home=self.home)
        if self.on_event:
            log.subscribe(self.on_event)
        return log

    def _say(self, msg: str) -> None:
        if not self.quiet:
            from rad.ui import info
            info(msg)

    def _planner(self) -> Planner:
        cfg = self.home.cfg
        retries = cfg.get("plan_retries", 1)
        return Planner(self._brain(), str(self.home.workspace()),
                       max_tasks=int(cfg.get("max_plan_tasks", 16) or 16),
                       retries=retries)

    # ------------------------------------------------------------ lifecycle (delegates)
    def create(self, goal: str, success_criteria: Optional[List[str]] = None,
               constraints: Optional[List[str]] = None, budget: Optional[Budget] = None,
               auto: bool = False, priority: str = "normal", deadline: Optional[float] = None,
               tags: Optional[List[str]] = None) -> Objective:
        return self.lifecycle.create(goal, success_criteria=success_criteria, constraints=constraints,
                                     budget=budget, auto=auto, priority=priority, deadline=deadline,
                                     tags=tags)

    def pause(self, ref: str) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if obj and obj.status in ObjectiveStatus.ACTIVE:
            return self.lifecycle.pause(obj)
        return obj

    def cancel(self, ref: str) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if obj and obj.status in ObjectiveStatus.ACTIVE:
            return self.lifecycle.cancel(obj)
        return obj

    def retry(self, ref: str, max_tasks: Optional[int] = None) -> Optional[Objective]:
        obj = self.store.resolve(ref)
        if not obj:
            return None
        graph = self.load_graph(obj)
        self.lifecycle.retry(obj, graph=graph)
        self._log(obj.id).emit(E.OBJECTIVE_STATUS, obj.id, status="retrying")
        return self._drive(obj, graph, max_tasks)

    def expire(self, ref: str, reason: str = "expired by user") -> Optional[Objective]:
        obj = self.store.resolve(ref)
        return self.lifecycle.expire(obj, reason) if obj else None

    def verify_only(self, ref: str) -> Optional[Dict[str, Any]]:
        """Re-run objective verification against the current world (no execution)."""
        obj = self.store.resolve(ref)
        if not obj:
            return None
        graph = self.load_graph(obj)
        observer = Observer(self.store.dir(obj.id))
        verifier = Verifier(self.home.workspace(), observer, llm=self._brain(), home=self.home)
        log = self._log(obj.id)
        log.emit(E.VERIFICATION_RECHECK, obj.id, scope="objective")
        return self._verify_objective(obj, graph, verifier, observer, log, execute=False)

    # ------------------------------------------------------------ planning
    def plan(self, obj: Objective) -> TaskGraph:
        log = self._log(obj.id)
        self.lifecycle.planning(obj)
        planner = self._planner()
        res = planner.plan(obj)
        graph: TaskGraph = res["graph"]
        obj.plan_version = int(getattr(obj, "plan_version", 0) or 0) + 1
        for t in graph.tasks.values():
            t.plan_version = obj.plan_version
        obj.verification = {"objective_checks": [c.to_dict() for c in res["objective_checks"]]}
        self.checkpoints.save(obj, graph, note="plan")
        log.emit(E.PLAN_CREATED, obj.id, source=res["source"], plan_version=obj.plan_version,
                 attempts=res.get("attempts", 0), tasks=[
            {"id": t.id, "text": t.text, "depends_on": t.depends_on, "checks": len(t.checks),
             "priority": t.priority, "optional": t.optional, "agent": t.agent} for t in graph.tasks.values()])
        for t in graph.tasks.values():
            log.emit(E.TASK_CREATED, obj.id, t.id, text=t.text, depends_on=t.depends_on, agent=t.agent)
        if self.on_plan is not None:
            try:
                self.on_plan(obj, graph)
            except Exception:
                pass
            self.checkpoints.save(obj, graph, note="plan (tagged)")
        return graph

    def load_graph(self, obj: Objective) -> TaskGraph:
        return TaskGraph.from_list(self.store.load_tasks(obj.id))

    # ------------------------------------------------------------ run / resume
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
        restored = 0
        for t in graph.tasks.values():
            if t.status in (TaskStatus.RUNNING, TaskStatus.OBSERVING, TaskStatus.VERIFYING):
                t.status = TaskStatus.FAILED
                t.history.append({"from": "crash", "to": "FAILED", "at": time.time(), "note": "interrupted"})
                t.transition(TaskStatus.RETRYING, "resumed after interruption")
                restored += 1
        if restored:
            log = self._log(obj.id)
            log.emit(E.CRASH_DETECTED, obj.id, tasks=restored)
            log.emit(E.CHECKPOINT_RESTORED, obj.id, tasks=restored)
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

    # ------------------------------------------------------------ main loop
    def _drive(self, obj: Objective, graph: TaskGraph, max_tasks: Optional[int]) -> Objective:
        log = self._log(obj.id)
        obj.set_status(ObjectiveStatus.RUNNING)
        self.checkpoints.acquire(obj.id)
        self.checkpoints.save(obj, graph, note="run start")
        obs_dir = self.store.dir(obj.id)
        observer = Observer(obs_dir)
        verifier = Verifier(self.home.workspace(), observer, llm=self._brain(), home=self.home,
                            provenance_dir=obs_dir)
        recovery = RecoveryEngine()
        repairs: Dict[str, int] = {}
        lock = threading.RLock()
        parallel = max(1, int(self.home.cfg.get("objective_parallel", 1) or 1))
        if not obj.auto:
            parallel = 1                      # confirmations are interactive → never interleave
        budgets = BudgetManager(obj.budget, obj.usage,
                                events=lambda kind, data: log.emit(kind, obj.id, **data),
                                objective_id=obj.id, deadline=obj.deadline)

        sandbox = Sandbox(self.home, workspace=self.home.workspace())
        executor = Executor(self.home, objective=obj, budgets=budgets, observer=observer, log=log,
                            sandbox=sandbox, lock=lock, actor=f"control:{obj.id}",
                            tool_runner=self._tool_runner())
        scheduler = Scheduler(parallel=parallel, max_tasks=max_tasks)
        started = time.time()
        base_seconds = float(obj.usage.seconds or 0)
        sessions: List[Any] = []
        self.last_run = {"objective": obj.id, "parallel": parallel, "max_tasks": max_tasks}

        def tick() -> None:
            budgets.tick(base_seconds + (time.time() - started))

        def one(task: Task) -> None:
            session = self._make_session(obj, task)
            sessions.append(session)
            executor.task_id = task.id
            executor.install(session)
            ctx = getattr(session, "ctx", None)
            if ctx is not None:
                try:
                    ctx._task_id = task.id                    # type: ignore[attr-defined]
                except Exception:
                    pass
                if task.agent:
                    spec = self._agent_spec(task)
                    if spec is not None:
                        ctx.agent_caps = list(spec.caps)
                        executor.sandbox = agent_sandbox(self.home, spec)
            try:
                self._run_task(obj, graph, task, session, observer, verifier, recovery, repairs, log,
                               lock, budgets, executor)
            finally:
                try:
                    session.close()
                except Exception:
                    pass
                executor.sandbox = sandbox

        try:
            while True:
                tick()
                over = budgets.check()
                if over:
                    stopped = self._on_budget(obj, graph, log, over.reason, observer, verifier)
                    if stopped is not None:
                        return stopped
                    break
                if obj.status == ObjectiveStatus.PAUSED:
                    self.checkpoints.save(obj, graph, "paused")
                    return obj
                if graph.is_complete():
                    break
                scheduler.block_doomed(graph)
                batch = scheduler.next_batch(graph)
                if batch.empty:
                    if scheduler.expect_more(graph):
                        continue                      # a retry will make progress
                    why = self._stuck_reason(graph)
                    st = (ObjectiveStatus.NEEDS_USER
                          if any(k in why for k in ("NEEDS_USER", "BLOCKED", "budget", "stopped"))
                          else ObjectiveStatus.FAILED)
                    return self._finish(obj, graph, log, st, why, observer=observer)
                if max_tasks is not None and scheduler.dispatched > max_tasks:
                    self.checkpoints.save(obj, graph, "task limit")
                    return obj
                tasks = batch.tasks
                if len(tasks) == 1:
                    one(tasks[0])
                else:
                    log.emit(E.TASK_STATUS, obj.id, status="parallel", tasks=[t.id for t in tasks])
                    with ThreadPoolExecutor(max_workers=len(tasks), thread_name_prefix="rad-task") as pool:
                        futs = [pool.submit(one, t) for t in tasks]
                        for f in as_completed(futs):
                            f.result()        # re-raise BudgetExceeded etc. in the driver
                tick()
                self.checkpoints.save(obj, graph, "loop")
                scheduler.block_doomed(graph)
                if max_tasks is not None and scheduler.dispatched >= max_tasks:
                    if graph.is_complete():
                        break
                    self.checkpoints.save(obj, graph, "task limit")
                    return obj
        except BudgetExceeded as e:
            tick()
            stopped = self._on_budget(obj, graph, log, str(e), observer, verifier)
            if stopped is not None:
                return stopped
        finally:
            for s in sessions:
                try:
                    s.close()
                except Exception:
                    pass
            self.checkpoints.release(obj.id)

        tick()
        return self._verify_objective(obj, graph, verifier, observer, log)

    def _tool_runner(self):
        """The tool runner used underneath the executor (injectable in tests)."""
        runner = getattr(self, "tool_runner", None)
        if runner is not None:
            return runner
        from rad.tools import run_tool
        return run_tool

    # ------------------------------------------------------------ one task
    def _run_task(self, obj: Objective, graph: TaskGraph, task: Task, session, observer: Observer,
                  verifier: Verifier, recovery: RecoveryEngine, repairs: Dict[str, int], log: EventLog,
                  lock: Optional[threading.RLock] = None, budgets: Optional[BudgetManager] = None,
                  executor: Optional[Executor] = None) -> None:
        lock = lock or threading.RLock()
        if task.status == TaskStatus.PENDING:
            task.transition(TaskStatus.READY)
        if task.status == TaskStatus.RETRYING:
            task.transition(TaskStatus.READY)
        hint = task.verification.get("hint", "") if task.verification else ""
        task.transition(TaskStatus.RUNNING)
        log.emit(E.TASK_STARTED, obj.id, task.id, attempt=task.attempts, text=task.text,
                 agent=task.agent, priority=task.priority)
        self._say(f"  ▶ {task.text}  {'(retry %d)' % task.attempts if task.attempts > 1 else ''}")

        session._rad_current_task = task.id  # type: ignore[attr-defined]
        error = ""
        reply = ""
        prompt = self._task_prompt(obj, graph, task, hint)
        try:
            if session.requirements is not None:
                log.emit(E.MODEL_SELECTED, obj.id, task.id,
                         requirements=session.requirements.to_dict(),
                         provider=str(getattr(session, "last_provider", "") or ""))
            with lock:
                if budgets is not None:
                    budgets.charge("model_calls", 1)
                else:
                    obj.usage.model_calls += 1
            log.emit(E.MODEL_CALLED, obj.id, task.id, purpose="execute", attempt=task.attempts)
            reply = session.think(prompt) or ""
            if budgets is not None:
                usage = getattr(session, "last_usage", {}) or {}
                tokens = int(usage.get("in", 0)) + int(usage.get("out", 0))
                extra_calls = max(0, int(usage.get("rounds", 1)) - 1)
                if tokens or extra_calls:
                    budgets.charge_model(tokens=tokens, calls=extra_calls)
                    log.emit(E.MODEL_CALLED, obj.id, task.id, purpose="usage",
                             tokens=tokens, rounds=usage.get("rounds", 1),
                             provider=getattr(session, "last_provider", ""))
        except BudgetExceeded:
            raise
        except Exception as e:
            error = str(e)
        task.reply = reply[-4000:]
        # transcript for replay: exact prompt + reply + provider (never inferred later)
        log.emit(E.TRANSCRIPT, obj.id, task.id, attempt=task.attempts, prompt=prompt, reply=reply[-12000:],
                 provider=getattr(session, "last_provider", ""), error=error[:500],
                 usage=getattr(session, "last_usage", {}) or {})

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
                self._recover(obj, graph, task, observer, recovery, repairs, log, error=error,
                              budgets=budgets, executor=executor)
            return

        task.transition(TaskStatus.OBSERVING)
        task.observations = [o.id for o in observer.for_task(task.id)]
        log.emit(E.TASK_STATUS, obj.id, task.id, status=TaskStatus.OBSERVING,
                 observations=len(task.observations))
        task.transition(TaskStatus.VERIFYING)
        log.emit(E.VERIFICATION_STARTED, obj.id, task.id, checks=len(task.checks))
        ver = verifier.verify_task(task, reply)
        task.verification = ver
        task.artifacts = [a for o in observer.for_task(task.id) for a in o.artifacts]
        log.emit(E.VERIFICATION_RESULT, obj.id, task.id, status=ver["status"], summary=ver["summary"][:600])

        claimed_done = bool(DONE_RE.search(reply))
        task_obs = observer.for_task(task.id)
        refused = any(o.status in ("blocked", "declined", "denied") for o in task_obs)
        if ver["status"] == VERIFIED or (ver["status"] == UNVERIFIED and claimed_done and not task.checks
                                          and self.home.cfg.get("accept_unverified_done", True)
                                          and not any(o.status == "error" for o in task_obs)
                                          and not refused):
            # note: a task whose only actions were *refused* by policy/sandbox can never be
            # accepted as done, no matter what the model claims (see the adversarial lab bank)
            # VERIFIED, or: no checks were plannable, the model claimed DONE and no tool errored.
            # The latter is recorded honestly as UNVERIFIED on the task.
            task.transition(TaskStatus.COMPLETED, ver["summary"][:300] or "done")
            log.emit(E.TASK_COMPLETED, obj.id, task.id, verified=ver["status"] == VERIFIED)
            self._record_agent_run(obj, task, reply, "done", ver)
            self._say(f"  ✓ {task.text}  [{ver['status']}]")
            return

        task.transition(TaskStatus.FAILED, f"verification {ver['status']}: {ver['summary'][:200]}")
        log.emit(E.TASK_FAILED, obj.id, task.id, verification=ver["status"], summary=ver["summary"][:400])
        self._record_agent_run(obj, task, reply or error, "failed", ver)
        with lock:
            self._recover(obj, graph, task, observer, recovery, repairs, log, verification=ver,
                          budgets=budgets, executor=executor)

    def _record_agent_run(self, obj: Objective, task: Task, output: str, status: str,
                          verification: Optional[Dict[str, Any]] = None) -> None:
        """Tasks delegated to a specialist agent leave a run record in the agent registry.

        The control plane still owns execution — this is the audit trail that says *which*
        agent did the work, under which capability envelope, with what result, so the team
        history (`rad agents runs`, `/v1/agents`) reflects the objective that used it.
        """
        if not task.agent:
            return
        try:
            import uuid as _uuid

            from rad.agents import AgentRegistry, AgentRun
            spec = self._agent_spec(task)
            if spec is None:
                return
            obs = [o for o in Observer(self.store.dir(obj.id)).for_task(task.id)]
            ver = verification or {}
            run = AgentRun(id="run_" + _uuid.uuid4().hex[:8], agent=spec.id, role=spec.role,
                           objective_id=obj.id, task_id=task.id, input=task.text[:300],
                           status=status, output=str(output or "")[:800],
                           tool_calls=len(obs),
                           denied=[o.tool for o in obs if o.status in ("declined", "denied", "blocked")],
                           provider=str(getattr(self, "last_provider", "") or ""),
                           evidence=[{"task_verification": ver.get("status", ""),
                                      "summary": str(ver.get("summary", ""))[:200],
                                      "caps": list(spec.caps), "attempts": int(task.attempts)}])
            AgentRegistry(self.home).save_run(run)
        except Exception:
            pass                                        # an audit record must never break a run

    # ------------------------------------------------------------ recovery
    def _recover(self, obj: Objective, graph: TaskGraph, task: Task, observer: Observer,
                 recovery: RecoveryEngine, repairs: Dict[str, int], log: EventLog,
                 error: str = "", verification: Optional[Dict[str, Any]] = None,
                 budgets: Optional[BudgetManager] = None,
                 executor: Optional[Executor] = None) -> None:
        log.emit(E.RECOVERY_STARTED, obj.id, task.id)
        artifacts = observer.artifacts()
        d: Decision = recovery.decide(task, observer.for_task(task.id), error=error, verification=verification,
                                      repairs_so_far=repairs.get(task.id, 0),
                                      retries_left=(budgets.remaining("retries") if budgets else
                                                    obj.budget.retries - obj.usage.retries),
                                      artifacts=artifacts)
        task.failure_class = d.failure_class
        log.emit(E.RECOVERY_DECISION, obj.id, task.id, strategy=d.strategy, failure_class=d.failure_class,
                 reason=d.reason)
        self._say(f"  ↻ {d.failure_class} → {d.strategy}: {d.reason}")

        def spend_retry() -> None:
            if budgets is not None:
                budgets.charge_retry()
            else:
                obj.usage.retries += 1

        if d.strategy in ("retry", "retry_with_hint", "switch_tool", "switch_model"):
            spend_retry()
            if d.strategy == "switch_model":
                self._switch_model(session_hint=d.data.get("avoid"), log=log, obj=obj, task=task)
            task.verification = {**(task.verification or {}), "hint": d.hint or d.reason}
            task.transition(TaskStatus.RETRYING, d.reason)
            return
        if d.strategy == "rollback":
            restored = self._rollback(observer, d.data.get("path", ""), log=log, obj=obj, task=task)
            if restored:
                spend_retry()
                task.verification = {**(task.verification or {}),
                                     "hint": f"restored {restored} to its last verified version; "
                                             f"redo the step without corrupting it. {d.hint}"}
                task.transition(TaskStatus.RETRYING, f"rolled back {restored}")
                return
            d = Decision("retry_with_hint" if task.can_retry else "ask_user", d.failure_class,
                         "rollback was not possible — " + d.reason, hint=d.hint)
        if d.strategy == "repair":
            repairs[task.id] = repairs.get(task.id, 0) + 1
            spend_retry()
            if d.failure_class == FailureClass.ENVIRONMENT:
                text = f"Repair prerequisite so that this can succeed: {task.text}. {d.hint}"
            else:
                text = f"Repair so that machine checks pass. {d.hint}"
            fix = Task.new(obj.id, text, max_attempts=2)
            if d.failure_class != FailureClass.ENVIRONMENT and task.checks:
                fix.checks = [Check(kind=c.kind, args=dict(c.args), description=c.description)
                              for c in task.checks]
            # repair runs before the failed task; failed task retries after it
            fix.depends_on = list(task.depends_on)
            graph.add(fix)
            task.depends_on = list(dict.fromkeys(task.depends_on + [fix.id]))
            task.verification = {**(task.verification or {}), "hint": d.hint or d.reason}
            task.transition(TaskStatus.RETRYING, "waiting on repair step")
            log.emit(E.TASK_CREATED, obj.id, fix.id, text=fix.text, repair_for=task.id)
            return
        if d.strategy == "spawn_specialist":
            role = d.data.get("role") or self._pick_role(task, d.failure_class)
            if role and (budgets is None or budgets.remaining("agents") > 0):
                if budgets is not None:
                    budgets.charge_agent()
                task.agent = role
                spend_retry()
                task.verification = {**(task.verification or {}),
                                     "hint": f"a {role} specialist takes this over. {d.hint}"}
                task.transition(TaskStatus.RETRYING, f"delegated to {role}")
                log.emit(E.AGENT_STARTED, obj.id, task.id, agent=role, reason=d.reason)
                return
        if d.strategy == "replan":
            repairs[task.id] = repairs.get(task.id, 0) + 1
            planner = self._planner()
            new = planner.replan(obj, graph, task, d.hint or d.reason)
            if new:
                # superseded work is *recorded* (CANCELLED + deactivated), never silently dropped:
                # the task keeps its history, its failure reason and its events, but it no longer
                # counts as outstanding work for this objective.
                superseded = [t for t in graph.tasks.values()
                              if (t.status in TaskStatus.OPEN or t.id == task.id) and t.id != task.id] \
                    + [task]
                for t in superseded:
                    if t.status in TaskStatus.OPEN or t.id == task.id:
                        t.transition(TaskStatus.CANCELLED, "superseded by replan")
                        t.active = False
                        log.emit(E.TASK_STATUS, obj.id, t.id, status=TaskStatus.CANCELLED,
                                 superseded=True, reason="superseded by replan")
                obj.plan_version = int(getattr(obj, "plan_version", 0) or 0) + 1
                for t in new:
                    t.plan_version = obj.plan_version
                    graph.add(t)
                    log.emit(E.TASK_CREATED, obj.id, t.id, text=t.text, replan=True,
                             plan_version=obj.plan_version)
                log.emit(E.REPLAN, obj.id, task.id, plan_version=obj.plan_version, new_tasks=[t.id for t in new],
                         superseded=[t.id for t in superseded if t.id != task.id])
                return
            d = Decision("ask_user", d.failure_class, "replan produced no usable plan — " + d.reason)
        if d.strategy == "ask_user":
            task.transition(TaskStatus.NEEDS_USER, d.reason)
            log.emit(E.NEEDS_USER, obj.id, task.id, note=d.reason, data=d.data)
            return
        task.transition(TaskStatus.BLOCKED, d.reason)

    def _switch_model(self, session_hint: Optional[List[str]], log: EventLog, obj: Objective,
                      task: Task) -> None:
        """Remember which providers failed so the next attempt avoids them."""
        avoid: List[str] = list(session_hint or [])
        if not avoid:
            try:
                from rad.router import RouterState
                r = RouterState(self.home)
                avoid = [name for name, f in r.failures.items() if f]
            except Exception:
                avoid = []
        for p in avoid:
            if p not in self._avoid_providers:
                self._avoid_providers.append(p)
        if avoid:
            log.emit(E.MODEL_FALLBACK, obj.id, task.id, avoid=avoid)

    def _rollback(self, observer: Observer, path: str, log: EventLog, obj: Objective, task: Task) -> str:
        """Restore the last *verified* version of an artifact that this attempt broke."""
        if not path:
            return ""
        name = Path(path).name
        for art in sorted(observer.artifacts().values(), key=lambda a: -a["version"]):
            if Path(art["location"]).name == name and art.get("verification", {}).get("ok"):
                if observer.rollback_artifact(art["id"]):
                    log.emit(E.RECOVERY_DECISION, obj.id, task.id, strategy="rollback_done",
                             artifact=art["id"], path=path)
                    return name
        return ""

    @staticmethod
    def _pick_role(task: Task, failure_class: str) -> str:
        text = (task.text or "").lower()
        if failure_class in ("VALIDATION_FAILURE", "UNKNOWN", "PLANNING_FAILURE"):
            if any(w in text for w in ("code", "script", "function", "test", "bug", "refactor")):
                return "coder"
            if any(w in text for w in ("research", "compare", "source", "web", "cite")):
                return "researcher"
            if any(w in text for w in ("write", "report", "doc", "summary")):
                return "writer"
            return "reviewer"
        return ""

    # ------------------------------------------------------------ budget vs. already-done work
    def _on_budget(self, obj: Objective, graph: TaskGraph, log: EventLog, reason: str,
                   observer: Observer, verifier: Verifier) -> Optional[Objective]:
        """Budget exhausted: never rubber-stamp DONE, but do not ignore already-met checks.

        If the graph is already complete, or remaining work is already proven by machine
        checks (including objective_checks), fall through to `_verify_objective`.
        Otherwise NEEDS_USER — same as before. Model claims are not consulted here.
        """
        log.emit(E.BUDGET_EXCEEDED, obj.id, reason=reason)
        if graph.is_complete():
            return None
        closed = self._close_already_satisfied(obj, graph, verifier, observer, log)
        if closed:
            log.emit(E.TASK_STATUS, obj.id, status="already_verified_on_budget", closed=closed)
        if graph.is_complete():
            return None
        if self._objective_already_satisfied(obj, verifier):
            self._supersede_open(obj, graph, log,
                                 "objective machine checks already satisfied (budget exhausted)")
            return None
        return self._finish(obj, graph, log, ObjectiveStatus.NEEDS_USER,
                            f"stopped: {reason}", observer=observer)

    def _close_already_satisfied(self, obj: Objective, graph: TaskGraph, verifier: Verifier,
                                 observer: Observer, log: EventLog) -> List[str]:
        """Complete OPEN tasks whose machine checks already pass — no model call, no DONE claim."""
        closed: List[str] = []
        for task in list(graph.tasks.values()):
            if task.status not in (TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RETRYING):
                continue
            if not task.checks:
                continue
            ver = verifier.verify_task(task, reply="")
            machine = [r for r in ver.get("results") or [] if r.get("machine", True) and r.get("level") == "check"]
            if ver.get("status") != VERIFIED or not machine or any(not r.get("ok") for r in machine):
                continue
            self._walk_to_completed(task, ver, "already satisfied by machine checks")
            log.emit(E.TASK_COMPLETED, obj.id, task.id, verified=True, skipped_model=True)
            closed.append(task.id)
        return closed

    def _objective_already_satisfied(self, obj: Objective, verifier: Verifier) -> bool:
        raw = (obj.verification or {}).get("objective_checks") or []
        if not raw:
            return False
        checks = [Check.from_dict(c) for c in raw]
        results = [verifier.run_check(c) for c in checks]
        machine = [r for r in results if r.get("machine", True)]
        return bool(machine) and all(bool(r.get("ok")) for r in machine)

    def _supersede_open(self, obj: Objective, graph: TaskGraph, log: EventLog, reason: str) -> None:
        for t in graph.tasks.values():
            if t.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                continue
            try:
                if t.status == TaskStatus.OBSERVING:
                    t.transition(TaskStatus.FAILED, reason)
                if t.status == TaskStatus.VERIFYING:
                    t.transition(TaskStatus.FAILED, reason)
                t.transition(TaskStatus.CANCELLED, reason)
                t.active = False
                log.emit(E.TASK_STATUS, obj.id, t.id, status=TaskStatus.CANCELLED,
                         superseded=True, reason=reason)
            except Exception:
                continue

    @staticmethod
    def _walk_to_completed(task: Task, ver: Dict[str, Any], note: str) -> None:
        if task.status == TaskStatus.PENDING:
            task.transition(TaskStatus.READY, note)
        if task.status == TaskStatus.RETRYING:
            task.transition(TaskStatus.READY, note)
        if task.status == TaskStatus.READY:
            task.transition(TaskStatus.RUNNING, note)
        if task.status == TaskStatus.RUNNING:
            task.transition(TaskStatus.OBSERVING, note)
        if task.status == TaskStatus.OBSERVING:
            task.transition(TaskStatus.VERIFYING, note)
        task.verification = ver
        if task.status == TaskStatus.VERIFYING:
            task.transition(TaskStatus.COMPLETED, note)
        elif task.status == TaskStatus.FAILED:
            task.transition(TaskStatus.COMPLETED, note)

    # ------------------------------------------------------------ objective verification
    def _verify_objective(self, obj: Objective, graph: TaskGraph, verifier: Verifier,
                          observer: Observer, log: EventLog, execute: bool = True) -> Objective:
        log.emit(E.VERIFICATION_STARTED, obj.id, scope="objective")
        checks = [Check.from_dict(c) for c in (obj.verification or {}).get("objective_checks", [])]
        final = "\n\n".join(f"[{t.text}]\n{t.reply}" for t in graph.tasks.values()
                            if t.status == TaskStatus.COMPLETED)
        ver = verifier.verify_objective(obj.goal, obj.success_criteria, checks, final,
                                        observer.artifacts())
        task_unverified = [t.id for t in graph.tasks.values()
                           if t.status == TaskStatus.COMPLETED and t.verification.get("status") != VERIFIED]
        ver["tasks_unverified"] = task_unverified
        ver["budget"] = (BudgetManager(obj.budget, obj.usage, objective_id=obj.id).to_dict())
        obj.verification = {**(obj.verification or {}), "objective": ver}
        log.emit(E.VERIFICATION_RESULT, obj.id, scope="objective", status=ver["status"],
                 tasks_unverified=task_unverified)
        if ver["status"] == FAILED:
            if not execute:
                return obj
            return self._finish(obj, graph, log, ObjectiveStatus.FAILED,
                                "objective verification failed: " + "; ".join(
                                    r["detail"][:80] for r in ver["results"] if not r["ok"]),
                                observer=observer)
        obj.result = self._final_report(obj, graph, observer, ver)
        if execute:
            self._learn(obj, graph, observer, ver)
            return self._finish(obj, graph, log, ObjectiveStatus.COMPLETED, "")
        return obj

    # ------------------------------------------------------------ learning
    def _learn(self, obj: Objective, graph: TaskGraph, observer: Observer, ver: Dict[str, Any]) -> None:
        """Experience → memory, with honest origins, then *validated* lessons.
        Runs for failed and blocked objectives too — the outcome is recorded honestly."""
        try:
            from rad.memory import Memory, OBSERVED
            from rad.world import WorldModel
            mem = Memory(self.home)
            arts = list(observer.artifacts().values())
            summary = (f"objective '{obj.goal[:120]}' finished ({ver['status']}); "
                       f"{len(graph.tasks)} tasks, {obj.usage.retries} retries, "
                       f"{obj.usage.tool_calls} tool calls"
                       + (f"; artifacts: {', '.join(a['location'].rsplit('/', 1)[-1] for a in arts[:5])}"
                          if arts else ""))
            mem.add("episodic", summary, tags=["objective", obj.id], origin=OBSERVED, source=obj.id,
                    importance=0.6)
            by_task: Dict[str, List[Dict[str, Any]]] = {}
            for a in arts:
                by_task.setdefault(a["task_id"], []).append(a)
            wm = WorldModel(self.home)
            for tid, items in by_task.items():
                wm.learn_observation(obj.id, tid, items)
        except Exception:
            pass
        # experience learning: propose → validate against recorded episodes → promote
        try:
            from rad.experience import Experience
            exp = Experience(self.home)
            report = exp.run(obj, graph, observer=observer, verification=ver)
            self.last_run["lessons"] = report
        except Exception:
            pass

    def _final_report(self, obj: Objective, graph: TaskGraph, observer: Observer, ver: Dict[str, Any]) -> str:
        lines = [f"Objective: {obj.goal}", f"Verification: {ver['status']}"]
        if ver.get("tasks_unverified"):
            lines.append(f"Note: {len(ver['tasks_unverified'])} task(s) completed without machine verification.")
        arts = observer.artifacts()
        if arts:
            lines.append("Artifacts:")
            lines += [f"  - {a['location']} ({a.get('size', 0)} bytes, v{a['version']})"
                      for a in arts.values()]
        lines.append("Tasks:")
        for t in graph.tasks.values():
            lines.append(f"  [{t.status}] {t.text}")
        return "\n".join(lines)

    # ------------------------------------------------------------ helpers
    def _finish(self, obj: Objective, graph: TaskGraph, log: EventLog, status: str, note: str,
                observer: Optional[Observer] = None) -> Objective:
        obj.budget_status = BudgetManager(obj.budget, obj.usage, objective_id=obj.id).to_dict()
        obj.set_status(status)
        if status == ObjectiveStatus.COMPLETED:
            obj.failure = ""
            obj.result_summary = "verified complete" if (obj.verification or {}).get("objective", {}).get(
                "status") == VERIFIED else "completed (not machine-verified)"
            log.emit(E.OBJECTIVE_COMPLETED, obj.id)
        elif status == ObjectiveStatus.FAILED:
            obj.failure = note
            obj.result_summary = f"failed: {note[:200]}"
            log.emit(E.OBJECTIVE_FAILED, obj.id, reason=note)
        else:
            obj.failure = note
            obj.result_summary = f"{status}: {note[:200]}"
            log.emit(E.OBJECTIVE_STATUS, obj.id, status=status, note=note)
        self.checkpoints.save(obj, graph, f"finish {status}")
        if observer is not None:
            try:
                self._learn(obj, graph, observer, {"status": status, "note": note,
                                                   "tasks_unverified": []})
            except Exception:
                pass
        return obj

    def _checkpoint(self, obj: Objective, graph: TaskGraph, log: EventLog, note: str = "") -> None:
        cp = self.checkpoints.save(obj, graph, note)
        log.emit(E.CHECKPOINT, obj.id, status=obj.status, tasks=graph.summary(),
                 usage=obj.usage.to_dict(), seq=cp["seq"])

    def _stuck_reason(self, graph: TaskGraph) -> str:
        bad = [t for t in graph.tasks.values()
               if t.status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER)]
        return "; ".join(f"{t.status} {t.text[:60]}: {t.note[:100]}" for t in bad) or "no runnable tasks"

    def _task_prompt(self, obj: Objective, graph: TaskGraph, task: Task, hint: str) -> str:
        lines = [f"OBJECTIVE: {obj.goal}"]
        if obj.success_criteria:
            lines.append("Success criteria: " + "; ".join(obj.success_criteria))
        if obj.constraints:
            lines.append("Constraints: " + "; ".join(obj.constraints))
        done = [t for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED]
        if done:
            lines.append("Already completed: " + "; ".join(t.text[:80] for t in done))
        lines.append(f"\nCURRENT TASK: {task.text}")
        if task.agent:
            lines.append(f"This task is delegated to the specialist agent '{task.agent}'.")
        if task.checks:
            lines.append("This task will be VERIFIED by machine checks: " +
                         "; ".join(c.description or f"{c.kind} {c.args}" for c in task.checks))
        if hint:
            lines.append("\nFEEDBACK FROM PREVIOUS ATTEMPT: " + hint)
        lines.append("\nDo the actual work with your tools now. When finished end with one line "
                     "'DONE: <what was done>'. If impossible/unsafe: 'BLOCKED: <why>'. "
                     "If you need information only the user has: 'NEEDS_USER: <question>'.")
        return "\n".join(lines)


def agent_sandbox(home: RadHome, spec: Any) -> Sandbox:
    """A sandbox narrowed to an agent's capability envelope."""
    try:
        return Sandbox.for_agent(home, list(spec.caps), workspace=home.workspace(), name=spec.id)
    except Exception:
        return Sandbox(home, workspace=home.workspace(), name=getattr(spec, "id", "agent"))
