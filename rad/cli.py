"""The face — `rad`, the door. Every command from the spec lives here."""
from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from rad import __version__
from rad.home import RadHome, mask
from rad.ui import col, fail, info, ok, warn

from rad import providers as P


# ---------------------------------------------------------------- helpers

def _home(args) -> RadHome:
    return RadHome(getattr(args, "home", None))


def _router(home: RadHome):
    from rad.router import RouterState
    return RouterState(home)


def _llm(home: RadHome, prompt: str) -> str:
    r = _router(home)
    return r.chat([{"role": "user", "content": prompt}], stream_cb=None).text


# ---------------------------------------------------------------- commands

def cmd_chat(args) -> int:
    from rad.session import repl
    home = _home(args)
    if args.workspace:
        home.update(workspace=str(Path(args.workspace).expanduser()))
    if args.use:
        home.update(force_provider=args.use)
    if args.free_lock:
        home.update(free_lock=True)
    if args.model:
        home.update(model=args.model)
    if args.auto:
        home.update(auto=True)
    repl(home, auto=home.cfg.get("auto", False), voice=args.voice)
    return 0


def cmd_keys(args) -> int:
    home = _home(args)
    if args.keys_action == "add":
        if not args.key or not args.provider:
            fail("usage: rad keys add <provider> <key>")
            return 1
        known = [s.name for s in P.all_specs(home)]
        if args.provider not in known:
            warn(f"'{args.provider}' is not a built-in provider — storing anyway (usable via custom endpoints)")
        home.vault_set(args.provider, args.key)
        ok(f"key for {args.provider} stored in encrypted vault ({mask(args.key)})")
        return 0
    if args.keys_action == "rm":
        home.vault_remove(args.provider)
        ok(f"removed {args.provider} key from vault")
        return 0
    # list
    lines = []
    vault = home.vault_get_all()
    for spec in P.all_specs(home):
        if spec.local:
            reachable, models = P.probe_local(spec)
            lines.append(f"  {spec.name:<10} local   " + (col.green("running") if reachable else col.dim("not running"))
                         + (f"  {col.dim(', '.join(models[:4]))}" if models else ""))
            continue
        key = P.find_key(home, spec)
        if key:
            where = "vault" if key in vault.values() else "env/.env"
            lines.append(f"  {spec.name:<10} {where:<7} {mask(key)}")
        else:
            lines.append(f"  {spec.name:<10} {col.dim('no key')}")
    print(col.bold("Keys (auto-fetched from vault → env → .env):"))
    print("\n".join(lines))
    try:
        import cryptography  # noqa: F401
        info("  vault encryption: Fernet ✓")
    except ImportError:
        warn("  vault encryption: NOT available (pip install cryptography — `rad install vault`)")
    return 0


def cmd_providers(args) -> int:
    home = _home(args)
    r = _router(home)
    print(col.bold("Providers — brain socket:"))
    print(r.describe())
    return 0


def cmd_use(args) -> int:
    home = _home(args)
    home.update(force_provider=args.provider)
    ok(f"pinned provider: {args.provider}")
    return 0


def cmd_cost(args) -> int:
    print(col.bold("Paid spend (free/local never appears here):"))
    print(_router(_home(args)).cost_report())
    return 0


def cmd_see(args) -> int:
    from rad.tools import see_image
    home = _home(args)
    r = _router(home)
    out = see_image(args.image, " ".join(args.question or []), r, home)
    print(out)
    return 0


def cmd_browse(args) -> int:
    from rad.tools import fetch_public_page
    text, err = fetch_public_page(args.url, max_chars=args.chars or 8000)
    if err:
        fail(err)
        return 1
    print(text)
    return 0


def cmd_search(args) -> int:
    from rad.tools import search_web
    for i, r in enumerate(search_web(args.query, n=args.n), 1):
        print(f"{i}. {col.bold(r['title'])}")
        print(f"   {col.cyan(r['url'])}")
        if r["snippet"]:
            print(f"   {col.dim(r['snippet'][:200])}")
    return 0


def cmd_remember(args) -> int:
    from rad.memory import Memory
    home = _home(args)
    e = Memory(home).add(args.layer, " ".join(args.text), tags=["cli"])
    ok("stored in long-term memory" if e else "already in memory (duplicates are strengthened, not duplicated)")
    return 0


def cmd_recall(args) -> int:
    from rad.memory import Memory
    home = _home(args)
    found = Memory(home).recall(" ".join(args.query), k=args.n)
    if not found:
        info("nothing in memory matches")
        return 0
    for e in found:
        print(f"  [{e.layer}] {col.dim(f's={e.strength:.2f}')} {e.text}")
    return 0


def cmd_sleep(args) -> int:
    from rad.sleep import run_sleep
    home = _home(args)
    info("  rad is sleeping… (consolidating memory)")
    report = run_sleep(home, _router(home), sync_drive=not args.no_sync)
    ok(f"sleep done: +{report.get('added', 0)} long-term, {report.get('faded', 0)} faded, {report.get('archived', 0)} archived")
    return 0


def cmd_memory(args) -> int:
    from rad.memory import Memory
    home = _home(args)
    m = Memory(home)
    if args.memory_action == "prune":
        faded, archived = m.decay_and_archive()
        ok(f"pruned: {faded} faded in place, {archived} archived")
        return 0
    print(col.bold("Memory layers:"))
    print(m.show())
    return 0


def cmd_evolve(args) -> int:
    from rad.dna import Evolver
    home = _home(args)
    direction = " ".join(args.direction) if args.direction else ""
    if not direction:
        fail("usage: rad evolve <direction>   e.g.  rad evolve reply shorter and more casual")
        return 1
    r = _router(home)
    llm = (lambda p: _llm(home, p)) if r.build_chain() else None
    if llm is None:
        info("  (no brain online — using deterministic evolution)")
    try:
        dna = Evolver(home).evolve(direction, llm=llm)
        ok(f"evolved → generation {dna['generation']}")
    except Exception as e:
        fail(str(e))
        return 1
    return 0


def cmd_dna(args) -> int:
    from rad.dna import Evolver
    home = _home(args)
    ev = Evolver(home)
    if args.dna_action == "show":
        print(col.bold("DNA — who Rad is:"))
        print(ev.show())
    elif args.dna_action == "rollback":
        dna = ev.rollback()
        if dna:
            ok(f"rolled back to generation {dna['generation']}")
        else:
            info("nothing to roll back (only one generation)")
    elif args.dna_action == "reset":
        dna = ev.reset()
        ok(f"factory reset → generation {dna['generation']}")
    return 0


def cmd_connect(args) -> int:
    from rad import mcp
    from rad.ui import ask
    home = _home(args)
    info(f"  connecting to: {args.link}  (self-building — this can take a minute)")
    done, msg, entry = mcp.connect(home, args.link, yes=args.yes, confirm=ask)
    if done:
        ok(msg)
    else:
        fail(msg)
        return 1
    return 0


def cmd_skills(args) -> int:
    home = _home(args)
    reg = home.skills()
    if not reg:
        info("no skills connected yet — `rad connect <link>`")
        return 0
    for name, e in reg.items():
        print(f"  • {col.bold(name)}  {col.dim(e.get('transport', 'stdio'))}")
        for t in e.get("tools", []):
            print(f"      {t['name']:<32} {col.dim((t.get('description') or '')[:80])}")
    return 0


def cmd_drop(args) -> int:
    from rad import mcp
    home = _home(args)
    if mcp.drop(home, args.name):
        ok(f"dropped skill '{args.name}'")
    else:
        fail(f"no skill named '{args.name}'")
        return 1
    return 0


def cmd_drive(args) -> int:
    from rad.drive import Drive
    home = _home(args)
    d = Drive(home)
    if args.drive_action == "connect":
        d.connect(args.client_id, args.client_secret)
    elif args.drive_action == "push":
        print(d.push())
    elif args.drive_action == "pull":
        print(d.pull())
    else:
        print(d.status())
    return 0


def cmd_remind(args) -> int:
    from rad import jobs
    home = _home(args)
    # greedy split: consume as many leading tokens as still parse as a time
    tokens = list(args.when) + list(args.task)
    when_str, task_tokens = None, None
    for i in range(1, len(tokens) + 1):
        candidate = " ".join(tokens[:i])
        if jobs.parse_when(candidate) is not None:
            when_str, task_tokens = candidate, tokens[i:]
            break
    if when_str is None or not task_tokens:
        fail("could not split when/task — use: rad remind <in 5m | 2h | tomorrow 9am | 14:30> <task>")
        return 1
    when = jobs.parse_when(when_str)
    task = " ".join(task_tokens)
    job = jobs.add_job(home, "note", when, task)
    ok(f"reminder set [{job['id']}] at {time.strftime('%Y-%m-%d %H:%M', time.localtime(when))} — {task}")
    return 0


def cmd_watch(args) -> int:
    from rad import jobs
    home = _home(args)
    job = jobs.add_job(home, "watch", time.time(), task=f"watch {args.url}", url=args.url,
                       every_min=args.every or home.cfg.get("watch_every_min", 30))
    ok(f"watching [{job['id']}] {args.url} every {job['every_min']} min — changes land in notifications.md")
    return 0


def cmd_jobs(args) -> int:
    from rad import jobs
    home = _home(args)
    if args.cancel:
        if jobs.cancel_job(home, args.cancel):
            ok(f"cancelled {args.cancel}")
        else:
            fail(f"no active job {args.cancel}")
            return 1
        return 0
    print(col.bold("Pending jobs:"))
    print(jobs.list_jobs(home))
    return 0


def cmd_watcher(args) -> int:
    """Detached loop — spawned by the scheduler, not meant for humans."""
    from rad import jobs
    home = _home(args)
    jobs.run_watcher(home, args.job_id)
    return 0


def cmd_say(args) -> int:
    from rad import voice as V
    home = _home(args)
    note = V.speak(" ".join(args.text), home)
    if note:
        print(col.dim(note))
    return 0


def cmd_listen(args) -> int:
    from rad import voice as V
    home = _home(args)
    text = V.listen(home, seconds=args.seconds or 10)
    if text:
        print(text)
    return 0 if text else 1


def cmd_models(args) -> int:
    home = _home(args)
    print(col.bold("Local engines (brain socket):"))
    for spec in P.all_specs(home):
        if not spec.local:
            continue
        ok_up, models = P.probe_local(spec)
        if ok_up:
            print(f"  {col.green(spec.name + ':')}  {', '.join(models[:8]) or '(models hidden)'}")
        else:
            print(f"  {col.dim(spec.name + ': not running')}  {col.dim(spec.desc)}")
    info("  (cloud models: `rad providers` — use --model <name> to pin one)")
    return 0


def cmd_provider_add(args) -> int:
    home = _home(args)
    customs = home.cfg.get("custom_providers", []) or []
    customs = [c for c in customs if c.get("name") != args.name]
    customs.append({"name": args.name, "url": args.url, "key": args.key,
                    "tier": args.tier, "model": args.model or ""})
    home.update(custom_providers=customs)
    ok(f"custom provider '{args.name}' added (open door: any OpenAI-compatible endpoint)")
    return 0


def cmd_workspace(args) -> int:
    home = _home(args)
    if args.path:
        home.update(workspace=str(Path(args.path).expanduser()))
        ok(f"workspace → {home.workspace()}")
    else:
        print(f"  {home.workspace()}")
    return 0


def cmd_install(args) -> int:
    home = _home(args)
    kind = args.thing
    if kind == "edge0":
        if not (sys.platform == "darwin" and platform.machine() in ("arm64", "Apple")):
            if os.name == "nt":
                fail("Edge0 is Apple Silicon (MLX) only — on Windows your local engine is Ollama or LM Studio: "
                     "winget install Ollama.Ollama  (uses your NVIDIA GPU automatically), "
                     "then `ollama serve` and pull a model (e.g. `ollama pull llama3.2:3b`). "
                     "Rad auto-detects it. Or skip local entirely — NIM/Groq free tiers work out of the box.")
            else:
                fail("Edge0 runs on Apple Silicon (MLX) only. On this machine Rad will use Ollama/LM Studio "
                     "as local engine — `brew install ollama && ollama serve`, or start a cloud key instead.")
            return 1
        dest = home.root / "edge0"
        if not dest.exists():
            ok("cloning Edge0…")
            subprocess.run(["git", "clone", "--depth", "1", "https://github.com/Edge0-AI/Edge0.git", str(dest)],
                           check=True, timeout=600)
        info(f"  installed at {dest}")
        info("  next:  cd " + str(dest) + " && pip install -e .   then follow its README to fetch the "
             + f"edge0-{home.cfg.get('edge0_tier', '10b')} model")
        info("  Rad will auto-detect it at " + str(home.cfg.get('edge0_url')))
        return 0
    mapping = {
        "vault": ["cryptography"],
        "cloud": ["google-auth", "google-auth-oauthlib", "google-api-python-client"],
        "voice": ["faster-whisper", "sounddevice", "piper-tts"],
        "dev": ["pytest"],
    }
    if kind not in mapping:
        fail(f"unknown install target '{kind}' (choose: {', '.join(mapping)} | edge0)")
        return 1
    ok(f"installing: {', '.join(mapping[kind])}")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", *mapping[kind]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(r.stderr.strip()[-500:])
        return 1
    ok(f"{kind} ready")
    return 0


def cmd_version(args) -> int:
    print(f"rad v{__version__}")
    return 0


# ---------------------------------------------------------------- parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rad", description="Rad — open, self-evolving, free-first AI agent")
    p.add_argument("--home", help="RAD_HOME override (default ~/.rad)", default=None)
    sub = p.add_subparsers(dest="cmd")

    # chat (default)
    c = sub.add_parser("chat", help="talk to Rad (default)")
    c.add_argument("--voice", action="store_true", help="voice mode: speak + listen")
    c.add_argument("--auto", action="store_true", help="hands act without confirmation")
    c.add_argument("--use", help="pin a provider")
    c.add_argument("--free-lock", action="store_true", help="paid providers impossible")
    c.add_argument("--model", help="pin a model name")
    c.add_argument("--workspace", help="where hands work")
    c.set_defaults(fn=cmd_chat)

    k = sub.add_parser("keys", help="API key vault")
    ksub = k.add_subparsers(dest="keys_action")
    ka = ksub.add_parser("add"); ka.add_argument("provider"); ka.add_argument("key")
    kr = ksub.add_parser("rm"); kr.add_argument("provider")
    ksub.add_parser("list")
    k.set_defaults(fn=cmd_keys, keys_action="list")

    pr = sub.add_parser("providers", help="show detected providers + chain"); pr.set_defaults(fn=cmd_providers)
    u = sub.add_parser("use", help="pin a provider"); u.add_argument("provider"); u.set_defaults(fn=cmd_use)
    co = sub.add_parser("cost", help="paid spend so far"); co.set_defaults(fn=cmd_cost)

    se = sub.add_parser("see", help="vision: look at an image")
    se.add_argument("image"); se.add_argument("question", nargs="*"); se.set_defaults(fn=cmd_see)

    br = sub.add_parser("browse", help="scrape a public page")
    br.add_argument("url"); br.add_argument("--chars", type=int, default=None)
    br.set_defaults(fn=cmd_browse)

    s = sub.add_parser("search", help="search the public web")
    s.add_argument("query"); s.add_argument("-n", type=int, default=5)
    s.set_defaults(fn=cmd_search)

    rm = sub.add_parser("remember", help="pin a fact to long-term memory")
    rm.add_argument("text", nargs="+"); rm.add_argument("--layer", default="semantic",
                                                          choices=["episodic", "semantic", "procedural"])
    rm.set_defaults(fn=cmd_remember)

    rc = sub.add_parser("recall", help="search long-term memory")
    rc.add_argument("query", nargs="+"); rc.add_argument("-n", type=int, default=5)
    rc.set_defaults(fn=cmd_recall)

    sl = sub.add_parser("sleep", help="consolidate memory now")
    sl.add_argument("--no-sync", action="store_true")
    sl.set_defaults(fn=cmd_sleep)

    me = sub.add_parser("memory", help="memory layers")
    me.add_argument("memory_action", nargs="?", default="show", choices=["show", "prune"])
    me.set_defaults(fn=cmd_memory)

    ev = sub.add_parser("evolve", help="directed evolution: rad evolve <direction>")
    ev.add_argument("direction", nargs="*")
    ev.set_defaults(fn=cmd_evolve)

    dn = sub.add_parser("dna", help="Rad's identity")
    dn.add_argument("dna_action", nargs="?", default="show", choices=["show", "rollback", "reset"])
    dn.set_defaults(fn=cmd_dna)

    cn = sub.add_parser("connect", help="self-build + connect any MCP skill from a link")
    cn.add_argument("link"); cn.add_argument("--yes", action="store_true",
                                          help="skip tool-list approval")
    cn.set_defaults(fn=cmd_connect)

    sk = sub.add_parser("skills", help="list connected skills"); sk.set_defaults(fn=cmd_skills)
    dp = sub.add_parser("drop", help="disconnect a skill"); dp.add_argument("name"); dp.set_defaults(fn=cmd_drop)

    dv = sub.add_parser("drive", help="Google Drive cloud mind")
    dvsub = dv.add_subparsers(dest="drive_action")
    dvc = dvsub.add_parser("connect"); dvc.add_argument("--client-id"); dvc.add_argument("--client-secret")
    dvsub.add_parser("push"); dvsub.add_parser("pull")
    dv.set_defaults(fn=cmd_drive, drive_action="status")

    re_ = sub.add_parser("remind", help="rad remind <in 5m | 2h | tomorrow 9am | 14:30> <task>")
    re_.add_argument("when", nargs="+"); re_.add_argument("task", nargs="*")
    re_.set_defaults(fn=cmd_remind)

    wt = sub.add_parser("watch", help="watch a public page for changes")
    wt.add_argument("url"); wt.add_argument("--every", type=int, default=0)
    wt.set_defaults(fn=cmd_watch)

    jb = sub.add_parser("jobs", help="list/cancel jobs")
    jb.add_argument("cancel", nargs="?", default=None)
    jb.set_defaults(fn=cmd_jobs)

    wh = sub.add_parser("watcher", help=argparse.SUPPRESS)
    wh.add_argument("job_id")
    wh.set_defaults(fn=cmd_watcher)

    sy = sub.add_parser("say", help="speak text (TTS)"); sy.add_argument("text", nargs="+"); sy.set_defaults(fn=cmd_say)
    ls = sub.add_parser("listen", help="record + transcribe mic"); ls.add_argument("--seconds", type=int, default=None)
    ls.set_defaults(fn=cmd_listen)

    mo = sub.add_parser("models", help="local engine models"); mo.set_defaults(fn=cmd_models)

    pa = sub.add_parser("provider", help="custom providers (open door)")
    psub = pa.add_subparsers(dest="provider_action")
    padd = psub.add_parser("add")
    padd.add_argument("name"); padd.add_argument("url")
    padd.add_argument("--key", default=None); padd.add_argument("--tier", default="paid",
                                                                choices=["local", "free", "paid"])
    padd.add_argument("--model", default=None)
    pa.set_defaults(fn=cmd_provider_add)

    ws = sub.add_parser("workspace", help="show/set the hands workspace")
    ws.add_argument("path", nargs="?", default=None)
    ws.set_defaults(fn=cmd_workspace)

    ins = sub.add_parser("install", help="install optional parts")
    ins.add_argument("thing", choices=["vault", "cloud", "voice", "dev", "edge0"])
    ins.set_defaults(fn=cmd_install)

    v = sub.add_parser("version", help="version"); v.set_defaults(fn=cmd_version)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    choices = set(parser._subparsers._group_actions[0].choices)
    # no subcommand (or a chat flag first) → chat
    if not argv or (argv[0] not in choices and argv[0] not in ("-h", "--help")):
        if argv and argv[0] == "--home":
            idx = argv.index("--home")
            argv = argv[:idx] + ["chat"] + argv[idx:]
        else:
            argv = ["chat"] + argv
    args = parser.parse_args(argv)
    if not getattr(args, "fn", None):
        parser.print_help()
        return 0
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        print()
        return 130
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
