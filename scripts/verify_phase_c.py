#!/usr/bin/env python3
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
