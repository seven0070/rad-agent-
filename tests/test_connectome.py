"""RadConnectome — fruit fly brain wiring tests.

Covers: neuron/synapse recording, STDP plasticity bounds, rich-club hubs,
neuPrint queries (neighbors/path/suggest), projectome regions, sleep replay
pruning + archive, event ingestion from objective events, CLI wiring.
"""
from __future__ import annotations

import json

from rad.connectome import (PRUNE_BELOW, RICH_CLUB_FRAC, W_CEIL, W_FLOOR, W_INIT,
                            Connectome, ingest_objective_events, kind_of, region_of)


def test_fire_creates_neurons_and_synapse(home):
    cx = Connectome(home)
    s = cx.fire("coder", "write_file")
    assert cx.neurons["coder"].kind == "agent"
    assert cx.neurons["write_file"].kind == "tool"
    assert s.weight == W_INIT
    assert cx.neurons["coder"].fires == 1


def test_ltp_strengthens_bounded(home):
    cx = Connectome(home)
    for _ in range(50):
        cx.fire("coder", "write_file", success=True)
    s = cx.synapses[("coder", "write_file")]
    assert s.weight == W_CEIL
    assert s.successes == 50


def test_ltd_weakens_bounded(home):
    cx = Connectome(home)
    for _ in range(50):
        cx.fire("coder", "write_file", success=False)
    s = cx.synapses[("coder", "write_file")]
    assert s.weight == W_FLOOR
    assert s.failures == 50


def test_neutral_fire_no_weight_change(home):
    cx = Connectome(home)
    cx.fire("coder", "write_file")
    cx.fire("coder", "write_file")
    assert cx.synapses[("coder", "write_file")].weight == W_INIT


def test_verified_flag_sticks(home):
    cx = Connectome(home)
    cx.fire("tester", "run_shell", verified=True)
    assert cx.synapses[("tester", "run_shell")].verified is True


def test_record_sequence(home):
    cx = Connectome(home)
    n = cx.record_sequence(["planner", "coder", "write_file"], verified=True, success=True)
    assert n == 2
    assert ("planner", "coder") in cx.synapses
    assert ("coder", "write_file") in cx.synapses


def test_neighbors_strongest_first(home):
    cx = Connectome(home)
    cx.fire("coder", "a_tool", success=True)
    cx.fire("coder", "a_tool", success=True)
    cx.fire("coder", "b_tool")
    outs = cx.neighbors("coder", "out")
    assert outs[0].post == "a_tool"
    ins = cx.neighbors("a_tool", "in")
    assert ins[0].pre == "coder"


def test_path_finds_route(home):
    cx = Connectome(home)
    cx.record_sequence(["planner", "coder", "tester"])
    p = cx.path("planner", "tester")
    assert p == ["planner", "coder", "tester"]


def test_path_none_when_disconnected(home):
    cx = Connectome(home)
    cx.fire("a", "b")
    assert cx.path("a", "zzz") is None
    assert cx.path("zzz", "a") is None


def test_path_self(home):
    cx = Connectome(home)
    assert cx.path("x", "x") == ["x"]


def test_rich_club_top_fraction(home):
    cx = Connectome(home)
    # hub connects to 10 leaves; leaves connect nowhere else
    for i in range(10):
        cx.fire("hub", f"leaf{i}")
    hubs = cx.rich_club(frac=RICH_CLUB_FRAC)
    assert "hub" in hubs
    assert len(hubs) >= 1


def test_rich_club_empty(home):
    cx = Connectome(home)
    assert cx.rich_club() == []


def test_suggest_verified_first(home):
    cx = Connectome(home)
    cx.fire("coder", "risky_tool")
    cx.fire("coder", "safe_tool", verified=True)
    sug = cx.suggest_next("coder")
    assert sug[0] == "safe_tool"


def test_projectome_regions(home):
    cx = Connectome(home)
    cx.fire("memory", "recall")          # mushroom_body -> mushroom_body
    cx.fire("coder", "write_file")       # central_complex-ish
    proj = cx.projectome()
    assert isinstance(proj, dict) and proj
    assert "mushroom_body" in proj


def test_region_kind_mapping():
    assert kind_of("coder") == "agent"
    assert kind_of("write_file") == "tool"
    assert kind_of("semantic") == "memory"
    assert region_of("recall") == "mushroom_body"
    assert region_of("chat") == "antennal_lobe"
    assert region_of("sidecar") == "ventral_nerve_cord"
    assert region_of("x402") == "neurosecretory"


def test_sleep_replay_decays_and_prunes(home):
    cx = Connectome(home)
    cx.fire("a", "b")  # neutral, weight INIT, no successes -> prunable after decay
    s = cx.synapses[("a", "b")]
    s.weight = PRUNE_BELOW  # force below threshold
    cx.fire("c", "d", success=True)  # has successes -> survives
    res = cx.sleep_replay()
    assert ("a", "b") not in cx.synapses
    assert ("c", "d") in cx.synapses
    assert res["pruned"] == 1
    archived = list((home.root / "connectome" / "archive").glob("pruned-*.json"))
    assert archived, "pruned synapses must be archived, never deleted"


def test_sleep_replay_empty(home):
    cx = Connectome(home)
    res = cx.sleep_replay()
    assert res == {"decayed": 0, "pruned": 0, "neurons": 0, "synapses": 0}


def test_persistence_roundtrip(home):
    cx = Connectome(home)
    cx.fire("coder", "write_file", verified=True, success=True)
    cx.save()
    cx2 = Connectome(home)
    assert ("coder", "write_file") in cx2.synapses
    assert cx2.synapses[("coder", "write_file")].verified is True


def test_ingest_no_objectives(home):
    res = ingest_objective_events(home)
    assert res["edges"] == 0


def test_ingest_builds_edges_from_events(home, tmp_path):
    objs = home.root / "objectives" / "obj_test"
    objs.mkdir(parents=True, exist_ok=True)
    events = [
        {"kind": "TOOL_CALLED", "data": {"tool": "read_file"}},
        {"kind": "TOOL_CALLED", "data": {"tool": "write_file"}},
        {"kind": "TASK_COMPLETED", "data": {}},
        {"kind": "TASK_END", "data": {}},
    ]
    (objs / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
    res = ingest_objective_events(home)
    assert res["edges"] == 1
    assert res["tasks"] == 1
    cx = Connectome(home)
    assert ("read_file", "write_file") in cx.synapses
    assert cx.synapses[("read_file", "write_file")].verified is True


def test_stats_shape(home):
    cx = Connectome(home)
    cx.fire("a", "b", verified=True)
    st = cx.stats()
    assert st["neurons"] == 2
    assert st["synapses"] == 1
    assert st["verified_edges"] == 1
    assert isinstance(st["rich_club"], list)
    assert isinstance(st["regions"], list)
