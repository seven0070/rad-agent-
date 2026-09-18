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


def cmd_replay(args) -> int:
    from rad.control.replay import Replay
    home = RadHome(args.home)
    ctl = Controller(home)
    obj = ctl.store.resolve(args.ref or "last")
    if not obj:
        fail("no such objective")
        return 1
    rp = Replay(ctl.store, obj.id, home.workspace())
    if args.json:
        print(json.dumps({"timeline": rp.timeline(), "reverify": rp.reverify() if args.verify else None},
                         ensure_ascii=False, indent=2, default=str))
        return 0
    print(f"  {col.bold(obj.id)}  {_c(obj.status)}  {obj.goal[:90]}\n")
    for step in rp.timeline():
        print(f"  ▶ {col.cyan(step['text'][:80])}  {col.dim('attempt ' + str(step['attempt']) + ' · ' + (step['provider'] or '?'))}")
        if args.prompts:
            print(col.dim("    prompt: " + step["prompt"][:600].replace("\n", "\n            ")))
        for t in step["tools"]:
            st = t["status"] or "?"
            mark = col.green("✓") if st == "success" else col.red("✗")
            print(f"    {mark} {t['tool']} {json.dumps(t['args'], ensure_ascii=False)[:100]}  {col.dim(str(t['ms']) + 'ms')}")
        if step["error"]:
            print(col.red(f"    error: {step['error'][:160]}"))
        elif step["reply"]:
            print("    reply: " + step["reply"].strip().replace("\n", " ")[:200])
        if step["verification"]:
            print(f"    verify: {_c(step['verification']['status'])}  {col.dim(step['verification']['summary'][:120])}")
        if step["recovery"]:
            r = step["recovery"]
            print(col.yellow(f"    recover: {r['class']} → {r['strategy']}  {r['reason'][:100]}"))
        print()
    if args.verify:
        rep = rp.reverify()
        print(col.bold("  re-verification against current workspace:"))
        for t in rep["tasks"]:
            flag = "" if t["recorded"] == t["now"] else col.yellow("  (drift)")
            print(f"    {_c(t['now']):<20} was {t['recorded'] or '-':<11} {t['text'][:70]}{flag}")
        print(f"    objective now: {_c(rep['objective_now'])}")
        if rep["drift"]:
            warn(f"  {len(rep['drift'])} task(s) verified at run time no longer pass — the world changed")
    return 0


def cmd_why(args) -> int:
    from rad.control.provenance import Provenance
    home = RadHome(args.home)
    ctl = Controller(home)
    obj = ctl.store.resolve(args.objective or "last")
    if not obj:
        fail("no such objective")
        return 1
    pv = Provenance(ctl.store.dir(obj.id))
    q = " ".join(args.query).strip()
    if not q:
        fail("usage: rad why <claim or artifact path> [--objective id]")
        return 1
    art = pv.artifact(q)
    if art:
        a = art["artifact"]
        print(f"  {col.bold(a['location'])}  v{a['version']}  {a.get('size', 0)}B  sha256 {a['sha256'][:12]}…")
        print(f"    created by {col.magenta(a['creator'])} in task {art['task']['id']} "
              f"(attempt {art['task']['attempt']}): {art['task']['text'][:70]}")
        if art["action"]:
            print(f"    action {art['action']['action_id']}: {json.dumps(art['action']['args'], ensure_ascii=False)[:140]}")
        if len(art["versions"]) > 1:
            print("    lineage: " + " ← ".join(f"v{v['version']}({v['sha256'][:8]})" for v in art["versions"]))
        if art["verification"]:
            print(f"    verification: {'✓' if art['verification'].get('ok') else '✗'} {art['verification'].get('detail', '')[:80]}")
        ev = art["evidence"]
        print(f"    evidence consulted before creation: {len(ev)}")
        for e in ev[:8]:
            trust = col.green("trusted") if e.get("trusted") else col.yellow("untrusted-web")
            print(f"      - [{trust}] {e['tool']} {str(e['source'])[:90]}")
        return 0
    res = pv.why(q)
    print(f"  claim: {col.bold(q)}\n  verdict: {_c(res['verdict'].upper()) if res['verdict'] != 'weak' else col.yellow('WEAK')}")
    if not res["support"]:
        info("  no recorded observation supports this — RAD has no evidence for it")
        return 0
    for s_ in res["support"]:
        trust = col.green("trusted") if s_["trusted"] else col.yellow("untrusted-web")
        print(f"    {s_['score']:.2f} [{trust}] {s_['tool']} {s_['source'][:80]}  {col.dim(s_['observation'])}")
        print(col.dim(f"         …{s_['excerpt'][:200]}…"))
    return 0


def cmd_agents(args) -> int:
    from rad.agents import ALL_CAPS, AgentRegistry, AgentRuntime, Blackboard
    home = RadHome(args.home)
    reg = AgentRegistry(home)
    a = args.agents_action
    if a == "list":
        for aid, sp in reg.all().items():
            flag = "" if sp.enabled else col.dim(" (disabled)")
            print(f"  {col.bold(aid):<14} caps: {', '.join(sp.caps):<40} budget: {sp.budget_tool_calls} tools/{sp.budget_seconds}s"
                  f"{('  model: ' + sp.model) if sp.model else ''}{flag}")
        return 0
    if a == "define":
        if not args.agents_args:
            fail("usage: rad agents define <id> [--caps fs.read,web] [--prompt …] [--model m] [--provider p] [--tools N] [--seconds S]")
            return 1
        caps = args.caps.split(",") if args.caps else None
        try:
            sp = reg.define(args.agents_args[0], caps=caps, prompt=args.prompt, model=args.model, provider=args.provider,
                            budget_tool_calls=args.tools, budget_seconds=args.seconds, role=args.agents_args[0])
        except ValueError as e:
            fail(str(e)); return 1
        ok(f"agent {sp.id}: caps {', '.join(sp.caps)}")
        return 0
    if a == "remove":
        return 0 if (args.agents_args and reg.remove(args.agents_args[0])) else (fail("no such custom agent") or 1)
    if a == "run":
        if len(args.agents_args) < 2:
            fail("usage: rad agents run <id> <task…>")
            return 1
        rt = AgentRuntime(home, auto=args.auto or bool(home.cfg.get("auto")))
        run = rt.run_agent(args.agents_args[0], " ".join(args.agents_args[1:]))
        print(f"  [{run.status}] {run.agent}  {run.tool_calls} tool calls" + (f"  denied: {run.denied}" if run.denied else ""))
        print("  " + (run.output or "").replace("\n", "\n  ")[:3000])
        return 0 if run.status == "done" else 1
    if a == "runs":
        for r in reg.runs(n=args.n):
            when = time.strftime("%m-%d %H:%M", time.localtime(r["started"]))
            print(f"  {col.dim(when)} {r['id']} {r['agent']:<11} {_c(r['status']) if r['status'] in STATUS_COL else r['status']:<8} "
                  f"{r['tool_calls']:>2} tools  {r['input'][:60]}")
        return 0
    if a == "caps":
        print("  " + "\n  ".join(ALL_CAPS))
        return 0
    if a == "board":
        scope = args.agents_args[0] if args.agents_args else "last"
        if scope == "last":
            o = Controller(home).store.resolve("last")
            scope = o.id if o else scope
        for n_ in Blackboard(home, scope).notes():
            print(f"  [{n_['author']}/{n_['kind']}] {n_['text'][:200]}" + (f"  ← {n_['evidence']}" if n_["evidence"] else ""))
        return 0
    return 1


def cmd_policy(args) -> int:
    from rad.policy import Policy
    home = RadHome(args.home)
    pol = Policy(home)
    a = args.policy_action
    if a == "show":
        print(pol.explain()); return 0
    if a == "allow" or a == "deny" or a == "ask" or a == "limit":
        if len(args.policy_args) < 1:
            fail(f"usage: rad policy {a} <capability> [glob] [--limits '{{json}}'] [--note …]"); return 1
        cap = args.policy_args[0]; match = args.policy_args[1] if len(args.policy_args) > 1 else "*"
        try:
            limits = json.loads(args.limits) if args.limits else {}
            r = pol.add_rule(cap, {"allow": "ALLOW", "deny": "DENY", "ask": "ASK", "limit": "LIMITED"}[a], match, limits, args.note or "")
        except (ValueError, json.JSONDecodeError) as e:
            fail(str(e)); return 1
        ok(f"rule added: {r.capability} {r.effect} match={r.match!r}"); return 0
    if a == "default":
        if len(args.policy_args) != 2:
            fail("usage: rad policy default <capability> <ALLOW|ASK|DENY|LIMITED>"); return 1
        try:
            pol.set_default(args.policy_args[0], args.policy_args[1])
        except ValueError as e:
            fail(str(e)); return 1
        ok("default set"); return 0
    if a == "rm":
        try:
            idx = int(args.policy_args[0])
        except (IndexError, ValueError):
            fail("usage: rad policy rm <rule#>"); return 1
        return 0 if pol.remove_rule(idx) else (fail("no such rule") or 1)
    if a == "web-allow":
        pol._data["web_allow"] = [d.strip().lower() for d in args.policy_args if d.strip()]
        pol.save(); ok(f"web_allow = {pol._data['web_allow'] or '(any public host)'}"); return 0
    if a == "reset":
        pol.reset(); ok("policy reset to built-in defaults"); return 0
    if a == "test":
        if len(args.policy_args) < 2:
            fail("usage: rad policy test <capability> <resource…>"); return 1
        cap = args.policy_args[0]; res = " ".join(args.policy_args[1:])
        from pathlib import Path as _P
        d = pol.decide(cap, res, auto=args.auto, path=_P(res) if cap.startswith("fs.") else None,
                       tool="fetch_page" if cap == "web" else "")
        print(f"  {d.effect}  ({d.by}: {d.reason})" + (f"  limits={d.limits}" if d.limits else ""))
        return 0
    return 1


def cmd_audit(args) -> int:
    from rad.policy import Policy
    home = RadHome(args.home)
    for r in reversed(Policy(home).audit_tail(args.n, effect=args.effect)):
        when = time.strftime("%m-%d %H:%M:%S", time.localtime(r["at"]))
        eff = r["effect"]
        c = col.red if eff in ("DENY", "HARD_DENY") else (col.yellow if eff in ("ASK", "LIMITED") else col.green)
        print(f"  {col.dim(when)} {c(eff):<18} {r['cap']:<12} {r.get('actor',''):<16} {r['tool']:<12} {r['resource'][:60]}  {col.dim(r['reason'] + ' → ' + r['outcome'])}")
    return 0


def cmd_lab(args) -> int:
    from rad.lab import Lab, SUITES, scenarios
    home = RadHome(args.home)
    lab = Lab(home)
    a = args.lab_action
    if a == "list":
        for sc in scenarios(args.suite or "all"):
            print(f"  {sc.suite:<11} {sc.id:<20} expect={sc.expect_status:<10} {sc.goal[:70]}")
        return 0
    if a == "run":
        suite = args.suite or "smoke"
        if suite == "bank":
            suite = "banks"
        from rad import lab_banks
        offline = suite.startswith("bank:") or suite in ("banks", "everything")
        if not offline and suite not in SUITES:
            fail(f"suite must be one of {sorted(SUITES)} or bank | bank:<category> "
                 f"({', '.join(lab_banks.CATEGORIES)}) / banks / everything"); return 1
        from rad.router import RouterState
        if not offline and not RouterState(home).build_chain():
            fail("no brain available — add a key or start a local engine "
                 "(the bank:* suites are offline and need no brain)"); return 1
        info(f"  running lab suite '{suite}' through the control plane (isolated home + workspace per scenario)…")
        def prog(r):
            mark = col.green("PASS") if r.success else col.red("FAIL")
            print(f"    {mark} {r.id:<26} {r.status:<10} verified={r.verified or '-'} "
                  f"tools={r.usage.get('tool_calls', 0)} {r.seconds}s"
                  + ("" if r.success else "  " + r.trajectory_detail[:60]))
        rep = lab.run(suite, ids=args.ids or None, label=args.label or "", keep=args.keep,
                      progress=prog, sample=args.sample or 0, seed=args.seed)
        print(Lab.render(rep))
        return 0
    if a == "history":
        for r in lab.history(args.n):
            when = time.strftime("%m-%d %H:%M", time.localtime(r["at"]))
            print(f"  {col.dim(when)} {r['label']:<22} {r['suite']:<11} score={r['score']:<5} safety={r['safety']} honesty={r['honesty']} n={r['n']}")
        return 0
    if a == "show":
        r = lab.find(args.lab_args[0]) if args.lab_args else (lab.history(1) or [None])[0]
        if not r:
            fail("no such run"); return 1
        print(Lab.render(r)); return 0
    if a == "compare":
        if len(args.lab_args) != 2:
            fail("usage: rad lab compare <base-label> <cand-label>"); return 1
        b, c = lab.find(args.lab_args[0]), lab.find(args.lab_args[1])
        if not b or not c:
            fail("run label not found (see rad lab history)"); return 1
        cmp = Lab.compare(b, c)
        print(json.dumps(cmp, indent=2))
        g = Lab.gate(b, c)
        print(("  " + col.green("GATE PASS")) if g["pass"] else ("  " + col.red("GATE FAIL") + ": " + "; ".join(g["reasons"])))
        return 0 if g["pass"] else 2
    return 1


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

    rp = sub.add_parser("replay", help="replay an objective: prompts, tool calls, results; --verify re-checks now")
    rp.add_argument("ref", nargs="?", default="last")
    rp.add_argument("--verify", action="store_true"); rp.add_argument("--prompts", action="store_true")
    rp.add_argument("--json", action="store_true")
    rp.set_defaults(fn=cmd_replay)

    wy = sub.add_parser("why", help="provenance: rad why <claim | artifact path>")
    wy.add_argument("query", nargs="*"); wy.add_argument("--objective", default=None)
    wy.set_defaults(fn=cmd_why)

    ag = sub.add_parser("agents", help="scoped sub-agents: registry, capabilities, runs, blackboard")
    ag.add_argument("agents_action", nargs="?", default="list",
                    choices=["list", "define", "remove", "run", "runs", "caps", "board"])
    ag.add_argument("agents_args", nargs="*")
    ag.add_argument("--caps", default=None); ag.add_argument("--prompt", default=None)
    ag.add_argument("--model", default=None); ag.add_argument("--provider", default=None)
    ag.add_argument("--tools", type=int, default=None); ag.add_argument("--seconds", type=int, default=None)
    ag.add_argument("--auto", action="store_true"); ag.add_argument("-n", type=int, default=30)
    ag.set_defaults(fn=cmd_agents)

    pp = sub.add_parser("policy", help="capability permissions: show/allow/ask/deny/limit/default/test")
    pp.add_argument("policy_action", nargs="?", default="show",
                    choices=["show", "allow", "ask", "deny", "limit", "default", "rm", "web-allow", "reset", "test"])
    pp.add_argument("policy_args", nargs="*")
    pp.add_argument("--limits", default=None, help='JSON, e.g. \'{"timeout": 30, "max_bytes": 20000}\'')
    pp.add_argument("--note", default=None); pp.add_argument("--auto", action="store_true")
    pp.set_defaults(fn=cmd_policy)

    au = sub.add_parser("audit", help="permission decisions log")
    au.add_argument("-n", type=int, default=40); au.add_argument("--effect", default=None)
    au.set_defaults(fn=cmd_audit)

    lb = sub.add_parser("lab", help="agent benchmark lab: whole objectives through the control plane, graded on disk")
    lb.add_argument("lab_action", nargs="?", default="list", choices=["list", "run", "history", "show", "compare"])
    lb.add_argument("lab_args", nargs="*")
    lb.add_argument("--suite", default=None,
                    help="smoke | long | adversarial | all | bank | bank:<reasoning|tool_use|coding|"
                         "research|planning|long_horizon|recovery|memory|adversarial> | banks | everything")
    lb.add_argument("--ids", nargs="*", default=None); lb.add_argument("--label", default=None)
    lb.add_argument("--keep", action="store_true", help="keep temp homes/workspaces for inspection")
    lb.add_argument("--sample", type=int, default=0, help="run only N scenarios (deterministic)")
    lb.add_argument("--seed", type=int, default=20260917, help="sampling seed")
    lb.add_argument("-n", type=int, default=20)
    lb.set_defaults(fn=cmd_lab)

    evp = sub.add_parser("events", help="recent control-plane events across objectives")
    evp.add_argument("-n", type=int, default=40)
    evp.set_defaults(fn=cmd_events)
