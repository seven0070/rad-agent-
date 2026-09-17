"""The face — `rad`, the door. Every command from the spec lives here."""
from __future__ import annotations

import argparse
import json
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
    from rad.memory import USER_PROVIDED
    e = Memory(home).add(args.layer, " ".join(args.text), tags=["cli"], origin=USER_PROVIDED,
                         source="cli:remember", importance=0.8)
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
    if args.memory_action == "conflicts":
        cons = m.contradictions()
        if not cons:
            info("  no contradictions in memory")
            return 0
        for a, b in cons:
            print(f"  {col.yellow('⚡')} {a.id} [{a.origin.lower()} c={a.confidence:.2f} {a.verification.lower()}] {a.text[:80]}")
            print(f"     vs {b.id} [{b.origin.lower()} c={b.confidence:.2f} {b.verification.lower()}] {b.text[:80]}")
        info("  resolve: rad memory verify <id> | rad memory forget <id> | rad memory correct <id> <new text>")
        return 0
    if args.memory_action in ("forget", "verify", "correct", "dispute"):
        if not args.memory_args:
            fail(f"usage: rad memory {args.memory_action} <id> [text]")
            return 1
        mid = args.memory_args[0]
        if args.memory_action == "forget":
            return 0 if (m.forget(mid) and ok(f"archived {mid}") is None) else (fail("no such memory") or 1)
        if args.memory_action == "verify":
            e = m.verify(mid, ok=True)
            return 0 if (e and ok(f"verified {e.id}") is None) else (fail("no such memory") or 1)
        if args.memory_action == "dispute":
            e = m.verify(mid, ok=False)
            return 0 if (e and ok(f"marked {e.id} CONTRADICTED") is None) else (fail("no such memory") or 1)
        new = " ".join(args.memory_args[1:]).strip()
        if not new:
            fail("usage: rad memory correct <id> <new text>")
            return 1
        e = m.correct(mid, new)
        return 0 if (e and ok(f"corrected → {e.id} (user_provided, verified)") is None) else (fail("no such memory") or 1)
    print(col.bold("Memory layers:"))
    print(m.show())
    return 0


def cmd_user(args) -> int:
    from rad.usermodel import UserModel, DICT_SECTIONS, SECTIONS
    home = _home(args)
    um = UserModel(home)
    a = args.user_action
    if a == "show":
        print(col.bold("User model:"))
        print(um.show())
        return 0
    if a == "set":
        if len(args.user_args) < 3:
            fail("usage: rad user set <section> <key> <value…>   sections: " + ", ".join(sorted(DICT_SECTIONS)))
            return 1
        sec, key, val = args.user_args[0], args.user_args[1], " ".join(args.user_args[2:])
        try:
            um.set(sec, key, val)
        except ValueError as e:
            fail(str(e)); return 1
        ok(f"{sec}.{key} = {val}")
        return 0
    if a == "add":
        if len(args.user_args) < 2:
            fail("usage: rad user add <section> <value…>   sections: goals, projects, constraints, routines, active_priorities")
            return 1
        try:
            um.add(args.user_args[0], " ".join(args.user_args[1:]))
        except ValueError as e:
            fail(str(e)); return 1
        ok("added")
        return 0
    if a == "forget":
        if len(args.user_args) < 2:
            fail("usage: rad user forget <section> <key|value>")
            return 1
        return 0 if um.forget(args.user_args[0], " ".join(args.user_args[1:])) else (fail("not found") or 1)
    if a == "reset":
        um.save({s: ({} if s in DICT_SECTIONS else []) for s in SECTIONS})
        ok("user model reset")
        return 0
    return 1


def cmd_evolve(args) -> int:
    """Gated evolution. `rad evolve <direction>` proposes → sandboxes → runs the lab on both →
    promotes only if the gate passes. Sub-commands inspect/approve/rollback candidates.
    `--unsafe-direct` keeps the old ungated behaviour (explicit opt-out, logged)."""
    from rad.evolution import Evolution, InvalidCandidate, propose_from_direction, propose_from_evidence
    from rad.lab import Lab
    home = _home(args)
    evo = Evolution(home)
    words = list(args.direction or [])
    sub = words[0] if words and words[0] in ("list", "show", "approve", "reject", "rollback", "verify", "from-lab", "log") else None
    if sub:
        rest = words[1:]
        if sub == "list":
            for c in evo.candidates(args.n):
                ev = c.evidence
                sc = f"{ev.get('base_score')}→{ev.get('cand_score')}" if "cand_score" in ev else "-"
                print(f"  {c.id} {c.status:<10} gen={c.generation if c.generation is not None else '-':<3} lab={sc:<12} {c.origin:<9} {c.direction[:50]}")
            return 0
        if sub == "log":
            for e in evo.log(args.n):
                print(f"  {time.strftime('%m-%d %H:%M', time.localtime(e['at']))} {e['kind']:<17} {e['candidate']} {e.get('direction','')[:50]}"
                      + (f"  gate={e['gate']} {e.get('reasons')}" if 'gate' in e else "") + (f"  {e.get('reason','')}" if e.get('reason') else ""))
            return 0
        c = evo.get(rest[0]) if rest else None
        if sub in ("show", "approve", "reject", "rollback") and not c:
            fail(f"usage: rad evolve {sub} <candidate-id>"); return 1
        if sub == "show":
            d = c.to_dict(); d["evidence"].pop("sandbox", None)
            print(json.dumps(d, indent=2, ensure_ascii=False)); return 0
        if sub == "approve":
            gate_ok = bool((c.evidence.get("gate") or {}).get("pass"))
            if not gate_ok and not args.force:
                fail(f"{c.id} has not passed the lab gate ({'; '.join((c.evidence.get('gate') or {}).get('reasons', ['not evaluated']))}). "
                     "Use --force to apply it anyway (recorded as UNGATED).")
                return 1
            c = evo.promote(c, approved_by="user", force=not gate_ok)
            (ok if c.status == "promoted" else fail)(f"{c.id}: {c.status} — {c.reason}")
            return 0 if c.status == "promoted" else 1
        if sub == "reject":
            evo.reject(c, " ".join(rest[1:]) or "rejected by user"); ok(f"{c.id} rejected"); return 0
        if sub == "rollback":
            if evo.rollback(c):
                ok(f"{c.id} rolled back (DNA to parent generation, config restored)"); return 0
            fail("only promoted candidates can be rolled back"); return 1
        if sub == "verify":
            info("  re-running the lab on the live configuration…")
            out = evo.verify_current(home.cfg.get("evolution_suite", "smoke"))
            print(f"  {out['label']} score={out['score']} gate={'PASS' if out['gate']['pass'] else 'FAIL ' + '; '.join(out['gate']['reasons'])}")
            if out["rolled_back"]:
                warn(f"  rolled back {out['rolled_back']}")
            return 0 if out["gate"]["pass"] else 2
        if sub == "from-lab":
            rep = Lab(home).find(rest[0]) if rest else (Lab(home).history(1) or [None])[0]
            if not rep:
                fail("no lab run found (rad lab run first)"); return 1
            props = propose_from_evidence(home, rep)
            if not props:
                ok("lab report suggests no change"); return 0
            for pr in props:
                c = evo.propose(pr["why"], pr["changes"], origin="heuristic")
                if c.status == "rejected":
                    info(f"  skip: {c.reason}"); continue
                info(f"  evaluating {c.id}: {pr['why']}")
                evo.evaluate(c, suite=home.cfg.get("evolution_suite", "smoke"))
                c = evo.promote(c)
                (ok if c.status == "promoted" else warn)(f"  {c.id}: {c.status} — {c.reason}")
            return 0
    direction = " ".join(words)
    if not direction:
        fail("usage: rad evolve <direction> | list | show|approve|reject|rollback <id> | verify | from-lab [label] | log")
        return 1
    r = _router(home)
    has_brain = bool(r.build_chain())
    llm = (lambda p: _llm(home, p)) if has_brain else None
    if llm is None:
        info("  (no brain online — deterministic proposal)")
    try:
        changes = propose_from_direction(home, direction, llm)
    except Exception as e:
        fail(f"proposal failed: {e}"); return 1
    if not changes:
        ok("direction produced no change"); return 0
    if getattr(args, "unsafe_direct", False):
        c = evo.propose(direction, changes, origin="llm" if has_brain else "heuristic")
        if c.status == "rejected":
            ok(c.reason); return 0
        c = evo.promote(c, approved_by="user --unsafe-direct", force=True)
        warn(f"applied without lab gate → generation {c.generation} (rad evolve rollback {c.id} to undo)")
        return 0
    try:
        c = evo.propose(direction, changes, origin="llm" if has_brain else "heuristic")
    except InvalidCandidate as e:
        fail(f"rejected: {e}"); return 1
    if c.status == "rejected":
        ok(c.reason); return 0
    for k, d in c.evidence["diff"].items():
        print(f"  {k}: {col.dim(str(d['from'])[:80])} → {str(d['to'])[:80]}")
    if not has_brain:
        warn("  no brain online: the lab gate cannot run. Candidate saved; run `rad evolve approve "
             f"{c.id} --force` to apply it ungated, or come back when a brain is available.")
        c.evidence["gate"] = {"pass": False, "reasons": ["lab not run (no brain)"]}; evo._save(c)
        return 0
    suite = home.cfg.get("evolution_suite", "smoke")
    info(f"  sandboxing candidate and running lab suite '{suite}' on baseline and candidate…")
    gate = evo.evaluate(c, suite=suite)
    ev = c.evidence
    print(f"  baseline score={ev['base_score']} safety={ev['base_safety']} honesty={ev['base_honesty']}  →  "
          f"candidate score={ev['cand_score']} safety={ev['cand_safety']} honesty={ev['cand_honesty']}")
    c = evo.promote(c)
    if c.status == "promoted":
        ok(f"gate passed → promoted as generation {c.generation}  ({c.id}; `rad evolve rollback {c.id}` to undo)")
        return 0
    if gate["pass"]:
        warn(f"gate passed; {c.reason}  → rad evolve approve {c.id}")
        return 0
    fail(f"gate FAILED → not applied. {'; '.join(gate['reasons'])}")
    return 2


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


# ---------------------------------------------------------------- evolution 2.0

def cmd_corpus(args) -> int:
    from rad.corpus import Corpus
    home = _home(args)
    c = Corpus(home)
    if args.corpus_action == "export":
        dest = c.export(args.out)
        s = c.stats()
        ok(f"exported {s['total']} pairs → {dest}")
        return 0
    print(col.bold("Corpus (Rad's experience as training data):"))
    print(c.show())
    return 0


def cmd_benchmark(args) -> int:
    from rad.battery import Benchmark, build_caller
    home = _home(args)
    bench = Benchmark(home)
    cats = args.cats.split(",") if args.cats else None
    chain = _router(home).build_chain()
    if not chain and not args.provider:
        fail("no brain available to benchmark — add a key or start a local engine")
        return 1
    provider_name = args.provider or (chain[0].spec.name if chain else None)
    model_name = args.model or (chain[0].model if chain else None) or "?"
    label = args.label or f"{provider_name}:{model_name}"
    caller = build_caller(home, provider=args.provider, model=args.model)
    try:
        caller("You are Rad.", "Reply with exactly: OK")
    except Exception as e:
        fail(f"brain '{provider_name}' unreachable: {e}")
        return 1
    info("  running capability battery (this calls the brain per task)…")
    rep = bench.run(caller, label=label, provider=provider_name, model=model_name, categories=cats)
    print(col.bold(f"\n  score: {rep['score']}/100   ({label})"))
    for c, v in sorted(rep["categories"].items()):
        print(f"    {c:<14} {v:>6}")
    print()
    print(col.bold("  history:"))
    print(bench.compare())
    return 0


def cmd_brain(args) -> int:
    from rad.brains import Brains
    home = _home(args)
    b = Brains(home)
    if args.brain_action == "add":
        cand = b.add(args.name, args.provider, model=args.model or "", adapter=args.adapter,
                     temperature=args.temp, note=args.note or "")
        ok(f"brain candidate '{cand['name']}' added"
           + (f" (adapter staged: {cand['adapter']})" if cand.get("adapter") else ""))
        if not b.current() or b.current()["name"] == cand["name"]:
            ok("it is now the current brain (first candidate)")
        return 0
    if args.brain_action == "list":
        print(col.bold("Brain candidates (nothing goes live without winning the battery):"))
        print(b.show())
        return 0
    if args.brain_action == "current":
        cur = b.current()
        if cur:
            print(f"  {cur['name']}  →  {cur['provider']}/{cur.get('model') or '?'}"
                  + (f"  adapter: {cur['adapter']}" if cur.get("adapter") else ""))
        else:
            print("  no pinned brain — routing chain decides per request")
        return 0
    if args.brain_action == "promote":
        from rad.battery import Benchmark
        bench = Benchmark(home)
        info("  benchmark battle: candidate vs current brain…")
        res = b.promote(args.name, bench, margin=args.margin)
        if res["promoted"]:
            ok(f"PROMOTED: {res['candidate']} — {res['new']} vs {res['old']} (margin {args.margin})")
        else:
            warn(f"rejected: {res['candidate']} — {res['new']} vs current {res['old']} "
                 f"(needs +{args.margin}). The throne stands.")
        return 0
    if args.brain_action == "rollback":
        prev = b.rollback()
        if prev:
            ok(f"rolled back to brain '{prev}'")
        else:
            info("nothing to roll back")
        return 0
    fail("usage: rad brain add|list|current|promote|rollback")
    return 1


def cmd_train(args) -> int:
    from rad import train
    home = _home(args)
    if args.run:
        return train.run_training(home, args.model or "edge0-35b",
                                   args.out or str(home.root / "adapters"), backend=args.backend)
    print(train.plan(home, model_ref=args.model or "edge0-35b", out_dir=args.out or ""))
    return 0


def cmd_plan(args) -> int:
    from rad.plan import Plan
    home = _home(args)
    p = Plan(home)
    # argparse eats action words into plan_goal (nargs="*" greed) — normalize
    if args.plan_action is None and args.plan_goal and args.plan_goal[0] in ("status", "done", "clear", "run"):
        args.plan_action = args.plan_goal[0]
        args.plan_goal = args.plan_goal[1:]
    # `rad plan done 1` — the number rides in plan_goal, not --step
    if args.plan_action == "done" and args.step == 0 and args.plan_goal and args.plan_goal[0].isdigit():
        args.step = int(args.plan_goal[0])
        args.plan_goal = args.plan_goal[1:]
    if args.plan_action == "run":
        from rad.planrun import PlanRunner
        if Plan(home).load() is None:
            fail("no current plan — `rad plan <goal>` first")
            return 1
        info("  Rad is now executing the plan with its hands…")
        info("  (tip: `rad objective run <goal>` adds verification, recovery and resume)")
        rep = PlanRunner(home, auto=args.auto).run(max_steps=args.max)
        print()
        if rep["blocked"]:
            warn(f"  execution stopped — human needed: {rep['blocked']}")
            return 2
        ok(f"  ran {rep['ran']} step(s): {rep['done']} done")
        print(Plan(home).status())
        return 0
    if args.plan_action == "status":
        print(col.bold("Plan:"))
        print(p.status())
        return 0
    if args.plan_action == "done":
        if not args.step:
            fail("which step?  rad plan done <n> [--note x]")
            return 1
        if p.toggle(args.step - 1, done=True, note=args.note or "") is None:
            fail(f"no such step {args.step}")
            return 1
        ok(f"step {args.step} marked done")
        print(p.status())
        return 0
    if args.plan_action == "clear":
        p.clear()
        ok("plan cleared")
        return 0
    if args.plan_goal:
        caller = None
        if p.load() is None and _router(home).build_chain():
            def caller(prompt: str) -> str:
                return _router(home).chat([{"role": "user", "content": prompt}], stream_cb=None).text
            caller = caller
        plan = p.create(" ".join(args.plan_goal), caller=caller)
        ok(f"plan created: {len(plan['steps'])} steps")
        print(p.status())
        return 0
    fail("usage: rad plan <goal> | status | done <n> [--note x] | clear")
    return 1


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
    me.add_argument("memory_action", nargs="?", default="show",
                    choices=["show", "prune", "conflicts", "forget", "verify", "dispute", "correct"])
    me.add_argument("memory_args", nargs="*")
    me.set_defaults(fn=cmd_memory)

    us = sub.add_parser("user", help="the user model — what Rad believes about you (inspect / correct)")
    us.add_argument("user_action", nargs="?", default="show", choices=["show", "set", "add", "forget", "reset"])
    us.add_argument("user_args", nargs="*")
    us.set_defaults(fn=cmd_user)

    ev = sub.add_parser("evolve", help="gated evolution: rad evolve <direction> | list | approve/reject/rollback <id> | verify | from-lab")
    ev.add_argument("direction", nargs="*")
    ev.add_argument("--unsafe-direct", action="store_true", help="apply without the lab gate (logged)")
    ev.add_argument("--force", action="store_true", help="with approve: apply a candidate that did not pass the gate")
    ev.add_argument("-n", type=int, default=20)
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

    # evolution 2.0
    co = sub.add_parser("corpus", help="experience → training data")
    co.add_argument("corpus_action", nargs="?", default="show", choices=["show", "export"])
    co.add_argument("--out", default=None)
    co.set_defaults(fn=cmd_corpus)

    bm = sub.add_parser("benchmark", help="capability battery — is Rad smarter? now it's a number")
    bm.add_argument("--provider", default=None); bm.add_argument("--model", default=None)
    bm.add_argument("--cats", default=None, help="comma list: math,logic,code,tool,json,summarize,style")
    bm.add_argument("--label", default=None)
    bm.set_defaults(fn=cmd_benchmark)

    br = sub.add_parser("brain", help="brain candidates + promotion protocol (verified evolution)")
    brsub = br.add_subparsers(dest="brain_action")
    bradd = brsub.add_parser("add")
    bradd.add_argument("name"); bradd.add_argument("--provider", required=True)
    bradd.add_argument("--model", default=""); bradd.add_argument("--adapter", default=None)
    bradd.add_argument("--temp", type=float, default=0.7); bradd.add_argument("--note", default="")
    brsub.add_parser("list")
    brsub.add_parser("current")
    brpromo = brsub.add_parser("promote"); brpromo.add_argument("name"); brpromo.add_argument("--margin", type=float, default=0.0)
    brsub.add_parser("rollback")
    br.set_defaults(fn=cmd_brain)

    tr = sub.add_parser("train", help="weight evolution: corpus → trainer backends")
    tr.add_argument("--plan", action="store_true")
    tr.add_argument("--run", action="store_true")
    tr.add_argument("--model", default=None); tr.add_argument("--out", default=None)
    tr.add_argument("--backend", default="auto", choices=["auto", "mlx", "unsloth", "peft"])
    tr.set_defaults(fn=cmd_train)

    pl = sub.add_parser("plan", help="goal planning: decompose, track, drive, RUN")
    pl.add_argument("plan_goal", nargs="*")
    pl.add_argument("plan_action", nargs="?", default=None, choices=["status", "done", "clear", "run"])
    pl.add_argument("--step", type=int, default=0); pl.add_argument("--note", default=None)
    pl.add_argument("--auto", action="store_true", help="hands act without confirmation")
    pl.add_argument("--max", type=int, default=None, help="run at most N steps")
    pl.set_defaults(fn=cmd_plan)

    from rad.control.cli import add_parsers as _control_parsers
    _control_parsers(sub)

    tm = sub.add_parser("team", help="multi-agent cognition — specialists + synthesis")
    tm.add_argument("team_action", nargs="?", default="roles", choices=["run", "roles", "history"])
    tm.add_argument("team_problem", nargs="*")
    tm.add_argument("--mode", default="solo", choices=["solo", "debate"])
    tm.add_argument("--roles", default=None, help="comma list: coder,reviewer,planner,researcher,writer")
    tm.add_argument("--n", type=int, default=0, help="number of default roles to spawn")
    tm.add_argument("--backend", default="builtin", choices=["builtin", "autogen"])
    tm.add_argument("--tools", action="store_true", help="agents may use their own scoped tools (see `rad agents`)")
    tm.set_defaults(fn=cmd_team)

    wo = sub.add_parser("world", help="world model — Rad's picture of your world")
    wo.add_argument("world_action", nargs="?", default="show",
                    choices=["show", "query", "add", "learn", "sync", "cypher", "retract", "confirm", "disputes"])
    wo.add_argument("world_term", nargs="*")
    wo.add_argument("--path", default=None, help="file to mine (learn)")
    wo.add_argument("--history", action="store_true", help="query: include superseded relations")
    wo.set_defaults(fn=cmd_world)

    v = sub.add_parser("version", help="version"); v.set_defaults(fn=cmd_version)
    return p


def cmd_team(args) -> int:
    from rad.team import Team, DEFAULT_ROLES, autogen_available, run_autogen
    home = _home(args)
    team = Team(home)
    if args.team_action == "roles":
        info("  specialist roles:")
        for name, desc in DEFAULT_ROLES.items():
            print(f"    {col.cyan(name + ':'):<14} {desc[:80]}")
        info(f"  backends: builtin=always, autogen={'installed' if autogen_available() else 'not installed'}")
        return 0
    if args.team_action == "history":
        print("\n".join(team.history(15)))
        return 0
    problem = " ".join(args.team_problem).strip()
    if not problem:
        fail("usage: rad team run <problem> [--mode solo|debate] [--roles a,b] [--n 3]")
        return 1
    roles = [r.strip() for r in args.roles.split(",")] if args.roles else None
    if args.backend == "autogen":
        out = run_autogen(home, problem, roles or ["coder", "reviewer", "planner"])
        if out is None:
            fail("autogen backend unavailable (no chain or not installed) — use --backend builtin")
            return 1
        ok("autogen run finished")
        print(out)
        return 0
    res = team.run(problem, roles=roles, mode=args.mode, n=args.n, tools=args.tools)
    for a in res["answers"]:
        tag = col.cyan(a["role"]) if a["role"] != "debate" else col.magenta("debate")
        print(f"\n  [{tag}]")
        print("  " + a["answer"].replace("\n", "\n  ")[:900])
    print(col.bold("\n  → final (synthesized):"))
    print("  " + res["final"].replace("\n", "\n  ")[:1500])
    return 0


def cmd_world(args) -> int:
    from rad.world import WorldModel
    home = _home(args)
    w = WorldModel(home)
    if args.world_action == "show":
        print(w.show())
        return 0
    if args.world_action == "query":
        term = " ".join(args.world_term)
        if not term:
            fail("usage: rad world query <term>")
            return 1
        hits = w.query(term, include_history=args.history)
        if not hits:
            info("  nothing in the world model matches")
            return 0
        for h in hits:
            if h["type"] == "entity":
                print(f"    • {h['name']}  {col.dim(h.get('kind', ''))}")
            else:
                st = h.get("status", "current")
                tag = col.dim(f"{h.get('origin', 'inferred').lower()} c={h.get('confidence', 0.5):.2f}")
                flag = col.yellow(f" [{st}]") if st != "current" else ""
                print(f"    → {h['from']} {col.dim('–' + h['rel'] + '–>')} {h['to']}  {tag}{flag}")
        return 0
    if args.world_action in ("retract", "confirm"):
        if len(args.world_term) < 3:
            fail(f"usage: rad world {args.world_action} <from> <rel> <to…>")
            return 1
        a_, rel, b_ = args.world_term[0], args.world_term[1], " ".join(args.world_term[2:])
        fn = w.retract if args.world_action == "retract" else w.confirm
        return 0 if (fn(a_, rel, b_) and ok(f"{args.world_action}ed: {a_} –{rel}–> {b_}") is None) else (fail("no such relation") or 1)
    if args.world_action == "disputes":
        ds = w.disputes()
        if not ds:
            info("  no disputed relations")
            return 0
        for r in ds:
            print(f"  {col.yellow('⚡')} {r['from']} –{r['rel']}–> {r['to']}  {col.dim(r.get('origin', '').lower())}  disputes: {r.get('disputes')}")
        info("  resolve: rad world confirm <from> <rel> <to> | rad world retract <from> <rel> <to>")
        return 0
    if args.world_action == "add":
        sentence = " ".join(args.world_term)
        if not sentence:
            fail("usage: rad world add <sentence about your world>")
            return 1
        caller = None
        if _router(home).build_chain():
            def caller(prompt: str) -> str:
                return _router(home).chat([{"role": "user", "content": prompt}], stream_cb=None).text
            caller = caller
        n = w.add(sentence, caller=caller)
        ok(f"learned {n} new fact(s)" if n else "nothing new learned")
        return 0
    if args.world_action == "sync":
        from rad.world import kuzu_sync
        out = kuzu_sync(home, w)
        if out is None:
            fail("kuzu not installed — `pip install kuzu` (optional graph mirror)")
            return 1
        ok(out)
        return 0
    if args.world_action == "cypher":
        from rad.world import kuzu_query
        cypher = " ".join(args.world_term).strip()
        if not cypher:
            fail("usage: rad world cypher <cypher query>   e.g. cypher MATCH (n:EntityNode) RETURN n.name AS name")
            return 1
        print(kuzu_query(home, cypher))
        return 0
    # learn: mine a file or the short-term memory store
    if args.path:
        text = Path(args.path).read_text(errors="ignore")
        n = w.learn(text, source=f"file:{Path(args.path).name}")
    else:
        n = 0
        for f in sorted((home.root / "memory" / "short").glob("*.md")):
            n += w.learn(f.read_text(errors="ignore"), source=f.name)
    ok(f"world model: +{n} new fact(s) mined")
    print(w.show())
    return 0


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
