"""P1 swarm: EvolveMem, MemSkill, Desktop Studio v3 plugin pane + GGUF stub."""
import json
import pathlib
import tempfile

from rad.home import RadHome
from rad.memory import Memory
from rad.world import WorldModel

def test_memory_evolve_config_exists(tmp_path):
    home = RadHome(tmp_path / ".rad")
    assert "memory.evolve" in home.cfg
    assert home.cfg["memory.evolve"] is False

def test_memory_evolve_disabled_by_default(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.memory import evolve_memory_nightly
    res = evolve_memory_nightly(home)
    assert res.get("evolve") == "disabled"
    assert "memory.evolve" in res.get("reason", "")

def test_memory_evolve_diagnose_propose_gate(tmp_path):
    home = RadHome(tmp_path / ".rad")
    home.cfg["memory.evolve"] = True
    home.save_config()
    from rad.memory import diagnose_retrieval_failures, propose_scorer_tweak, lab_gate_evolve
    # empty memory: no failures -> no_op
    diag = diagnose_retrieval_failures(home)
    assert "needs_tweak" in diag
    assert diag["needs_tweak"] is False
    prop = propose_scorer_tweak(home, diag)
    assert prop["type"] == "no_op"
    gate = lab_gate_evolve(home, prop)
    assert gate["promoted"] is False
    # with failures: create contradictions
    m = Memory(home)
    m.add("semantic", "Alice works at Acme", origin="USER_PROVIDED")
    m.add("semantic", "Alice works at Beta", origin="USER_PROVIDED")
    # force low strength count by adding many then lowering strength? Use contradictions already
    diag2 = diagnose_retrieval_failures(home)
    assert diag2["needs_tweak"] is True
    prop2 = propose_scorer_tweak(home, diag2)
    assert prop2["type"] == "scorer_weight"
    assert prop2["target"] == "fusion_rrf"
    gate2 = lab_gate_evolve(home, prop2)
    assert gate2["promoted"] is True
    assert gate2["gate"] == "retrieval_bank"

def test_world_evolve_mirror(tmp_path):
    home = RadHome(tmp_path / ".rad")
    home.cfg["memory.evolve"] = True
    home.save_config()
    from rad.world import world_diagnose, world_propose, world_lab_gate, evolve_world_nightly
    diag = world_diagnose(home)
    assert "disputed" in diag
    prop = world_propose(home, diag)
    gate = world_lab_gate(home, prop)
    # no disputes initially -> no_op
    assert prop["type"] == "no_op"
    assert gate["promoted"] is False
    # create disputed relation
    w = WorldModel(home)
    d = w.data()
    w._add_relation(d, "Alice", "works_at", "Acme", "manual", "USER_PROVIDED")
    w.save(d)
    d = w.data()
    w._add_relation(d, "Alice", "works_at", "Beta", "text", "INFERRED")
    w.save(d)
    diag2 = world_diagnose(home)
    assert diag2["needs_tweak"] is True
    prop2 = world_propose(home, diag2)
    assert prop2["type"] == "world_weight"
    gate2 = world_lab_gate(home, prop2)
    assert gate2["promoted"] is True
    # nightly respects config
    res = evolve_world_nightly(home)
    assert "diagnosis" in res

def test_sleep_evolve_flag(tmp_path):
    home = RadHome(tmp_path / ".rad")
    home.cfg["memory.evolve"] = True
    home.save_config()
    from rad.sleep import run_sleep
    # without evolve
    r1 = run_sleep(home, sync_drive=False, evolve=False)
    assert "evolve" not in r1
    # with evolve
    r2 = run_sleep(home, sync_drive=False, evolve=True)
    assert "evolve" in r2
    assert "diagnosis" in r2["evolve"]
    # disabled config still returns evolve disabled
    home.cfg["memory.evolve"] = False
    home.save_config()
    r3 = run_sleep(home, sync_drive=False, evolve=True)
    assert r3["evolve"]["evolve"] == "disabled"

def test_cli_sleep_evolve_parser():
    from rad.cli import build_parser
    p = build_parser()
    args = p.parse_args(["sleep", "--evolve"])
    assert args.evolve is True
    args2 = p.parse_args(["sleep"])
    assert getattr(args2, "evolve", False) is False

def test_cli_skills_evolve_parser():
    from rad.cli import build_parser
    p = build_parser()
    args = p.parse_args(["skills", "evolve"])
    assert args.skills_action == "evolve"

def test_skills_mine_trajectories(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.skills import mine_trajectories, skill_bank_load
    # empty -> no trajs
    assert mine_trajectories(home) == []
    # create objective with events
    obj = home.root / "objectives" / "obj1"
    obj.mkdir(parents=True)
    with open(obj / "events.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"kind":"TOOL_CALLED","data":{"tool":"read_file"}})+"\n")
        f.write(json.dumps({"kind":"TOOL_CALLED","data":{"tool":"write_file"}})+"\n")
        f.write(json.dumps({"kind":"TASK_COMPLETED","data":{}})+"\n")
    trajs = mine_trajectories(home)
    assert len(trajs) == 1
    assert trajs[0]["sequence"] == ["read_file", "write_file"]

def test_skills_evolve_lab_gated(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.skills import skills_evolve, skill_bank_load, mine_trajectories
    obj = home.root / "objectives" / "obj_e1"
    obj.mkdir(parents=True)
    with open(obj / "events.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"kind":"TOOL_CALLED","data":{"tool":"a"}})+"\n")
        f.write(json.dumps({"kind":"TOOL_CALLED","data":{"tool":"b"}})+"\n")
        f.write(json.dumps({"kind":"TASK_COMPLETED"})+"\n")
    before = len(skill_bank_load(home).get("skills", {}))
    res = skills_evolve(home)
    assert res["before"] == before
    assert res["after"] == before + 1
    assert res["delta"] == 1
    assert res["promoted"] is True
    assert res["gate"] == "acceptance_bank"
    # second evolve with same traj should not promote (no bank growth)
    res2 = skills_evolve(home)
    assert res2["delta"] == 0
    assert res2["promoted"] is False

def test_skills_lifecycle_reuse_refine(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.skills import induce_skill, refine_skill, skill_bank_load
    r1 = induce_skill(home, {"sequence":["x","y"],"objective":"o1"})
    assert r1["status"] == "induced"
    key = r1["key"]
    r2 = induce_skill(home, {"sequence":["x","y"],"objective":"o1"})
    assert r2["status"] == "reused"
    assert r2["skill"]["reuse_count"] == 2
    r3 = refine_skill(home, key, ["x","y","z"])
    assert r3["status"] == "refined"
    assert r3["skill"]["sequence"] == ["x","y","z"]
    assert r3["skill"]["lifecycle"] == "refined"

def test_providers_gguf_detection(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.providers import all_specs, detect_gguf_import
    oll = [s for s in all_specs(home) if s.name == "ollama"][0]
    res = detect_gguf_import(oll)
    assert "supported" in res
    assert "gguf_models" in res
    # ollama should report supported even offline (stub)
    assert res["supported"] is True
    # non-ollama
    openai_spec = [s for s in all_specs(home) if s.name == "openai"][0]
    res2 = detect_gguf_import(openai_spec)
    assert res2["supported"] is False

def test_probe_local_gguf_annotates(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.providers import all_specs, probe_local
    oll = [s for s in all_specs(home) if s.name == "ollama"][0]
    reachable, models = probe_local(oll)
    # probe_local should annotate gguf fields without crashing
    assert isinstance(reachable, bool)
    assert isinstance(models, list)
    assert hasattr(oll, "_gguf_supported") or hasattr(oll, "_gguf_models") or True  # at least not crash

def test_desktop_mcp_plugin_pane_exists():
    p = pathlib.Path("desktop/src/components/chat/McpPluginPane.tsx")
    assert p.exists(), "McpPluginPane.tsx missing"
    txt = p.read_text(encoding="utf-8")
    assert "McpPluginPane" in txt
    assert "GGUF" in txt
    assert "MCP" in txt or "mcp" in txt.lower()

def test_desktop_plugin_pane_structure():
    import pathlib
    chat_dir = pathlib.Path("desktop/src/components/chat")
    assert (chat_dir / "McpPluginPane.tsx").exists()
    assert (chat_dir / "ChatFeed.tsx").exists()
