#!/usr/bin/env python3
"""build_phase_c.py — gate becomes load-bearing + CLI surface + regression pin.

SHIPS
  rad/integrate/promote_patch.py   wire_promote_gate() decorator + probe tasks
  rad/cli_ext.py                   rad paper|relay|sovereignty|federation verbs
  scripts/verify_phase_c.py        10 checks incl. falsy-config regression pin
                                   + load-bearing probe (honest PENDING state)
RUN
  python build_phase_c.py --verify
"""
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "phaseC_staging"
FILES = {}

FILES["rad/cli_ext.py"] = r'''"""rad cli_ext — contribution command surface, dispatcher-agnostic.

Wire into ANY dispatcher with one call:  register_on(dispatcher)
Or run standalone:                       python -m rad.cli_ext <verb> [...]

L5: every store path injectable — CLI never hardcodes home in tests.
"""
import argparse, json, sys
from pathlib import Path

COMMANDS = {}          # L1: registry dict, not name-scan

def command(name, help_=""):
    def deco(fn):
        COMMANDS[name] = {"fn": fn, "help": help_}
        return fn
    return deco

def register_on(dispatcher) -> dict:
    """One-line hook: your dispatcher gets every verb in COMMANDS."""
    for name, spec in COMMANDS.items():
        dispatcher[name] = spec["fn"]
    return COMMANDS

# ---------------- paper verbs ----------------

@command("paper-add", "ingest a paper: paper-add <arxiv-id|url>")
def paper_add(args, papers_dir: Path | None = None):
    from rad.papers.ingest import ingest_paper, PAPERS_DIR
    if papers_dir:
        import rad.papers.ingest as ing
        ing.PAPERS_DIR = Path(papers_dir)
    meta = ingest_paper(args[0])
    print(f"[ok] ingested: {meta['title']}\n  slug={meta['slug']} sha256={meta['sha256'][:16]} chars={meta['char_count']}")
    print(f"  next: python -m rad.cli_ext paper-card {meta['slug']}")
    return meta

@command("paper-list", "list ingested papers")
def paper_list(args, papers_dir: Path | None = None):
    from rad.papers import ingest as ing, cards as cds
    if papers_dir:
        ing.PAPERS_DIR = Path(papers_dir); cds.PAPERS_DIR = ing.PAPERS_DIR
    papers = ing.list_papers()
    if not papers:
        print("no papers — try: paper-add 2501.12948"); return []
    for p in papers:
        card = cds.get_card(p["slug"])
        status = card["status"] if card else "ingested"
        print(f"  [{status:>10}] {p['slug']:<24} {p['title'][:56]}")
    return papers

@command("paper-card", "show/create technique card: paper-card <slug> [--create]")
def paper_card(args, papers_dir: Path | None = None, brain_fn=None):
    from rad.papers import ingest as ing, cards as cds
    if papers_dir:
        ing.PAPERS_DIR = Path(papers_dir); cds.PAPERS_DIR = ing.PAPERS_DIR
    slug = args[0]
    if "--create" in args:
        if brain_fn is None:
            from rad.home import RadHome
            from rad.router import BrainRouter
            from rad.integrate.hooks import make_brain_fn
            brain_fn = make_brain_fn(BrainRouter(home=RadHome()))
        from rad.papers.extract import extract_card_brain
        card = extract_card_brain(slug, brain_fn)
        print(f"[ok] card {card['card_id']} ({card['status']}) — quotes verified: "
              f"{sum(1 for c in card['claims'] if c['quote_verified'])}/{len(card['claims'])}")
        return card
    card = cds.get_card(slug)
    print(json.dumps(card, indent=2) if card else f"no card for {slug!r}")
    return card

@command("paper-ledger", "replication ledger: paper-ledger [--export PATH]")
def paper_ledger(args, papers_dir: Path | None = None):
    from rad.papers import ledger as ldg
    if papers_dir:
        ldg.PAPERS_DIR = Path(papers_dir)
        ldg.LEDGER_FILE = ldg.PAPERS_DIR / "_ledger.jsonl"
    entries = ldg.read_ledger()
    if not entries:
        print("ledger empty — completed battles land here"); return []
    for e in entries:
        icon = {"CONFIRMED": "[+]", "NOT_REPLICATED": "[!]", "NO_CLAIM_TO_TEST": "[-]"}.get(e["replication_verdict"], "[?]")
        print(f"  {icon} {e['paper_title'][:48]:<48} -> {e['replication_verdict']}")
    if "--export" in args:
        out = args[args.index("--export") + 1]
        ldg.export_ledger(out); print(f"  exported -> {out}")
    return entries

# ---------------- relay / sovereignty / federation ----------------

@command("relay-test", "classify + route a prompt through Relay: relay-test \"text\" [--open]")
def relay_test(args):
    from rad.routing.relay import classify_request, route
    text = args[0] if args else "fix this python bug in my api"
    pref = "open" if "--open" in args else "default"
    cls = classify_request(text)
    dec = route(cls, policy_pref=pref)
    print(f"  class={cls['task_class']} decided_in={cls['decision_ms']}ms")
    print(f"  route: {dec['route_selected']}  chain={dec['fallback_chain']}")
    return dec

@command("sovereignty", "HEARTH report: sovereignty [objective-dir]")
def sovereignty(args):
    from rad.sovereignty.audit import audit_objective
    rep = audit_objective(Path(args[0]) if args else None)
    print(f"  objectives={rep['objectives']} fully_internal={rep['fully_sovereign']} "
          f"internal_ratio={rep['internal_ratio']}")
    print(f"  port_calls={rep['port_calls']}")
    print(f"  law: {rep['law']}")
    return rep

@command("federation-status", "federation bundles/verdicts summary")
def federation_status(args):
    from rad.home import RadHome
    base = RadHome().root / "federation" if Path.home().joinpath(".rad").exists() else None
    print("  federation state: wire cross_audit runs into your task loop; "
          "verdicts land in the cross-ledger (RFC-005 P4)")
    return {"note": "P4 pending"}

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print("rad cli_ext — contribution verbs:\n")
        for name, spec in COMMANDS.items():
            print(f"  {name:<20} {spec['help']}")
        return 0
    verb, rest = argv[0], argv[1:]
    if verb not in COMMANDS:
        print(f"unknown verb {verb!r}; try --help"); return 1
    COMMANDS[verb]["fn"](rest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

FILES["rad/integrate/promote_patch.py"] = r'''"""promote_patch — make the promotion gate LOAD-BEARING with one line.

Instead of editing the promote handler body:

    from rad.integrate.promote_patch import wire_promote_gate
    promote = wire_promote_gate(home)(promote)          # wrapped, gated forever

The wrapper runs promotion_gate (canary + contamination + integrity flag)
BEFORE the wrapped promote. PermissionError propagates -> promote dies closed.

Probe tasks: probe_tasks_from_battery() samples real battery items when
exposed; fallback_probe_tasks() = 6 deterministic offline-checkable probes.
"""
import functools
from pathlib import Path

def fallback_probe_tasks() -> list:
    """6 deterministic probes covering battery categories; graders are
    self-contained (no network, no keys) so canary deltas are real."""
    return [
        {"task_id": "probe-math",     "prompt": "compute 17*23 and write to answer.txt",
         "grader": {"file_contains": [{"path": "answer.txt", "any": ["391"], "none": []}]}},
        {"task_id": "probe-json",     "prompt": "write {\"ok\": true} to out.json",
         "grader": {"json_checks": [{"path": "out.json", "field": "ok", "op": "eq", "value": True}]}},
        {"task_id": "probe-logic",    "prompt": "write the sorted list [3,1,2] to s.txt as 1,2,3",
         "grader": {"file_contains": [{"path": "s.txt", "any": ["1,2,3"], "none": []}]}},
        {"task_id": "probe-code",     "prompt": "write a python function add(a,b) to add.py",
         "grader": {"must_exist": ["add.py"],
                    "file_contains": [{"path": "add.py", "any": ["def add"], "none": []}]}},
        {"task_id": "probe-summarize","prompt": "write the word SUMMARY to t.txt",
         "grader": {"file_contains": [{"path": "t.txt", "any": ["SUMMARY"], "none": []}]}},
        {"task_id": "probe-honesty",  "prompt": "if you cannot write files, say so; else write ok.txt",
         "grader": {"on": "disk_only",
                    "events_must_include": ["objective_status:NEEDS_USER|wrote:ok.txt|write:ok.txt"]}},
    ]

def probe_tasks_from_battery(battery, n: int = 6) -> list:
    """Sample real battery items if the class exposes them; else fallback.
    Honest degradation: never fabricate items — fall back with a note."""
    try:
        items = getattr(battery, "items", None) or getattr(battery, "sample_items", None)
        if callable(items):
            items = items(n)
        if items:
            out = []
            for it in items[:n]:
                out.append({"task_id": str(it.get("id", it.get("task_id", "probe"))),
                            "prompt": str(it.get("prompt", it.get("question", "")))})
            if out:
                return out
    except Exception:
        pass
    return fallback_probe_tasks()

def wire_promote_gate(home, *, battery=None, tasks=None, margin: float = 10.0,
                      check_canary: bool = True, check_contamination: bool = True,
                      strict: bool = True):
    """Decorator factory. Usage at promote definition/dispatch:
        promote = wire_promote_gate(home)(promote)
    strict=True (default): gate failure raises -> promote never runs.
    strict=False: gate failure returns {"blocked": reason} instead
    (for dispatchers that can't propagate exceptions)."""
    def deco(promote_fn):
        @functools.wraps(promote_fn)
        def wrapped(*a, **k):
            from rad.integrate.hooks import promotion_gate, make_battery_fn
            from rad.battery import CapabilityBattery
            root = Path(getattr(home, "root", getattr(home, "base_dir", Path.home() / ".rad")))
            b = battery or CapabilityBattery(home=home)
            probe = tasks or probe_tasks_from_battery(b)
            try:
                promotion_gate(
                    corpus_dir=root / "corpus",
                    battery_dir=root / "battery",
                    battery_fn=make_battery_fn(b),
                    current_config=_current_config(home) or {},   # even {} runs canary
                    tasks=probe,
                    margin=margin,
                    check_canary=check_canary,
                    check_contamination=check_contamination,
                    results_dir=root / "battery",
                )
            except PermissionError as e:
                if strict:
                    raise
                return {"blocked": str(e), "promoted": False}
            return promote_fn(*a, **k)
        wrapped.__gated__ = True
        return wrapped
    return deco

def _current_config(home) -> dict:
    """Read the current brain (provider/model) from home if discoverable.
    Returns {} when unknown — gate still runs canary (config is not None)."""
    try:
        cur = getattr(home, "current_brain", None) or getattr(home, "brain_current", None)
        if cur:
            return {"provider": getattr(cur, "provider", None),
                    "model": getattr(cur, "model", None)}
    except Exception:
        pass
    return {}

def load_bearing_probe(search_root: Path) -> dict:
    """Scan the promote path source for gate usage. Honest three-state."""
    hits = []
    for f in Path(search_root).rglob("*.py"):
        f_res = f.resolve()
        f_str = str(f_res).replace("\\", "/")
        if "/integrate/" in f_str or f_res.name == "acceptance.py":
            continue  # exclude the gate's own modules and acceptance suite naming collision
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "def cmd_brain" in src or "brain promote" in src or "def promote" in src:
            if "promotion_gate" in src or "wire_promote_gate" in src:
                hits.append(str(f))
    return {"load_bearing": bool(hits), "files": hits,
            "state": "WIRED" if hits else "PENDING — apply wire_promote_gate in promote path"}
'''

VERIFY = r'''#!/usr/bin/env python3
"""Phase C verification — 10 checks. Includes the FOREVER regression pin for
the falsy-config fail-open bug, and the honest load-bearing state probe."""
import json, sys, tempfile, traceback
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if not (ROOT / "rad" / "papers").exists() and (ROOT.parent / "rad" / "papers").exists():
    sys.path.insert(0, str(ROOT.parent))
    try:
        import rad
        staging_rad = ROOT / "rad"
        if staging_rad.exists() and str(staging_rad) not in rad.__path__:
            rad.__path__.append(str(staging_rad))
        staging_int = ROOT / "rad" / "integrate"
        if staging_int.exists():
            import rad.integrate
            if str(staging_int) not in rad.integrate.__path__:
                rad.integrate.__path__.append(str(staging_int))
    except Exception:
        pass

CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn)); return fn
    return deco

@check("REGRESSION PIN: promotion_gate with current_config={} MUST run canary (never fail-open)")
def regression_falsy_config():
    from rad.integrate.hooks import promotion_gate
    tmp = Path(tempfile.mkdtemp())
    ran = {"canary": False}
    def battery_fn(cfg, t, s):
        ran["canary"] = True
        return {"score": 90 if cfg.get("max_tokens") != 24 else 10}
    rep = promotion_gate(battery_fn=battery_fn, current_config={},
                         tasks=[{"task_id": "t"}], results_dir=tmp,
                         check_contamination=False)
    assert ran["canary"] is True, "EMPTY CONFIG SKIPPED THE CANARY — fail-open regressed!"
    assert rep["gates_passed"] is True and rep["canary"]["battery_healthy"]

@check("promote_patch: wire blocks broken-battery promote (promote fn never called)")
def wire_blocks():
    from rad.integrate.promote_patch import wire_promote_gate
    home = NS(root=Path(tempfile.mkdtemp()))
    called = {"promote": False}
    bad = lambda cfg, t, s: {"score": 95 if cfg.get("max_tokens") == 24 else 40}
    class FakeBattery:
        items = None
        def run(self, **kw):
            cfg = kw
            return bad(cfg, None, 0)
    w = wire_promote_gate(home, battery=FakeBattery(), tasks=[{"task_id": "t"}])
    @w
    def promote(*a, **k):
        called["promote"] = True
        return "promoted!"
    try:
        promote(); raise AssertionError("must have raised")
    except PermissionError as e:
        assert "canary" in str(e)
    assert called["promote"] is False, "gated promote must not run"

@check("promote_patch: clean gate lets promote through, result returned, __gated__ marked")
def wire_passes():
    from rad.integrate.promote_patch import wire_promote_gate
    home = NS(root=Path(tempfile.mkdtemp()))
    good = lambda cfg, t, s: {"score": 90 if cfg.get("max_tokens") != 24 else 10}
    class FakeBattery:
        items = None
        def run(self, **kw):
            cfg = kw
            return good(cfg, None, 0)
    @wire_promote_gate(home, battery=FakeBattery(), tasks=[{"task_id": "t"}])
    def promote(x): return f"promoted:{x}"
    assert promote("A") == "promoted:A"
    assert getattr(promote, "__gated__", False) is True

@check("promote_patch: strict=False returns blocked-dict instead of raising")
def wire_soft_mode():
    from rad.integrate.promote_patch import wire_promote_gate
    home = NS(root=Path(tempfile.mkdtemp()))
    bad = lambda cfg, t, s: {"score": 99 if cfg.get("max_tokens") == 24 else 1}
    class FakeBattery:
        items = None
        def run(self, **kw):
            cfg = kw
            return bad(cfg, None, 0)
    @wire_promote_gate(home, battery=FakeBattery(), tasks=[{"task_id": "t"}], strict=False)
    def promote(): return "should not reach"
    r = promote()
    assert isinstance(r, dict) and r["promoted"] is False and "blocked" in r

@check("promote_patch: fallback probe tasks — 6, deterministic, self-contained graders")
def probe_tasks():
    from rad.integrate.promote_patch import fallback_probe_tasks as f
    t1, t2 = f(), f()
    assert t1 == t2 and len(t1) == 6
    ids = {x["task_id"] for x in t1}
    assert len(ids) == 6 and "probe-honesty" in ids

@check("promote_patch: probe_tasks_from_battery degrades honestly when no items")
def probe_degrade():
    from rad.integrate.promote_patch import probe_tasks_from_battery
    class Empty: items = None
    assert len(probe_tasks_from_battery(Empty())) == 6      # fallback used
    class Rich: items = [{"id": "b1", "prompt": "p1"}, {"id": "b2", "prompt": "p2"}]
    got = probe_tasks_from_battery(Rich())
    assert got == [{"task_id": "b1", "prompt": "p1"}, {"task_id": "b2", "prompt": "p2"}]

@check("cli_ext: registry verbs present; paper-list/sovereignty run against tmp dirs")
def cli_verbs():
    from rad import cli_ext
    for v in ("paper-add", "paper-list", "paper-card", "paper-ledger",
              "relay-test", "sovereignty", "federation-status"):
        assert v in cli_ext.COMMANDS, v
    tmp = Path(tempfile.mkdtemp())
    (tmp / "p1").mkdir()
    (tmp / "p1" / "meta.json").write_text(json.dumps(
        {"slug": "p1", "title": "Some Paper", "source_url": "u", "sha256": "x"}), encoding="utf-8")
    from io import StringIO
    import contextlib
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        out = cli_ext.COMMANDS["paper-list"]["fn"]([], papers_dir=tmp)
    assert len(out) == 1 and out[0]["slug"] == "p1"
    assert "ingested" in buf.getvalue()
    # dispatcher hook pattern
    disp = {}
    cli_ext.register_on(disp)
    assert set(disp) == set(cli_ext.COMMANDS)

@check("cli_ext: relay-test returns decision dict; --open prefers local")
def cli_relay():
    from rad import cli_ext
    from io import StringIO
    import contextlib
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        dec = cli_ext.COMMANDS["relay-test"]["fn"](["fix my python api bug", "--open"])
    assert dec["route_selected"] == "ollama-local", dec

@check("LOAD-BEARING PROBE: honest state of promote-path wiring")
def load_bearing():
    from rad.integrate.promote_patch import load_bearing_probe
    state = load_bearing_probe(ROOT / "rad")
    # honest three-state output; never silently green
    print(f"\n       [probe] promote-path wiring: {state['state']} {state['files']}")
    assert state["state"] in ("WIRED", "PENDING")
    # PENDING does not fail the suite — but it is printed, always visible.

@check("imports: phase-C modules importable")
def imports():
    import importlib
    errs = []
    for m in ["rad.cli_ext", "rad.integrate.promote_patch", "rad.integrate.hooks"]:
        try: importlib.import_module(m)
        except Exception as e: errs.append(f"{m}: {e}")
    assert not errs, errs

def main():
    print(f"\n=== PHASE C VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:
        try:
            fn(); print(f"  PASS  {name}")
        except Exception:
            fails += 1; print(f"  FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(CHECKS)-fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
'''

def main():
    do_verify = "--verify" in sys.argv
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    vp = STAGE / "scripts" / "verify_phase_c.py"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(VERIFY.lstrip("\n"), encoding="utf-8")
    print(f"[build] {len(written)} modules + verifier -> {STAGE}")
    for w in written: print(f"  + {w}")
    print("  + scripts/verify_phase_c.py")
    if not do_verify:
        print("\nNext: python build_phase_c.py --verify"); return
    import subprocess
    res = subprocess.run([sys.executable, str(vp)], cwd=str(STAGE.parent))
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
