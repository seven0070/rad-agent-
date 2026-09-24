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
from rad.home import DEFAULTS, RadHome, mask
from rad.ui import ask, col, fail, info, ok, warn


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
    # voice backend auto (T5): --voice auto TEN→fallback, --voice-backend pins
    vb = getattr(args, "voice_backend", "auto")
    if vb != "auto":
        home.update(voice_backend=vb)
    elif args.voice:
        try:
            from rad.voice import voice_auto_mode
            mode = voice_auto_mode(home)
            info(f"  voice auto: {mode} (TEN={'on' if mode=='ten' else 'off'} fallback=Piper/Whisper)")
        except Exception:
            pass
    if args.auto:
        home.update(auto=True)
        try:
            from rad.authority import Authority
            Authority(home).note_session_auto(True, actor="user")
        except Exception:
            pass
    repl(home, auto=home.cfg.get("auto", False), voice=args.voice)
    return 0


def cmd_keys(args) -> int:
    from rad import providers as P
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
    from rad.health import last_class_c
    home = _home(args)
    r = _router(home)
    print(col.bold("Providers — brain socket:"))
    print(r.describe())
    last = last_class_c(home)
    if last and last.get("class_c"):
        print(col.yellow(
            f"  last Class C: {last.get('provider')} {last.get('kind')} HTTP {last.get('status')}"
        ))
        if last.get("next_steps"):
            print(col.dim("  " + last["next_steps"]))
    return 0


def cmd_use(args) -> int:
    home = _home(args)
    home.update(force_provider=args.provider)
    ok(f"pinned provider: {args.provider}")
    return 0


def cmd_cost(args) -> int:
    from rad.control.objectives import ObjectiveStore, usage_rollup_report
    home = _home(args)
    print(col.bold("Paid spend (free/local never appears here):"))
    print(_router(home).cost_report())
    print()
    print(col.bold("Objective usage (persisted records; not remaining quota):"))
    print(usage_rollup_report(ObjectiveStore(home).usage_rollup()))
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
    evolve_flag = getattr(args, "evolve", False)
    report = run_sleep(home, _router(home), sync_drive=not args.no_sync, evolve=evolve_flag)
    if evolve_flag:
        ev = report.get("evolve")
        if ev and ev.get("evolve") == "disabled":
            info(f'  evolve skipped: {ev.get("reason")}')
        elif ev:
            gate = ev.get("gate", {})
            if gate.get("promoted"):
                ok(f'evolve promoted: {gate.get("proposal",{}).get("type")} -> {gate.get("gate")} gate passed')
            else:
                info(f'evolve: {gate.get("reason","no promotion")} (proposal {ev.get("proposal",{}).get("type")})')

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


def cmd_doctor(args) -> int:
    from rad.doctor import Doctor, render
    home = _home(args)
    print(col.bold(f"rad doctor{' --fix' if args.fix else ''}:"))
    findings = Doctor(
        home, fix=args.fix, probe_network=not args.offline,
        force=bool(getattr(args, "force", False))).run()
    print(render(findings))
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    return 1 if any(f.status == "fail" for f in findings) else 0


def cmd_health(args) -> int:
    """Pause / resume / campaign surface. Skip-blocked unless --force."""
    from rad.health import operator_status
    home = _home(args)
    st = operator_status(home, force=bool(getattr(args, "force", False)))
    if getattr(args, "json", False):
        print(json.dumps(st.to_dict(), indent=2, default=str))
        return 0 if st.next_action in ("resume", "run") and st.allow else 2
    print(col.bold("rad health — live-use campaign / operator workflow (G4-3):"))
    paint = col.green if st.allow else col.yellow
    print(f"  next-action  {paint(st.next_action)}")
    print(f"  live-gate    {'allow' if st.allow else 'deny'} — {st.reason}")
    if st.next_steps:
        print(col.dim("  next-steps   " + st.next_steps))
    if st.entitled:
        print(f"  entitled     {', '.join(st.entitled)}")
    if st.catalog_only:
        print(col.yellow("  catalog-only " + ", ".join(st.catalog_only)
                         + " (not a live brain)"))
    if st.skipped_inference:
        print(col.dim("  skipped-chat " + ", ".join(st.skipped_inference)
                      + " — last Class C still blocks"))
    last = st.last or {}
    if last.get("class_c"):
        ra = st.retry_after
        extra = f"; Retry-After {int(ra)}s" if ra else ""
        print(col.yellow(
            f"  last Class C {last.get('provider')} {last.get('kind')} "
            f"HTTP {last.get('status')}{extra}"))
    if st.paused_objectives:
        print("  paused       " + ", ".join(st.paused_objectives)
              + " — `rad objective resume <id>` after entitled")
    if getattr(args, "campaign", False) or not st.allow:
        print(col.bold("  campaign playbook:"))
        for line in st.playbook:
            print("    " + line)
    return 0 if st.next_action in ("resume", "run") and st.allow else 2


def cmd_storage(args) -> int:
    from rad.storage import SCHEMA_VERSION, Storage
    home = _home(args)
    st = Storage(home)
    a = args.storage_action
    if a == "status":
        sch = st.schema()
        print(f"  schema v{sch.get('version', 0)} (code expects v{SCHEMA_VERSION}); pending: {[m.name for m in st.pending()] or 'none'}")
        for a_ in sch.get("applied", []):
            print(f"    v{a_['version']} {a_['name']}  {time.strftime('%Y-%m-%d %H:%M', time.localtime(a_['at']))}  {a_.get('summary', '')}")
        for k, v in st.usage().items():
            print(f"  {k:<12} {v['files']:>5} files  {v['bytes'] / 1e3:>9.1f} KB")
        return 0
    if a == "migrate":
        done = st.migrate(dry_run=args.dry_run)
        for d in done:
            print(f"  v{d['version']} {d['name']} {d.get('summary', '')}{' (dry run)' if d.get('dry_run') else ''}")
        ok("up to date" if not done else f"{len(done)} step(s)")
        return 0
    if a == "check":
        f = st.integrity(repair=args.repair)
        for x in f:
            print(f"  {'fixed ' if x['repaired'] else ''}{x['path']}: {x['problem']}")
        (ok if not f else warn)(f"{len(f)} finding(s)")
        return 0 if not f else 1
    if a == "snapshot":
        p = st.snapshot(label=args.label or "manual", include_keys=args.include_keys)
        ok(f"snapshot → {p}" + ("" if args.include_keys else "  (keys excluded; --include-keys to add)"))
        return 0
    if a == "snapshots":
        for p in st.snapshots():
            print(f"  {p.name}  {p.stat().st_size / 1e3:.1f} KB")
        return 0
    if a == "restore":
        if not args.label:
            fail("usage: rad storage restore --label <snapshot file name>"); return 1
        p = home.root / "backups" / args.label
        if not p.exists():
            fail(f"no such snapshot {p.name}"); return 1
        if not args.yes and not ask(f"  restore {p.name} over {home.root}? (a pre-restore snapshot is taken first)"):
            return 1
        ok(f"restored: {', '.join(st.restore(p))}")
        return 0
    return 1


def cmd_serve(args) -> int:
    from rad.api import make_server, token_for
    home = _home(args)
    host = args.host or "127.0.0.1"
    if host not in ("127.0.0.1", "localhost", "::1") and not args.i_know_this_exposes_rad:
        fail("binding to a non-loopback host exposes RAD's control plane to the network. "
             "Add --i-know-this-exposes-rad if that is really what you want (and use a firewall).")
        return 1
    tok = token_for(home, rotate=args.rotate_token)
    port = args.port or int(home.cfg.get("api_port", 7331))
    srv = make_server(home, host=host, port=port)
    print(col.bold(f"rad api  http://{host}:{port}/v1"))
    print(f"  token: {tok}   (stored 0600 at {home.root / 'api.token'}; --rotate-token to replace)")
    from rad.authority import Authority
    auth = Authority(home)
    confirm = "never" if (home.cfg.get("auto") or auth.confirmation_is_automatic()) else "ask"
    print(f"  confirmation={confirm}  profile={auth.state.profile}  "
          f"auto={'on' if home.cfg.get('auto') else 'off'}   log: {home.root / 'logs' / 'api.jsonl'}")
    print(col.dim("  curl -H \"Authorization: Bearer $TOKEN\" http://%s:%d/v1/health" % (host, port)))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


def cmd_desktop(args) -> int:
    """Launch RAD Desktop if a built binary exists; otherwise print the foundation path.

    Desktop is a surface over `rad serve`. It never executes tools itself.
    """
    root = Path(__file__).resolve().parent.parent / "desktop"
    info("RAD Desktop 1.0.1 — surface over the existing Python HTTP API")
    info("  backend: rad serve   (Policy.decide + Executor unchanged)")
    info(f"  ui source: {root}")
    if not root.exists():
        fail("desktop/ is not in this checkout")
        return 1
    built = [
        root / "src-tauri" / "target" / "release" / "rad-desktop",
        root / "src-tauri" / "target" / "debug" / "rad-desktop",
    ]
    for p in built:
        if sys.platform == "win32" and p.with_suffix(".exe").exists():
            p = p.with_suffix(".exe")
        if p.exists():
            ok(f"launching {p}")
            subprocess.Popen([str(p)], start_new_session=True)
            return 0
    print("  not built yet. From desktop/:")
    print("    npm install && npm run tauri dev")
    print("  The frontend talks only to /v1/* ; it has no arbitrary-shell command.")
    return 0


def cmd_web(args) -> int:
    """Launch the RAD Web UI (Rust web server + JavaScript/TypeScript frontend)."""
    import webbrowser
    root = Path(__file__).resolve().parent.parent
    web_dir = root / "desktop"
    dist_dir = web_dir / "dist"
    port = args.port or 3000
    api_port = args.api_port or 7331
    url = f"http://127.0.0.1:{port}"

    info("RAD Web UI — Rust + JavaScript/TypeScript Interface")
    info(f"  frontend url:  {url}")
    info(f"  agent backend: http://127.0.0.1:{api_port}/v1")

    # 1. Search for built Rust web server binary
    rust_bin = None
    for p in [
        root / "crates" / "rad-web" / "target" / "release" / "rad-web",
        root / "crates" / "rad-web" / "target" / "debug" / "rad-web",
    ]:
        if sys.platform == "win32" and p.with_suffix(".exe").exists():
            p = p.with_suffix(".exe")
        if p.exists():
            rust_bin = p
            break

    # Build web dist if needed
    if not dist_dir.exists() or not (dist_dir / "index.html").exists():
        info("  building frontend web assets (npm run build)...")
        subprocess.run(["npm", "run", "build"], cwd=str(web_dir), shell=sys.platform == "win32")

    if not getattr(args, "no_open", False):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if rust_bin:
        ok(f"launching Rust web daemon ({rust_bin.name})")
        return subprocess.call([
            str(rust_bin),
            "--port", str(port),
            "--api-port", str(api_port),
            "--dist", str(dist_dir),
        ])

    # Fallback to Python simple HTTP server if Rust binary is missing
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class WebHandler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(dist_dir), **kw)

        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

        def do_GET(self):
            clean = self.path.split("?")[0].lstrip("/")
            p = (dist_dir / clean).resolve()
            if not p.exists() and not self.path.startswith("/assets"):
                self.path = "/index.html"
            return super().do_GET()

    ok(f"RAD Web UI listening on {url} (fallback mode)")
    srv = ThreadingHTTPServer(("127.0.0.1", port), WebHandler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
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
    from rad import skills as SK
    home = _home(args)
    reg = home.skills()
    a = args.skills_action
    if a == "audit":
        rows = SK.audit(home)
        if not rows:
            info("no skills connected"); return 0
        for r in rows:
            mark = col.red("!") if r["flags"] else col.green("✓")
            print(f"  {mark} {col.bold(r['name']):<18} approval={r['approval']:<7} trust={r['trust']:<7} caps={', '.join(r['capabilities'])}  {r['tools']} tools")
            for f in r["flags"]:
                print(f"        {col.dim(f)}")
        return 1 if any(r["flags"] for r in rows) else 0
    if a == "approve":
        if not args.skills_args:
            fail("usage: rad skills approve <name> [allow|ask|deny|policy]"); return 1
        try:
            m = SK.approve(home, args.skills_args[0], args.skills_args[1] if len(args.skills_args) > 1 else "allow")
        except ValueError as e:
            fail(str(e)); return 1
        ok(f"{m['name']}: approval={m['approval']} pinned={m['pinned']}"); return 0
    if a == "declare":
        if len(args.skills_args) < 3:
            fail("usage: rad skills declare <skill> <tool> <cap,cap>   caps: fs.read fs.write shell web mcp"); return 1
        try:
            m = SK.declare(home, args.skills_args[0], args.skills_args[1], args.skills_args[2].split(","))
        except ValueError as e:
            fail(str(e)); return 1
        ok(f"{m['name']}.{args.skills_args[1]} → {m['tools'][args.skills_args[1]]}"); return 0
    if a == "manifest":
        if not args.skills_args:
            fail("usage: rad skills manifest <name>"); return 1
        m = SK.ensure_manifest(home, args.skills_args[0])
        if not m:
            fail("not connected"); return 1
        print(json.dumps(m, indent=2)); return 0
    if a == "evolve":
        # P1 stub: trajectory->skill miner, lab-gated promotion
        res = SK.skills_evolve(home)
        if res.get("promoted"):
            ok(f"skills evolve promoted: +{res['delta']} bank {res['before']}->{res['after']} ({res['reason']})")
        else:
            info(f"skills evolve: no promotion ({res['reason']}) trajectories={res.get('trajectories',0)} before={res.get('before')} after={res.get('after')}")
        return 0
    if not reg:
        info("no skills connected yet — `rad connect <link>`")
        return 0
    for name, e in reg.items():
        m = SK.ensure_manifest(home, name)
        print(f"  • {col.bold(name)}  {col.dim(e.get('transport', 'stdio'))}  approval={m.get('approval')}  caps={', '.join(m.get('capabilities', []))}")
        for t in e.get("tools", []):
            print(f"      {t['name']:<32} {col.dim(','.join(m.get('tools', {}).get(t['name'], [])) + '  ' + (t.get('description') or '')[:60])}")
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
    from rad import providers as P
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


def cmd_connectome(args) -> int:
    """RadConnectome — fruit fly brain wiring for Rad (neuPrint for agents)."""
    from rad.connectome import Connectome, ingest_objective_events
    home = _home(args)
    cx = Connectome(home)
    act = args.connectome_action
    if act == "show":
        st = cx.stats()
        print(col.bold(f"  RadConnectome — {st['neurons']} neurons, "
                       f"{st['synapses']} synapses ({st['verified_edges']} verified)"))
        if st["rich_club"]:
            print(f"  rich club: {col.cyan(', '.join(st['rich_club'][:8]))}")
        if st["regions"]:
            print(f"  regions: {', '.join(st['regions'])}")
        print(col.dim("  agents=neurons · tools=synapses · verified-only plasticity"))
        return 0
    if act == "ingest":
        res = ingest_objective_events(home)
        ok(f"ingested {res['tasks']} task(s) → {res['edges']} edge(s) "
           f"({res['stats']['neurons']} neurons, {res['stats']['synapses']} synapses)")
        return 0
    if act == "query":
        term = " ".join(args.connectome_term)
        if not term:
            fail("usage: rad connectome query <neuron>")
            return 1
        outs = cx.neighbors(term, "out")
        ins = cx.neighbors(term, "in")
        if not outs and not ins:
            info(f"  no synapses for {term!r} — run `rad connectome ingest` first")
            return 0
        print(col.bold(f"  {term}"))
        for s in outs:
            tag = col.cyan("VERIFIED") if s.verified else col.dim("unverified")
            print(f"    → {s.post:<22} w={s.weight:.2f} {tag}  ({s.successes}✓/{s.failures}✗)")
        for s in ins:
            tag = col.cyan("VERIFIED") if s.verified else col.dim("unverified")
            print(f"    ← {s.pre:<22} w={s.weight:.2f} {tag}")
        return 0
    if act == "path":
        if len(args.connectome_term) < 2:
            fail("usage: rad connectome path <from> <to>")
            return 1
        p = cx.path(args.connectome_term[0], args.connectome_term[1])
        if not p:
            info("  no path (max 4 hops) — hubs: " + ", ".join(cx.rich_club()[:5]))
            return 0
        print("  " + col.cyan(" → ".join(p)))
        return 0
    if act == "hubs":
        hubs = cx.rich_club()
        print(col.bold(f"  rich club ({len(hubs)} hubs):"))
        for h in hubs:
            print(f"    • {h}")
        return 0
    if act == "projectome":
        proj = cx.projectome()
        print(col.bold("  projectome (region → region):"))
        for ra, targets in sorted(proj.items()):
            for rb, n in sorted(targets.items(), key=lambda x: -x[1]):
                print(f"    {ra:<20} → {rb:<20} {n}")
        return 0
    if act == "suggest":
        if not args.connectome_term:
            fail("usage: rad connectome suggest <neuron>")
            return 1
        for nxt in cx.suggest_next(args.connectome_term[0]):
            print(f"    • {nxt}")
        print(col.dim("    advisory only — the control plane still decides"))
        return 0
    if act == "replay":
        res = cx.sleep_replay()
        ok(f"sleep replay: {res['decayed']} decayed, {res['pruned']} pruned "
           f"({res['synapses']} live)")
        return 0
    fail(f"unknown connectome action: {act}")
    return 1


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


def cmd_triage_corpus(args) -> int:
    from rad.triage_data import export as triage_export, show as triage_show
    home = _home(args)
    if args.corpus_action == "export":
        dest = triage_export(home, args.out)
        from rad.triage_data import stats
        s = stats(home=home)
        ok(f"exported {s['total']} triage rows "
           f"({s.get('auto', 0)} auto / {s.get('escalate', 0)} escalate) → {dest}")
        return 0
    print(col.bold("Triage corpus (objectives history → auto/escalate labels):"))
    print(triage_show(home))
    return 0


def cmd_benchmark(args) -> int:
    action = getattr(args, "bench_action", "run")
    if action == "bank":
        return _benchmark_bank(args)
    if action == "long":
        from rad.longhorizon import LongHorizonBenchmark
        home = _home(args)
        lh = LongHorizonBenchmark(home)
        if args.sample == 0 and not args.category:
            hist = lh.latest()
            if hist:
                print(LongHorizonBenchmark.render(hist))
                info("  (showing the last run — pass --sample N to run one now)")
                return 0
        info("  running the long-horizon suite through the control plane (real tools, isolated homes)…")
        rep = lh.run(sample=args.sample or 10, label=args.label or "", seed=args.seed)
        print(LongHorizonBenchmark.render(rep))
        return 0
    if action in ("history", "compare"):
        from rad.battery import Benchmark
        home = _home(args)
        bench = Benchmark(home)
        if action == "history":
            print(bench.compare(args.n))
            return 0
        hist = bench.history()
        if len(hist) < 2:
            fail("need two battery runs to compare")
            return 1
        a, b = hist[-2], hist[-1]
        diff = round(b["score"] - a["score"], 1)
        print(col.bold(f"  {a['label']} {a['score']} → {b['label']} {b['score']}  ({diff:+})"))
        for cat in sorted(set(a.get("categories", {})) | set(b.get("categories", {}))):
            av, bv = a["categories"].get(cat), b["categories"].get(cat)
            mark = " " if (av is None or bv is None) else ("▲" if bv > av else ("▼" if bv < av else "·"))
            print(f"    {mark} {cat:<14} {av} → {bv}")
        return 0 if diff >= 0 else 2
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


def _benchmark_bank(args) -> int:
    """Objective-level benchmark: whole objectives through the control plane, graded on disk.

    This is the offline lab agent, so it costs nothing and needs no provider — it measures the
    control plane (plan → execute → observe → verify → recover), not the model.
    """
    from rad import lab_banks
    from rad.lab import Lab
    home = _home(args)
    cat = args.category or "all"
    if cat not in ("all",) and cat not in lab_banks.CATEGORIES:
        fail(f"unknown category '{cat}' — one of: {', '.join(lab_banks.CATEGORIES)}, all")
        return 1
    sample = args.sample or 0
    info(f"  bank '{cat}': {sum(lab_banks.counts().values()) if cat == 'all' else lab_banks.counts()[cat]} "
         f"scenario(s), sample={sample or 'all'}, seed={args.seed}")
    suite = "banks" if cat == "all" else f"bank:{cat}"
    lab = Lab(home)
    label = args.label or f"bank-{cat}-{time.strftime('%H%M%S')}"

    def prog(r):
        if not r.success:
            print(f"    {col.red('FAIL')} {r.id:<26} {r.status:<10} {r.trajectory_detail[:60]}")

    rep = lab.run(suite=suite, label=label, sample=sample, seed=args.seed, progress=prog)
    print(Lab.render(rep))
    return 0 if rep["success_rate"] == 1.0 and rep["safety"] == 1.0 and rep["honesty"] == 1.0 else 1


def cmd_evaluate(args) -> int:
    """Full capability battery for a brain, with history, stability and a promotion gate."""
    from rad.evaluation import ModelEvaluator, CATEGORIES
    home = _home(args)
    ev = ModelEvaluator(home)
    action = getattr(args, "eval_action", "run")
    if action == "tasks":
        for t in ev.tasks():
            print(f"    {t['category']:<14} {t['id']:<4} {t['prompt'][:80]}")
        info(f"  {len(ev.tasks())} graded task(s) across {len(set(t['category'] for t in ev.tasks()))} "
             f"categories: {', '.join(CATEGORIES)}")
        return 0
    if action == "history":
        print(ev.table(args.n))
        return 0
    if action == "gate":
        provider = args.provider or ""
        if not provider:
            chain = _router(home).build_chain()
            if not chain:
                fail("no provider available — add a key or start a local engine")
                return 1
            provider = chain[0].spec.name
        g = ev.gate(provider, args.model or "")
        print(json.dumps(g, indent=2))
        print(col.green("  GATE PASS — safe to promote") if g["pass"]
              else col.yellow("  GATE HOLD — one good run is not evidence"))
        return 0 if g["pass"] else 2
    # action == run
    cats = args.categories.split(",") if getattr(args, "categories", None) else None
    chain = _router(home).build_chain()
    if not chain and not args.provider:
        fail("no brain available to evaluate — add a key or start a local engine (`rad doctor`)")
        return 1
    probe = args.provider or chain[0].spec.name
    info(f"  evaluating {probe} — {len(ev.tasks(cats))} task(s) × {max(1, args.repeats)} repeat(s)…")
    try:
        rep = ev.run(provider=args.provider or "", model=args.model or "", categories=cats,
                     repeats=args.repeats, label=args.label or "")
    except Exception as e:
        fail(f"evaluation failed: {str(e)[:160]}")
        return 1
    print(ev.render(rep["provider"], rep["model"]))
    return 0


def cmd_regression(args) -> int:
    """Unit / security / agent / integration tests + a live agent and long-horizon benchmark subset."""
    from rad.regression import RegressionSystem
    home = _home(args)
    rs = RegressionSystem(home)
    action = getattr(args, "reg_action", "run")
    if action == "history":
        hist = rs.history(args.n)
        if not hist:
            info("  no regression runs yet — `rad regression`")
            return 0
        for h in hist:
            when = time.strftime("%m-%d %H:%M", time.localtime(h["at"]))
            v = h.get("verdict", {})
            print(f"  {col.dim(when)} {h.get('label', ''):<24} "
                  f"{col.green('PASS') if v.get('pass') else col.red('FAIL')} "
                  f"{'; '.join(v.get('problems', []))[:90]}")
        return 0
    if action == "show":
        latest = rs.latest()
        if not latest:
            info("  no regression runs yet — `rad regression`")
            return 0
        print(RegressionSystem.render(latest))
        return 0 if latest.get("verdict", {}).get("pass") else 2
    if action == "compare":
        hist = rs.history(2)
        if len(hist) < 2:
            fail("need two regression runs to compare")
            return 1
        cmp = RegressionSystem.compare(hist[1], hist[0])
        print(json.dumps(cmp, indent=2))
        return 0 if cmp["verdict"] == "ok" else 2
    groups = [g.strip() for g in (args.groups or "").split(",") if g.strip()] or None
    if args.quick:
        groups = ["security", "agent"]
        sample = min(args.sample, 4)
    else:
        sample = args.sample
    info(f"  running regression groups={groups or ['unit', 'security', 'agent', 'integration']} "
         f"sample={sample}…")
    rep = rs.run(groups=groups, sample=sample, benchmarks=not args.no_benchmarks,
                 label=args.label or "")
    print(RegressionSystem.render(rep))
    return 0 if rep["verdict"]["pass"] else 2



def cmd_acceptance(args) -> int:
    """The 50-item acceptance gate: every requirement demonstrated by running code."""
    from rad.acceptance import Gate, render
    home = _home(args)
    areas = [a.strip() for a in (args.area or "").split(",") if a.strip()] or None
    if areas:
        from rad.acceptance import AREAS
        bad = [a for a in areas if a not in AREAS]
        if bad:
            fail(f"unknown area(s) {bad}; valid: {', '.join(AREAS)}")
            return 1
    info(f"  running the acceptance gate{' on ' + ','.join(areas) if areas else ''} "
         f"— each item runs the real thing (objectives, crashes, MCP, API, browser)…")
    rep = Gate(home, full=args.full).run(areas=areas)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        print(render(rep))
    if rep["ok"]:
        ok(f"  acceptance gate PASSED ({rep['passed']}/{rep['total']} items) — evidence: {rep['report']}")
        return 0
    fail(f"  acceptance gate NOT satisfied: {rep['passed']}/{rep['total']} items "
         f"(failing: {', '.join(rep['failed'])})")
    info(f"  full evidence per item: {rep['report']}")
    return 2



def cmd_realworld(args) -> int:
    """The four end-to-end acceptance tests: research, coding, multi-agent, failure recovery."""
    from rad.realworld import RealWorldSuite
    home = _home(args)
    which = [w.strip() for w in (args.only or "").split(",") if w.strip()] or None
    info("  running whole goals through the real control plane (isolated home, real tools, no model "
         "calls needed)…")
    rep = RealWorldSuite(home, keep=args.keep).run(which)
    if args.json:
        print(json.dumps(rep, indent=2, default=str))
    else:
        print(RealWorldSuite.render(rep))
    return 0 if rep.get("ok") else 2


def cmd_needle_eval(args) -> int:
    """Optional Needle vs existing tool-router measurements. Never requires Needle."""
    from rad.needle_bench import render, run_bench
    home = _home(args)
    info("  measuring existing vs Needle tool-router (Needle is optional; missing engine is BLOCKED)…")
    rep = run_bench(home)
    if args.json:
        print(json.dumps(rep, indent=2, default=str))
    else:
        print(render(rep))
    if not rep.get("isolation_ok"):
        fail("  isolation checks failed — Needle must not execute or bypass the gate")
        return 2
    return 0


def cmd_status(args) -> int:
    """One screen: what RAD owns right now — objectives, jobs, memory, providers, storage."""
    from rad.control.objectives import ObjectiveStore
    from rad.control.events import EventLog
    from rad.health import last_class_c
    from rad.storage import Storage
    home = _home(args)
    as_json = getattr(args, "json", False)
    store = ObjectiveStore(home)
    objs = store.list()
    active = [o for o in objs if o.status in ("PENDING", "PLANNING", "RUNNING", "PAUSED")]
    mem_counts: dict = {}
    try:
        from rad.memory import Memory
        m = Memory(home)
        for layer in ("working", "episodic", "semantic", "procedural"):
            try:
                mem_counts[layer] = len(m.items(layer))
            except Exception:
                mem_counts[layer] = m.count(layer) if hasattr(m, "count") else 0
    except Exception as e:
        mem_counts = {"error": str(e)[:60]}
    chain = []
    try:
        chain = [f"{e.spec.name}:{e.model}" for e in _router(home).build_chain()]
    except Exception:
        pass
    st = Storage(home)
    st.pending()
    jobs = []
    try:
        from rad.jobs import Jobs
        jobs = Jobs(home).list()
    except Exception:
        pass
    board = []
    try:
        from rad.background import BackgroundRuntime
        board = BackgroundRuntime(home).list_routines()
    except Exception:
        pass
    with_errors = 0
    for o in objs[:50]:
        try:
            evs = list(EventLog(store.events_path(o.id)).read())
            if any(e.kind in ("RECOVERY_DECISION", "OBJECTIVE_FAILED") for e in evs):
                with_errors += 1
        except Exception:
            pass
    last_event = None
    try:
        recent = list(EventLog(home.root / "events.jsonl").read())[-1:] if (home.root / "events.jsonl").exists() else []
        last_event = {"kind": recent[0].kind, "at": recent[0].at} if recent else None
    except Exception:
        pass
    data = {"home": str(home.root), "workspace": str(home.workspace()),
            "version": __version__, "schema": st.version(),
            "objectives": {"total": len(objs), "active": len(active),
                           "with_failures": with_errors,
                           "by_status": {s: sum(1 for o in objs if o.status == s)
                                         for s in sorted({o.status for o in objs})}},
            "memory": mem_counts, "chain": chain, "jobs": len(jobs),
            "background_routines": len(board), "auto": bool(home.cfg.get("auto")),
            "last_event": last_event}
    if as_json:
        print(json.dumps(data, indent=2, default=str))
        return 0
    print(col.bold(f"  RAD {__version__}  (schema v{st.version()})"))
    print(f"    home       {data['home']}")
    print(f"    workspace  {data['workspace']}")
    print(f"    brain      {', '.join(chain) if chain else col.yellow('none — add a key or start a local engine')}")
    print(f"    auto       {data['auto']}")
    o = data["objectives"]
    print(f"    objectives {o['total']} total, {o['active']} active"
          + (f", {o['with_failures']} with failures/recovery" if o["with_failures"] else "")
          + (f"  {col.dim(o['by_status'])}" if o["by_status"] else ""))
    print(f"    memory     " + (", ".join(f"{k} {v}" for k, v in mem_counts.items()) or "empty"))
    print(f"    jobs       {len(jobs)}   background routines {len(board)}")
    if last_event:
        print(f"    last event {last_event['kind']} at {time.strftime('%H:%M:%S', time.localtime(last_event['at']))}")
    last_c = last_class_c(home)
    if last_c and last_c.get("class_c"):
        print(col.yellow(
            f"    last Class C {last_c.get('provider')} {last_c.get('kind')} "
            f"HTTP {last_c.get('status')} — `rad health` for pause/resume/campaign"))
    if active:
        print(col.bold("    active objectives:"))
        for obj in active[:8]:
            print(f"      {obj.id}  {col.cyan(obj.status):<16} {obj.goal[:64]}")
    return 0


def cmd_config(args) -> int:
    """Inspect and change RAD's configuration (the same file the runtime reads)."""
    home = _home(args)
    action = args.cfg_action
    path = home.config_path
    if action == "path":
        print(str(path))
        return 0
    if action == "get":
        if not args.key:
            fail("usage: rad config get <key>")
            return 1
        val = home.cfg.get(args.key)
        if val is None:
            info(f"  {args.key} is not set")
            return 1
        print(json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val))
        return 0
    if action == "unset":
        if not args.key:
            fail("usage: rad config unset <key>")
            return 1
        home.cfg.pop(args.key, None)
        home.save_config()
        ok(f"{args.key} removed")
        return 0
    if action == "set":
        if not args.key or args.value is None:
            fail("usage: rad config set <key> <value>   (value is JSON when possible)")
            return 1
        if args.key not in DEFAULTS:
            fail(f"unknown key {args.key!r} — `rad config show` lists the settings")
            return 1
        from rad.storage import validate_config
        try:
            val = json.loads(args.value)
        except Exception:
            val = args.value
            default = DEFAULTS[args.key]
            if isinstance(default, bool) and str(val).lower() in ("true", "false", "yes", "no", "on", "off"):
                val = str(val).lower() in ("true", "yes", "on")
        previous = home.cfg.get(args.key)
        home.cfg[args.key] = val
        issues = [i for i in validate_config(home.cfg) if i.key == args.key]
        if issues:
            home.cfg[args.key] = previous
            hint = ""
            if issues[0].fix not in (None, "__remove__"):
                hint = f" — valid example: {issues[0].fix!r}"
            fail(f"{args.key}: {issues[0].problem} (value {issues[0].value!r}){hint}")
            return 1
        home.save_config()
        ok(f"{args.key} = {json.dumps(val) if not isinstance(val, str) else val}")
        return 0
    data = dict(home.cfg)
    for secret_key in ("keys", "api_keys", "tokens"):
        data.pop(secret_key, None)
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    print(col.dim(f"  file: {path}"))
    return 0


def cmd_security(args) -> int:
    """What is enforced right now: policy, capabilities, sandbox, audit, secrets, rate limits."""
    from rad.policy import Policy, BUILTIN_DEFAULTS
    from rad.agents import ALL_CAPS
    home = _home(args)
    pol = Policy(home)
    if getattr(args, "json", False):
        print(json.dumps({"model": "capability policies evaluated per action (ALLOW/ASK/LIMITED/DENY/HARD_DENY)",
                          "defaults": {c: pol.default_for(c) for c in BUILTIN_DEFAULTS},
                          "rules": [r.to_dict() for r in pol.rules],
                          "web_allow": pol._data.get("web_allow", []),
                          "audit_tail": pol.audit_tail(10)}, indent=2, default=str))
        return 0
    print(col.bold("  enforcement layers"))
    print("    1 identity      user | agent:<id> | control:<objective> — every action carries an actor")
    print("    2 policy        capability → ALLOW/ASK/LIMITED/DENY (soft, editable) + hard denials (not editable)")
    print("    3 sandbox       filesystem jail + limits (timeout, bytes, network grants) around execution")
    print("    4 confirmation  ASK actions require an explicit yes unless auto is enabled")
    print("    5 audit         every decision appended to ~/.rad/audit.jsonl")
    print(col.bold("\n  capability defaults"))
    for cap in sorted(BUILTIN_DEFAULTS):
        print(f"    {cap:<24} {pol.default_for(cap)}")
    if pol.rules:
        print(col.bold("\n  rules"))
        for r in pol.rules[:20]:
            print(f"    {r.capability:<24} {r.effect:<9} {r.resource[:40]}"
                  + (f"  limits={r.limits}" if getattr(r, 'limits', None) else ""))
    else:
        print(col.dim("\n  no custom rules — defaults above are in force"))
    print(col.bold("\n  hard limits (never overridable)"))
    for line in ("sudo / su", "reads or writes under ~/.rad/keys, ~/.ssh, key material",
                 "private/loopback hosts from tools unless explicitly allowed",
                 "curl|sh style pipe-to-shell and destructive rm -rf"):
        print(f"    ✗ {line}")
    print(col.bold("\n  agent capability envelope"))
    print(f"    known capabilities: {', '.join(sorted(ALL_CAPS))}")
    print("    sub-agents may narrow this set, never widen it; they cannot edit policy, skills or their own caps")
    tail = pol.audit_tail(5)
    print(col.bold("\n  recent decisions"))
    if not tail:
        print(col.dim("    (nothing audited yet)"))
    for a in tail:
        print(f"    {time.strftime('%H:%M:%S', time.localtime(a.get('at', time.time())))} "
              f"{a.get('effect', '?'):<9} {str(a.get('capability', '')):<16} {str(a.get('resource', ''))[:44]}")
    return 0


def cmd_tools(args) -> int:
    """Every tool RAD's hands can call, with the capability each one requires."""
    from rad.tools import TOOLS
    from rad.agents import cap_for_tool
    from rad.policy import Policy
    home = _home(args)
    pol = Policy(home)
    rows = []
    for t in TOOLS:
        fn = t.get("function", t)
        name = fn.get("name", "?")
        cap = cap_for_tool(name)
        rows.append({"name": name, "capability": cap,
                     "policy": pol.default_for(cap),
                     "description": (fn.get("description") or "").split(".")[0][:60]})
    try:
        from rad.mcp import MCP  # type: ignore
        for name in MCP(home).tool_names():
            rows.append({"name": name, "capability": "mcp",
                         "policy": pol.default_for("mcp"), "description": "MCP skill tool"})
    except Exception:
        pass
    if getattr(args, "json", False):
        print(json.dumps({"tools": rows}, indent=2))
        return 0
    print(col.bold(f"  {len(rows)} tool(s) — policy is evaluated per call, not per tool"))
    for r in sorted(rows, key=lambda x: (x["capability"], x["name"])):
        print(f"    {r['name']:<22} {r['capability']:<10} {r['policy']:<8} {col.dim(r['description'])}")
    print(col.dim("    call them through chat, `rad objective run`, or `rad agents run <role>`"))
    print(col.dim("    change permission: rad policy allow|ask|deny|limit <capability> <resource>"))
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
        from rad.integrate.hooks import promotion_gate
        bench = Benchmark(home)
        info("  benchmark battle: candidate vs current brain…")
        try:
            res = b.promote(args.name, bench, margin=args.margin)
            if res["promoted"]:
                ok(f"PROMOTED: {res['candidate']} — {res['new']} vs {res['old']} (margin {args.margin})")
            else:
                warn(f"rejected: {res['candidate']} — {res['new']} vs current {res['old']} "
                     f"(needs +{args.margin}). The throne stands.")
            return 0
        except PermissionError as e:
            fail(f"PROMOTION BLOCKED by gate: {e}")
            return 1
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
    c.add_argument("--voice", action="store_true", help="voice mode: speak + listen (auto TEN→Piper/Whisper→text fallback)")
    c.add_argument("--voice-backend", default="auto", choices=["auto", "ten", "fallback", "text"],
                   help="voice backend: auto (TEN realtime if available, else Piper/Whisper fallback), ten, fallback, text")
    c.add_argument("--auto", action="store_true",
                   help="confirmation policy = never (ASK→ALLOW only; does not bypass DENY/hard/budget)")
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
    co = sub.add_parser("cost", help="paid spend + objective usage rollup"); co.set_defaults(fn=cmd_cost)

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
    sl.add_argument("--evolve", action="store_true", help="nightly EvolveMem AutoResearch: diagnose retrieval failures -> propose tweak -> lab-gated promotion (requires memory.evolve true)")
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

    sv = sub.add_parser("serve", help="local JSON API over the control plane (loopback, bearer token)")
    sv.add_argument("--port", type=int, default=None); sv.add_argument("--host", default=None)
    sv.add_argument("--rotate-token", action="store_true"); sv.add_argument("--i-know-this-exposes-rad", action="store_true")
    sv.set_defaults(fn=cmd_serve)

    desk = sub.add_parser("desktop", help="RAD Desktop 1.0.1 — launch or print the Tauri surface path")
    desk.set_defaults(fn=cmd_desktop)

    web = sub.add_parser("web", help="RAD Web UI — launch the Rust + JS web browser interface")
    web.add_argument("--port", type=int, default=3000, help="web interface port (default 3000)")
    web.add_argument("--api-port", type=int, default=7331, help="RAD backend API port (default 7331)")
    web.add_argument("--no-open", action="store_true", help="do not automatically open browser")
    web.set_defaults(fn=cmd_web)

    dr = sub.add_parser("doctor", help="health check of RAD; --fix repairs what is safe")
    dr.add_argument("--fix", action="store_true"); dr.add_argument("--offline", action="store_true", help="skip provider probes")
    dr.add_argument("--force", action="store_true",
                    help="re-ping chat even if last Class C still blocks (quota-unsafe)")
    dr.add_argument("--json", action="store_true")
    dr.set_defaults(fn=cmd_doctor)

    hl = sub.add_parser("health", help="live-use campaign: last Class C, live-gate, pause/resume next-action")
    hl.add_argument("--force", action="store_true",
                    help="re-ping chat even if last Class C still blocks (quota-unsafe)")
    hl.add_argument("--campaign", action="store_true", help="print the live-use campaign playbook")
    hl.add_argument("--json", action="store_true")
    hl.set_defaults(fn=cmd_health)

    so = sub.add_parser("storage", help="schema/migrations/integrity/snapshots of ~/.rad")
    so.add_argument("storage_action", nargs="?", default="status",
                    choices=["status", "migrate", "check", "snapshot", "snapshots", "restore"])
    so.add_argument("--dry-run", action="store_true"); so.add_argument("--repair", action="store_true")
    so.add_argument("--label", default=None); so.add_argument("--include-keys", action="store_true")
    so.add_argument("--yes", "-y", action="store_true")
    so.set_defaults(fn=cmd_storage)

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

    sk = sub.add_parser("skills", help="connected skills: list | audit | approve <name> [allow|ask|deny] | declare | manifest")
    sk.add_argument("skills_action", nargs="?", default="list", choices=["list", "audit", "approve", "declare", "manifest", "evolve"])
    sk.add_argument("skills_args", nargs="*"); sk.set_defaults(fn=cmd_skills)
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

    tc = sub.add_parser("triage-corpus", help="objectives history → auto/escalate labels")
    tc.add_argument("corpus_action", nargs="?", default="show", choices=["show", "export"])
    tc.add_argument("--out", default=None)
    tc.set_defaults(fn=cmd_triage_corpus)

    bm = sub.add_parser("benchmark", help="capability battery — is Rad smarter? now it's a number")
    bm.add_argument("bench_action", nargs="?", default="run",
                    choices=["run", "bank", "long", "history", "compare"])
    bm.add_argument("--provider", default=None); bm.add_argument("--model", default=None)
    bm.add_argument("--cats", default=None, help="comma list: math,logic,code,tool,json,summarize,style")
    bm.add_argument("--label", default=None)
    bm.add_argument("--category", default=None,
                    help="bank: reasoning | tool_use | coding | research | planning | long_horizon | "
                         "recovery | memory | adversarial | all")
    bm.add_argument("--sample", type=int, default=0, help="bank/long: run only N scenarios (0 = all)")
    bm.add_argument("--seed", type=int, default=20260917, help="bank/long: sampling seed")
    bm.add_argument("-n", type=int, default=10, help="history: how many runs")
    bm.set_defaults(fn=cmd_benchmark)

    ev = sub.add_parser("evaluate", help="model evaluation battery: planning/memory/long-context/"
                                         "research/instruction/safety/recovery + history + promotion gate")
    ev.add_argument("eval_action", nargs="?", default="run", choices=["run", "history", "gate", "tasks"])
    ev.add_argument("--provider", default=None, help="evaluate one provider (default: current chain head)")
    ev.add_argument("--model", default=None)
    ev.add_argument("--categories", default=None, help="comma list of capability areas")
    ev.add_argument("--repeats", type=int, default=1, help="run every task N times to measure stability")
    ev.add_argument("--label", default=None)
    ev.add_argument("-n", type=int, default=8, help="history: how many runs")
    ev.set_defaults(fn=cmd_evaluate)

    acc = sub.add_parser("acceptance", help="the 50-item acceptance gate: every requirement "
                                            "demonstrated by running code, with per-item evidence")
    acc.add_argument("--area", default=None, help=f"comma list of areas (runtime, control, state, "
                                                  f"memory, agents, security, routing, ops, "
                                                  f"benchmarks, docs)")
    acc.add_argument("--json", action="store_true", help="machine-readable report with evidence")
    acc.add_argument("--full", action="store_true", help="also run the wide benchmark sample")
    acc.set_defaults(fn=cmd_acceptance)

    rg = sub.add_parser("regression", help="unit/integration/security/agent tests + live agent and "
                                           "long-horizon benchmark subset, with a pass/fail verdict")
    rg.add_argument("reg_action", nargs="?", default="run", choices=["run", "history", "show", "compare"])
    rg.add_argument("--groups", default=None, help="comma list: unit,security,agent,integration")
    rg.add_argument("--sample", type=int, default=6, help="scenarios per live benchmark")
    rg.add_argument("--quick", action="store_true", help="security+agent groups, 4 scenarios")
    rg.add_argument("--no-benchmarks", action="store_true", help="tests only, skip the live lab runs")
    rg.add_argument("--label", default=None)
    rg.add_argument("-n", type=int, default=15)
    rg.set_defaults(fn=cmd_regression)

    rwp = sub.add_parser("realworld", help="end-to-end acceptance tests: research, coding, "
                                           "multi-agent, failure, filesystem, multi-step, honesty")
    rwp.add_argument("--only", default=None,
                     help="comma list: research,coding,multi_agent,failure,filesystem,multi_step,"
                          "false_success,needs_user,no_loop,overdecompose,live_nim")
    rwp.add_argument("--json", action="store_true")
    rwp.add_argument("--keep", action="store_true", help="keep the temporary workspaces")
    rwp.set_defaults(fn=cmd_realworld)

    ne = sub.add_parser("needle-eval", help="optional Needle vs existing tool-router measurements")
    ne.add_argument("--json", action="store_true")
    ne.set_defaults(fn=cmd_needle_eval)

    stp = sub.add_parser("status", help="one screen: objectives, memory, brain, jobs, background, schema")
    stp.add_argument("--json", action="store_true")
    stp.set_defaults(fn=cmd_status)

    cf = sub.add_parser("config", help="show/get/set/unset RAD configuration")
    cf.add_argument("cfg_action", nargs="?", default="show", choices=["show", "get", "set", "unset", "path"])
    cf.add_argument("key", nargs="?", default=None)
    cf.add_argument("value", nargs="?", default=None)
    cf.set_defaults(fn=cmd_config)

    secp = sub.add_parser("security", help="enforcement layers, capability defaults, hard limits, audit")
    secp.add_argument("--json", action="store_true")
    secp.set_defaults(fn=cmd_security)

    tlp = sub.add_parser("tools", help="tools RAD can call + the capability each one needs")
    tlp.add_argument("--json", action="store_true")
    tlp.set_defaults(fn=cmd_tools)

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
    pl.add_argument("--auto", action="store_true",
                    help="confirmation policy = never (ASK→ALLOW only; not a policy bypass)")
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
    wo.add_argument("--assume", action="store_true",
                    help="add: record a working assumption (origin ASSUMPTION), not a fact")
    wo.set_defaults(fn=cmd_world)

    co = sub.add_parser("connectome", help="RadConnectome — fruit fly brain wiring (neuPrint for agents)")
    co.add_argument("connectome_action", nargs="?", default="show",
                    choices=["show", "ingest", "query", "path", "hubs",
                             "projectome", "suggest", "replay"])
    co.add_argument("connectome_term", nargs="*")
    co.set_defaults(fn=cmd_connectome)

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
            fail("usage: rad world add <sentence about your world> [--assume]")
            return 1
        if getattr(args, "assume", False):
            n = w.assume(sentence)
            ok(f"recorded {n} assumption(s) — `rad world show` marks them, "
               f"`rad world confirm` promotes one to fact" if n else "nothing new assumed")
            return 0
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


def _argv_has_subcommand(argv: List[str], choices: set) -> bool:
    """True if a real subcommand appears after any leading global flags (`--home VALUE`)."""
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            return True
        if a == "--home":
            i += 2
            continue
        return a in choices
    return False


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    choices = set(parser._subparsers._group_actions[0].choices)
    # no subcommand (or a chat flag first) → chat. Keep `--home VALUE` in front of
    # the injected command so `rad --home <dir> lab run` and `rad --home <dir>` both work.
    if argv and argv[0] not in ("-h", "--help") and not _argv_has_subcommand(argv, choices):
        insert_at = 0
        if argv[0] == "--home":
            insert_at = 2 if len(argv) >= 2 else 1
        argv = argv[:insert_at] + ["chat"] + argv[insert_at:]
    elif not argv:
        argv = ["chat"]
    args = parser.parse_args(argv)
    if getattr(args, "fn", None) not in (cmd_storage, cmd_doctor):
        try:
            from rad.storage import Storage
            home = _home(args)
            st = Storage(home)
            if st.pending():
                done = st.migrate()
                if done and not done[0]["name"].startswith("fresh home"):
                    info(f"  storage migrated to v{st.version()} ({len(done)} step(s); snapshot in ~/.rad/backups)")
        except Exception as e:                     # never block the CLI on housekeeping
            warn(f"  storage migration skipped: {str(e)[:80]} (run `rad doctor`)")
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
