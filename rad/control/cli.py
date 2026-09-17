"""CLI surface of the control plane: rad objective … | rad trace | rad inspect | rad events."""
from __future__ import annotations

import argparse
import json
import time
from typing import Any, Dict, List

from rad.control import events as E
from rad.control.controller import Controller
from rad.control.events import EventLog
from rad.control.objectives import Budget, ObjectiveStatus
from rad.control.tasks import TaskStatus
from rad.home import RadHome
from rad.ui import col, fail, info, ok, warn

STATUS_COL = {
    "completed": col.green, "failed": col.red, "cancelled": col.dim, "needs_user": col.yellow,
    "running": col.cyan, "paused": col.yellow, "pending": col.dim, "planning": col.cyan,
    "COMPLETED": col.green, "FAILED": col.red, "CANCELLED": col.dim, "NEEDS_USER": col.yellow,
    "BLOCKED": col.red, "RUNNING": col.cyan, "RETRYING": col.yellow, "PENDING": col.dim, "READY": col.dim,
}


def _c(s: str) -> str:
    return STATUS_COL.get(s, str)(s)


def _live_printer(ev: E.Event) -> None:
    d = ev.data
    if ev.kind == E.TOOL_CALLED:
        print(col.magenta(f"      ⚙ {d.get('tool')} {json.dumps(d.get('args', {}), ensure_ascii=False)[:120]}"))
    elif ev.kind == E.TOOL_RESULT and d.get("status") != "success":
        print(col.yellow(f"      ! {d.get('tool')} → {d.get('status')}"))
    elif ev.kind == E.VERIFICATION_RESULT and ev.task_id:
        print(col.dim(f"      verify: {d.get('status')}  {d.get('summary', '')[:100]}"))
    elif ev.kind == E.REPLAN:
        print(col.yellow(f"      replanned → {len(d.get('new_tasks', []))} new task(s)"))
    elif ev.kind == E.BUDGET_EXCEEDED:
        print(col.red(f"      budget: {d.get('reason')}"))


def _print_objective(o, ctl: Controller, verbose: bool = False) -> None:
    print(f"  {col.bold(o.id)}  {_c(o.status)}  {o.goal[:90]}")
    if o.success_criteria:
        for c in o.success_criteria:
            print(f"      · {c}")
    u, b = o.usage, o.budget
    print(col.dim(f"      tools {u.tool_calls}/{b.tool_calls}  model {u.model_calls}/{b.model_calls}  "
                  f"retries {u.retries}/{b.retries}  {int(u.seconds)}s"))
    g = ctl.load_graph(o)
    for tid in g.order:
        t = g.tasks[tid]
        v = t.verification.get("status", "") if t.verification else ""
        vtag = {"VERIFIED": col.green("✔"), "FAILED": col.red("✘"), "UNVERIFIED": col.yellow("?")}.get(v, " ")
        deps = f" ← {', '.join(d[-4:] for d in t.depends_on)}" if t.depends_on else ""
        print(f"    {vtag} {_c(t.status):<22} {t.id}  {t.text[:70]}{col.dim(deps)}")
        if verbose and t.note:
            print(col.dim(f"          {t.note[:160]}"))
        if verbose and t.verification.get("summary"):
            print(col.dim(f"          {t.verification['summary'][:200]}"))
    if o.failure:
        print(col.yellow(f"    ⚠ {o.failure[:200]}"))
    ov = (o.verification or {}).get("objective")
    if ov:
        print(f"    objective verification: {_c(ov['status'])}")
        if verbose:
            for r in ov.get("results", []):
                print(col.dim(f"      {'✓' if r['ok'] else '✗'} [{r['level']}] {r['kind']}: {r['detail'][:120]}"))


# ---------------------------------------------------------------- commands

def cmd_objective(args) -> int:
    home = RadHome(args.home)
    ctl = Controller(home)
    act = args.obj_action

    if act == "create" or act == "run":
        goal = " ".join(args.obj_args).strip()
        if not goal:
            fail("usage: rad objective run <goal> [--criteria ... ] [--auto]")
            return 1
        budget = Budget()
        if args.max_tools:
            budget.tool_calls = args.max_tools
        if args.max_retries is not None:
            budget.retries = args.max_retries
        if args.minutes:
            budget.seconds = int(args.minutes * 60)
        obj = ctl.create(goal, success_criteria=args.criteria or [], constraints=args.constraint or [],
                         budget=budget, auto=args.auto)
        ok(f"objective {obj.id} created")
        if act == "create":
            return 0
        return _run(ctl, obj, args)

    if act == "list":
        items = ctl.store.list(active_only=args.active)
        if not items:
            info("  no objectives — `rad objective run <goal>`")
            return 0
        for o in items:
            when = time.strftime("%m-%d %H:%M", time.localtime(o.created))
            print(f"  {o.id}  {_c(o.status):<20} {col.dim(when)}  {o.goal[:70]}")
        return 0

    ref = (args.obj_args[0] if args.obj_args else "last")
    obj = ctl.store.resolve(ref)
    if not obj:
        fail(f"no objective matches '{ref}'")
        return 1

    if act == "inspect":
        _print_objective(obj, ctl, verbose=True)
        if obj.result:
            print(col.bold("\n  result:"))
            print("  " + obj.result.replace("\n", "\n  "))
        return 0
    if act == "resume":
        if not args.auto and obj.auto:
            args.auto = True
        ctl.on_event = _live_printer
        info(f"  resuming {obj.id} …")
        obj = ctl.resume(obj.id, max_tasks=args.max_tasks)
        _print_objective(obj, ctl)
        return 0 if obj.status == ObjectiveStatus.COMPLETED else 2
    if act == "pause":
        ctl.pause(obj.id)
        ok(f"{obj.id} paused (resume with `rad objective resume {obj.id}`)")
        return 0
    if act == "cancel":
        ctl.cancel(obj.id)
        ok(f"{obj.id} cancelled")
        return 0
    if act == "delete":
        ctl.store.delete(obj.id)
        ok(f"{obj.id} deleted")
        return 0
    fail("usage: rad objective run|create|list|inspect|resume|pause|cancel|delete")
    return 1


def _run(ctl: Controller, obj, args) -> int:
    ctl.on_event = _live_printer
    if not obj.auto:
        warn("confirm-gated: Rad will ask before each shell/write action.  (--auto = no asking)")
    obj = ctl.run(obj, max_tasks=args.max_tasks)
    print()
    _print_objective(obj, ctl)
    if obj.status == ObjectiveStatus.COMPLETED:
        ok("objective COMPLETED")
        if obj.result:
            print("  " + obj.result.replace("\n", "\n  "))
        return 0
    if obj.status == ObjectiveStatus.NEEDS_USER:
        warn(f"objective needs you: {obj.failure or 'see tasks above'}  → fix, then `rad objective resume {obj.id}`")
        return 2
    if obj.status == ObjectiveStatus.RUNNING:
        info(f"  stopped after --max-tasks; `rad objective resume {obj.id}` to continue")
        return 0
    fail(f"objective {obj.status}: {obj.failure[:200]}")
    return 1


def cmd_trace(args) -> int:
    home = RadHome(args.home)
    ctl = Controller(home)
    obj = ctl.store.resolve(args.ref or "last")
    if not obj:
        fail("no such objective")
        return 1
    log = EventLog(ctl.store.events_path(obj.id))
    t0 = None
    for ev in log.read(kind=args.kind or None, task_id=args.task or None):
        t0 = t0 or ev.at
        if args.json:
            print(ev.to_json())
            continue
        dt = f"+{ev.at - t0:7.2f}s"
        tid = col.dim(ev.task_id[-8:]) if ev.task_id else " " * 8
        d = dict(ev.data)
        summary = _summ(ev.kind, d)
        print(f"  {col.dim(dt)} {tid} {ev.kind:<22} {summary}")
    return 0


def _summ(kind: str, d: Dict[str, Any]) -> str:
    if kind == E.TOOL_CALLED:
        return f"{d.get('tool')} {json.dumps(d.get('args', {}), ensure_ascii=False)[:90]}"
    if kind == E.TOOL_RESULT:
        return f"{d.get('tool')} → {d.get('status')} ({d.get('ms')}ms)"
    if kind == E.TASK_STARTED:
        return f"attempt {d.get('attempt')}: {d.get('text', '')[:80]}"
    if kind == E.VERIFICATION_RESULT:
        return f"{d.get('status')}  {d.get('summary', '')[:100]}"
    if kind == E.RECOVERY_DECISION:
        return f"{d.get('failure_class')} → {d.get('strategy')}  {d.get('reason', '')[:80]}"
    if kind == E.CHECKPOINT:
        return f"{d.get('status')} {d.get('tasks')}"
    if kind in (E.TASK_CREATED, E.PLAN_CREATED):
        return d.get("text", d.get("source", ""))[:90] if isinstance(d.get("text", ""), str) else ""
    return json.dumps(d, ensure_ascii=False)[:110]


def cmd_events(args) -> int:
    """Tail recent events across all objectives."""
    home = RadHome(args.home)
    ctl = Controller(home)
    rows: List[E.Event] = []
    for o in ctl.store.list()[:20]:
        rows += EventLog(ctl.store.events_path(o.id)).all()
    rows.sort(key=lambda e: e.at)
    for ev in rows[-args.n:]:
        when = time.strftime("%H:%M:%S", time.localtime(ev.at))
        print(f"  {col.dim(when)} {ev.objective_id[-8:]} {ev.kind:<22} {_summ(ev.kind, ev.data)}")
    return 0


# ---------------------------------------------------------------- parser hookup

def add_parsers(sub) -> None:
    ob = sub.add_parser("objective", help="autonomous objectives: plan → execute → verify → recover")
    ob.add_argument("obj_action", choices=["run", "create", "list", "inspect", "resume", "pause", "cancel", "delete"])
    ob.add_argument("obj_args", nargs="*")
    ob.add_argument("--criteria", action="append", help="success criterion (repeatable)")
    ob.add_argument("--constraint", action="append", help="constraint (repeatable)")
    ob.add_argument("--auto", action="store_true", help="hands act without confirmation")
    ob.add_argument("--active", action="store_true", help="list: only active objectives")
    ob.add_argument("--max-tasks", type=int, default=None, help="stop after N tasks (resume later)")
    ob.add_argument("--max-tools", type=int, default=None, help="tool-call budget")
    ob.add_argument("--max-retries", type=int, default=None, help="retry budget")
    ob.add_argument("--minutes", type=float, default=None, help="time budget")
    ob.set_defaults(fn=cmd_objective)

    tr = sub.add_parser("trace", help="event trail of an objective (default: last)")
    tr.add_argument("ref", nargs="?", default="last")
    tr.add_argument("--kind", default=None); tr.add_argument("--task", default=None)
    tr.add_argument("--json", action="store_true")
    tr.set_defaults(fn=cmd_trace)

    ins = sub.add_parser("inspect", help="objective + task graph + verification (default: last)")
    ins.add_argument("ref", nargs="?", default="last")
    ins.set_defaults(fn=lambda a: cmd_objective(argparse.Namespace(
        home=a.home, obj_action="inspect", obj_args=[a.ref], criteria=None, constraint=None, auto=False,
        active=False, max_tasks=None, max_tools=None, max_retries=None, minutes=None)))

    evp = sub.add_parser("events", help="recent control-plane events across objectives")
    evp.add_argument("-n", type=int, default=40)
    evp.set_defaults(fn=cmd_events)
