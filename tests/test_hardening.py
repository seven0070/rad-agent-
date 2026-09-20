"""Phase 9 hardening: config schema, storage migrations on legacy data, integrity + quarantine,
snapshot/restore, rad doctor (report vs --fix), and a corrupt-file sweep proving subsystems
degrade instead of crashing."""
import json
import os
import tarfile

import pytest

from rad.doctor import Doctor
from rad.home import RadHome
from rad.storage import SCHEMA_VERSION, Storage, validate_config


# ---------------------------------------------------------------- config

def test_validate_config_types_ranges_enums_unknown(home):
    assert validate_config(home.cfg) == []
    cfg = dict(home.cfg, auto="yes", objective_parallel=99, tts="loud", bogus=1, ollama_url="ftp://x", workspace="/definitely/missing")
    issues = {i.key: i for i in validate_config(cfg)}
    assert issues["auto"].fix is False and "bool" in issues["auto"].problem
    assert issues["objective_parallel"].fix == 8
    assert issues["tts"].fix == "auto"
    assert issues["bogus"].fix == "__remove__"
    assert "http" in issues["ollama_url"].problem
    assert "does not exist" in issues["workspace"].problem and issues["workspace"].fix is None


def test_doctor_reports_then_fixes_config(home):
    home.cfg.update({"auto": "yes", "objective_parallel": 99, "bogus": 1}); home.save_config()
    d = {f.check: f for f in Doctor(home, fix=False, probe_network=False).run()}
    assert d["config"].status == "warn" and not d["config"].fixed
    assert json.loads(home.config_path.read_text())["auto"] == "yes"          # report mode changed nothing
    d = {f.check: f for f in Doctor(home, fix=True, probe_network=False).run()}
    assert d["config"].fixed and d["config"].status == "ok"
    cfg = json.loads(home.config_path.read_text())
    assert cfg["auto"] is False and cfg["objective_parallel"] == 8 and "bogus" not in cfg


# ---------------------------------------------------------------- migrations

def _legacy_home(tmp_path) -> RadHome:
    """Build a home shaped like pre-Memory-2.0 RAD: memory files without provenance front-matter,
    a DNA generation without history, a world graph without origin."""
    root = tmp_path / "legacy"
    h = RadHome(str(root))
    mem = root / "memory" / "long" / "semantic"
    (mem / "abc123.md").write_text("---\nid: abc123\nlayer: semantic\ncreated: 1700000000\nlast_used: 1700000000\n"
                                   "strength: 1.0\ntags: []\n---\nmy editor is vim\n", encoding="utf-8")
    dna = {"name": "Rad", "generation": 0, "parent": None, "persona": "p", "style": [], "lessons": ["l1"], "feedback": []}
    (root / "dna" / "gen0.json").write_text(json.dumps(dna)); (root / "dna" / "current.json").write_text(json.dumps(dna))
    (root / "world").mkdir(exist_ok=True)
    (root / "world" / "graph.json").write_text(json.dumps({"entities": {"arjun": {"name": "Arjun", "kind": "person"}},
                                                           "relations": [{"from": "arjun", "rel": "located_in", "to": "pune"}]}))
    return h


def test_migrations_run_once_in_order_with_snapshot(tmp_path):
    h = _legacy_home(tmp_path)
    st = Storage(h)
    assert not st.is_fresh_home() and st.version() == 0
    assert [m.version for m in st.pending()] == [1, 2, 3]
    dry = st.migrate(dry_run=True)
    assert all(d["dry_run"] for d in dry) and st.version() == 0
    done = st.migrate()
    assert [d["version"] for d in done] == [1, 2, 3] and st.version() == SCHEMA_VERSION
    assert done[0]["summary"]["memories_rewritten"] == 1
    assert done[1]["summary"]["dna_files_updated"] == 2
    assert done[2]["summary"]["world_items_updated"] == 2
    # data is now explicit on disk
    raw = (h.root / "memory" / "long" / "semantic" / "abc123.md").read_text()
    assert "origin:" in raw and "my editor is vim" in raw
    assert "history" in json.loads((h.root / "dna" / "gen0.json").read_text())
    w = json.loads((h.root / "world" / "graph.json").read_text())
    assert w["relations"][0]["origin"] == "INFERRED"
    # a snapshot was taken before each step, applied list recorded, second run is a no-op
    assert len(st.snapshots()) == 3 and all("pre-migration" in p.name for p in st.snapshots())
    assert [a["version"] for a in st.schema()["applied"]] == [1, 2, 3]
    assert st.migrate() == [] and st.pending() == []
    # migrated data still loads through the real APIs
    from rad.memory import Memory
    e = Memory(h).scan()[0]
    assert e.text == "my editor is vim" and e.origin == "INFERRED"
    from rad.world import WorldModel
    assert WorldModel(h).query("arjun")


def test_fresh_home_is_stamped_not_migrated(home):
    st = Storage(home)
    assert st.pending() == [] and st.version() == SCHEMA_VERSION
    assert st.schema()["applied"][0]["name"] == "fresh home"
    assert st.snapshots() == []


# ---------------------------------------------------------------- integrity

def test_integrity_reports_and_quarantines_without_deleting(home):
    (home.root / "world").mkdir(exist_ok=True)
    (home.root / "world" / "graph.json").write_text("{not json")
    (home.root / "rad.json.tmp").write_text("half")
    (home.root / "audit.jsonl").write_text('{"ok": 1}\nBROKEN\n')
    (home.root / "objectives" / "obj_x").mkdir(parents=True)
    (home.root / "memory" / "long" / "semantic" / "bad.md").write_text("no front matter")
    rep = Storage(home).integrity(repair=False)
    probs = {f["path"]: f for f in rep}
    assert "world/graph.json" in probs and "rad.json.tmp" in probs and "audit.jsonl" in probs
    assert "objectives/obj_x" in probs and "memory/long/semantic/bad.md" in probs
    assert (home.root / "world" / "graph.json").read_text() == "{not json"     # report mode: untouched
    rep = Storage(home).integrity(repair=True)
    fixed = {f["path"]: f for f in rep if f["repaired"]}
    assert "world/graph.json" in fixed and "rad.json.tmp" in fixed
    q = list((home.root / "world").glob("graph.json.corrupt-*"))
    assert q and q[0].read_text() == "{not json"                                  # quarantined, not deleted
    assert not (home.root / "world" / "graph.json").exists()
    assert not [f for f in rep if f["path"] == "audit.jsonl" and f["repaired"]]   # jsonl never rewritten


def test_corrupt_files_do_not_crash_subsystems(home):
    """Failure injection: every store gets garbage; APIs must degrade to empty/default, not raise."""
    (home.root / "world").mkdir(exist_ok=True)
    (home.root / "world" / "graph.json").write_text("{")
    (home.root / "user.json").write_text("[]")
    (home.root / "world" / "graph.json").write_text('{"entities": [], "relations": {}}')   # valid JSON, wrong shape
    (home.root / "policy.json").write_text("garbage")
    (home.root / "agents").mkdir(exist_ok=True); (home.root / "agents" / "registry.json").write_text("{{")
    (home.root / "dna" / "current.json").write_text("nope")
    (home.root / "memory" / "long" / "semantic" / "x.md").write_text("---\nbroken: [\n---\n")
    (home.root / "objectives" / "obj_bad").mkdir(parents=True)
    (home.root / "objectives" / "obj_bad" / "objective.json").write_text("{]")
    from rad.world import WorldModel
    from rad.usermodel import UserModel
    from rad.policy import Policy
    from rad.agents import AgentRegistry
    from rad.dna import Evolver
    from rad.memory import Memory
    from rad.control.objectives import ObjectiveStore
    assert WorldModel(home).query("x") == []
    assert WorldModel(home).learn("Bengaluru is my city.") >= 0
    assert isinstance(UserModel(home).context_block(), str)
    assert Policy(home).decide("shell", "ls").effect in ("ASK", "ALLOW")
    assert "reviewer" in AgentRegistry(home).all()
    assert Evolver(home).load()["name"] == "Rad"
    assert isinstance(Memory(home).scan(), list)
    assert all(o.id != "obj_bad" for o in ObjectiveStore(home).list())
    findings = Doctor(home, fix=False, probe_network=False).run()
    assert any(f.check == "integrity" and f.status in ("warn", "fail") for f in findings)
    assert not any("check crashed" in f.message for f in findings)


# ---------------------------------------------------------------- snapshots

def test_snapshot_excludes_keys_and_restore_roundtrip(home):
    (home.root / "keys" / "keys.env").write_text("SECRET=1")
    from rad.usermodel import UserModel
    UserModel(home).set("preferences", "editor", "vim", origin="USER_PROVIDED")
    st = Storage(home)
    p = st.snapshot(label="t")
    with tarfile.open(p) as tar:
        names = tar.getnames()
    assert "user.json" in names and not any(n.startswith("keys") for n in names)
    if os.name != "nt":
        assert oct(p.stat().st_mode & 0o777) == "0o600"
    else:
        assert p.exists()
    UserModel(home).set("preferences", "editor", "emacs", origin="USER_PROVIDED")
    restored = st.restore(p)
    assert "user.json" in restored
    assert UserModel(home).show().count("vim") == 1 and "emacs" not in UserModel(home).show()
    assert (home.root / "keys" / "keys.env").read_text() == "SECRET=1"      # keys never touched
    assert any("pre-restore" in q.name for q in st.snapshots())


def test_restore_rejects_path_traversal(home, tmp_path):
    evil = tmp_path / "evil.tar.gz"
    payload = tmp_path / "x.txt"; payload.write_text("owned")
    with tarfile.open(evil, "w:gz") as tar:
        tar.add(payload, arcname="../../escaped.txt")
        tar.add(payload, arcname="ok.txt")
    Storage(home).restore(evil)
    assert not (home.root.parent.parent / "escaped.txt").exists() and (home.root / "ok.txt").exists()


def test_doctor_full_run_healthy_and_exit_semantics(home):
    fs = Doctor(home, fix=False, probe_network=False).run()
    assert {f.check for f in fs} >= {"python", "home", "config", "schema", "integrity", "policy", "memory", "objectives", "dna", "sandbox"}
    assert all(f.status in ("ok", "optional") for f in fs), [(f.check, f.status, f.message) for f in fs if f.status not in ("ok", "optional")]
    assert not any(f.status == "fail" for f in fs)
    home.update(allow_outside_workspace=True)
    assert {f.check: f.status for f in Doctor(home, fix=False, probe_network=False).run()}["workspace"] == "warn"
    from rad.policy import Policy
    Policy(home).set_default("shell", "ALLOW")
    assert {f.check: f.status for f in Doctor(home, fix=False, probe_network=False).run()}["policy"] == "warn"


def test_doctor_schema_reports_current_version_after_stamp(home):
    """Regression: doctor read the version *before* pending() stamped a fresh home, so a
    first run printed 'schema v0 (current)' even after writing schema v3."""
    from rad.storage import SCHEMA_VERSION
    sp = home.root / "schema.json"
    if sp.exists():
        sp.unlink()
    d = {f.check: f for f in Doctor(home, fix=False, probe_network=False).run()}
    assert d["schema"].status == "ok"
    assert f"v{SCHEMA_VERSION}" in d["schema"].message
    assert json.loads(sp.read_text())["version"] == SCHEMA_VERSION


def test_doctor_render_uses_release_labels(home):
    from rad.doctor import render
    fs = Doctor(home, fix=False, probe_network=False).run()
    text = render(fs)
    assert "READY" in text and "verdict: READY" in text
    assert "OPTIONAL" in text          # unused MCP/voice are optional, not failures
    assert "ok ·" not in text          # old ✓/ok vocabulary is gone from the summary line
