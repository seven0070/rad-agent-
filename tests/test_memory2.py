"""Memory 2.0 — origins, confidence, contradiction handling, correction, user model,
temporal world model, and the control plane feeding experience with honest provenance."""
import time

from rad.memory import (CONTRADICTED, INFERRED, MODEL_GENERATED, OBSERVED, UNVERIFIED, USER_PROVIDED,
                        VERIFIED, Memory)
from rad.usermodel import UserModel
from rad.world import WorldModel


# ---------------------------------------------------------------- origins & trust

def test_origin_sets_confidence_and_is_persisted(home):
    m = Memory(home)
    e = m.add("semantic", "user's editor is vim", origin=USER_PROVIDED, source="chat")
    g = m.add("semantic", "the build takes about 4 minutes", origin=MODEL_GENERATED, source="sleep")
    m2 = Memory(home)                       # fresh instance → parsed from disk
    a, b = m2.get(e.id), m2.get(g.id)
    assert a.origin == USER_PROVIDED and a.confidence == 0.9 and a.source == "chat"
    assert b.origin == MODEL_GENERATED and b.confidence == 0.4
    assert a.trust > b.trust


def test_old_memory_files_still_parse(home):
    m = Memory(home)
    p = m.long_dir("semantic") / "legacy.md"
    p.write_text("---\nid: legacy\nlayer: semantic\ncreated: 1\nlast_used: 1\nstrength: 0.8\ntags: []\n---\nold fact")
    e = m.get("legacy")
    assert e and e.origin == INFERRED and e.verification == UNVERIFIED and e.confidence == 0.5


def test_recall_ranks_trusted_over_generated(home):
    m = Memory(home)
    m.add("semantic", "deploy target is the staging cluster", origin=MODEL_GENERATED)
    m.add("semantic", "deploy target is the blue cluster", origin=USER_PROVIDED)
    found = m.recall("what is the deploy target cluster")
    assert "blue" in found[0].text


def test_reobservation_upgrades_and_verifies(home):
    m = Memory(home)
    e = m.add("semantic", "the api listens on port 8080", origin=MODEL_GENERATED)
    assert e.verification == UNVERIFIED
    e2 = m.add("semantic", "the api listens on port 8080", origin=OBSERVED, source="file:config")
    assert e2.id == e.id and e2.origin == OBSERVED and e2.verification == VERIFIED


def test_prompt_block_labels_origin(home):
    m = Memory(home)
    m.add("semantic", "user prefers tabs over spaces", origin=USER_PROVIDED)
    m.add("semantic", "user probably works late at night", origin=MODEL_GENERATED)
    block = m.format_for_prompt(m.recall("user prefers tabs spaces late night"))
    assert "user_provided" in block and "model_generated" in block and "hints, not facts" in block


# ---------------------------------------------------------------- contradictions

def test_contradiction_by_negation_links_and_marks_weaker(home):
    m = Memory(home)
    a = m.add("semantic", "the user uses docker for local development", origin=MODEL_GENERATED)
    b = m.add("semantic", "the user does not use docker for local development", origin=USER_PROVIDED)
    assert b.id != a.id
    a2 = m.get(a.id)
    assert b.id in a2.contradicts and a.id in b.contradicts
    assert a2.verification == CONTRADICTED and b.verification == UNVERIFIED
    assert len(m.contradictions()) == 1


def test_contradiction_by_value_same_subject(home):
    m = Memory(home)
    a = m.add("semantic", "my editor is vim", origin=USER_PROVIDED)
    b = m.add("semantic", "my editor is emacs", origin=MODEL_GENERATED)
    assert a.id in b.contradicts
    assert b.verification == CONTRADICTED          # weaker origin loses
    assert m.get(a.id).verification == UNVERIFIED


def test_contradicted_memory_ranks_low_and_decays_fast(home):
    m = Memory(home)
    a = m.add("semantic", "my editor is vim", origin=USER_PROVIDED)
    b = m.add("semantic", "my editor is emacs", origin=MODEL_GENERATED)
    found = m.recall("which editor")
    assert found[0].id == a.id
    b.last_used = time.time() - 20 * 86400
    m._save(b)
    a.last_used = time.time() - 20 * 86400
    m._save(a)
    m.decay_and_archive(threshold=0.0)
    assert m.get(b.id).strength < m.get(a.id).strength


def test_forget_correct_verify(home):
    m = Memory(home)
    a = m.add("semantic", "my editor is vim", origin=MODEL_GENERATED)
    b = m.add("semantic", "my editor is emacs", origin=MODEL_GENERATED)
    assert m.get(a.id).contradicts == [b.id]
    c = m.correct(b.id, "my editor is helix")
    assert m.get(b.id) is None                                  # archived
    assert c.origin == USER_PROVIDED and "corrected" in c.tags
    assert (home.root / "memory" / "archive" / f"{b.id}.md").exists()
    # unlinking: a no longer contradicts b … but now contradicts c
    assert b.id not in m.get(a.id).contradicts and c.id in m.get(a.id).contradicts
    m.verify(a.id, ok=True)
    assert m.get(a.id).verification == VERIFIED and m.get(a.id).confidence >= 0.9


def test_scan_cache_invalidates_on_write(home):
    m = Memory(home)
    m.add("semantic", "alpha fact one")
    assert len(m.scan()) == 1
    m.add("episodic", "beta event two")
    assert len(m.scan()) == 2
    other = Memory(home)
    other.add("procedural", "gamma skill three")
    time.sleep(0.01)
    assert len(m.scan()) == 3                                   # dir mtime signature changed


def test_sleep_labels_origins(home):
    m = Memory(home)
    m.short_path().write_text("[10:00:00] user: remember: my server is called atlas\n[10:00:01] rad: ok\n")
    m.sleep(consolidator=None)
    e = [x for x in m.scan("semantic") if "atlas" in x.text][0]
    assert e.origin == USER_PROVIDED
    m.mark_slept(at=time.time() - 2)
    m.session_log("user", "we shipped v2 today")            # real timestamp → unslept
    m.sleep(consolidator=lambda t: {"episodic": ["shipped v2"], "semantic": [], "procedural": []})
    e2 = [x for x in m.scan("episodic") if "v2" in x.text][0]
    assert e2.origin == MODEL_GENERATED and e2.source == "sleep"


# ---------------------------------------------------------------- user model

def test_user_model_set_add_show_and_precedence(home):
    um = UserModel(home)
    assert um.set("preferences", "editor", "vim")                              # user
    assert not um.set("preferences", "editor", "emacs", origin=MODEL_GENERATED)  # weaker: rejected
    d = um.data()
    assert d["preferences"]["editor"]["value"] == "vim"
    assert d["preferences"]["editor"]["disputed_by"][0]["value"] == "emacs"
    assert um.set("preferences", "editor", "helix")                            # user overrides user
    assert um.add("goals", "ship rad v1")
    assert not um.add("goals", "Ship RAD v1")                                  # dedupe
    assert "helix" in um.show() and "ship rad v1" in um.show()
    assert "disputed" not in um.show()


def test_user_model_learns_patterns_as_inferred(home):
    um = UserModel(home)
    n = um.learn_from_text("Call me Arjun. I prefer short answers. I'm working on the rad agent runtime.")
    assert n >= 2
    d = um.data()
    assert d["communication"]["name"]["value"] == "Arjun"
    assert d["communication"]["name"]["origin"] == INFERRED
    assert any("rad agent runtime" in p["value"] for p in d["projects"])
    block = um.context_block()
    assert "Arjun" in block and "inferred" in block


def test_user_model_forget_and_reset(home):
    um = UserModel(home)
    um.set("preferences", "editor", "vim")
    um.add("constraints", "never push to main")
    assert um.forget("preferences", "editor") and um.forget("constraints", "never push")
    assert um.context_block() == ""


def test_session_injects_user_model(home, tmp_path):
    from unittest import mock
    import rad.router as R
    import rad.providers as P
    from rad.session import Session
    home.update(workspace=str(tmp_path))
    UserModel(home).set("communication", "name", "Arjun")
    seen = {}

    def fake_chat(self, messages, **kw):
        seen["sys"] = messages[0]["content"]
        return P.ChatResult(text="hi")

    with mock.patch.object(R.RouterState, "chat", fake_chat):
        Session(home).think("I prefer dark mode")
    assert "communication.name: Arjun" in seen["sys"]
    assert UserModel(home).data()["preferences"]["likes"]["origin"] == INFERRED


# ---------------------------------------------------------------- temporal world model

def test_world_functional_relation_supersedes(home):
    w = WorldModel(home)
    w.add("Arjun lives in Pune")
    w.add("Arjun lives in Bengaluru")
    cur = [r for r in w.current_relations() if r["rel"] == "located_in"]
    assert len(cur) == 1 and cur[0]["to"] == "bengaluru"
    hist = [r for r in w.data()["relations"] if r.get("status") == "superseded"]
    assert len(hist) == 1 and hist[0]["to"] == "pune" and hist[0]["until"]
    assert not any(h["to"] == "pune" for h in w.query("arjun") if h["type"] == "relation")
    assert any(h["to"] == "pune" for h in w.query("arjun", include_history=True) if h["type"] == "relation")


def test_world_weaker_source_becomes_disputed_not_overwrite(home):
    w = WorldModel(home)
    w.add("Arjun works at Acme")                                             # manual → USER_PROVIDED
    w.learn("Arjun works at Globex", source="chat-close")                    # heuristic → INFERRED
    cur = [r for r in w.current_relations() if r["rel"] == "works_at"]
    by_to = {r["to"]: r for r in cur}
    assert by_to["acme"]["status"] == "current" and by_to["globex"]["status"] == "disputed"
    assert len(w.disputes()) == 1
    assert "disputed" in w.context_block("where does Arjun work")
    w.confirm("Arjun", "works_at", "globex")
    assert [r["to"] for r in w.current_relations() if r["rel"] == "works_at"] == ["globex"]
    assert w.retract("Arjun", "works_at", "globex")
    assert not [r for r in w.current_relations() if r["rel"] == "works_at"]


def test_world_learn_observation_is_observed_origin(home):
    w = WorldModel(home)
    n = w.learn_observation("obj_1", "t_1", [{"location": "/ws/report.md"}])
    assert n == 2
    d = w.data()
    assert d["entities"]["report.md"]["origin"] == OBSERVED and d["entities"]["report.md"]["kind"] == "artifact"
    rel = d["relations"][0]
    assert (rel["from"], rel["rel"], rel["to"], rel["origin"]) == ("obj_1", "created", "report.md", OBSERVED)


# ---------------------------------------------------------------- experience → memory (control plane)

def test_objective_completion_feeds_memory_with_observed_origin(home, tmp_path):
    from rad.control import Controller, ObjectiveStatus
    from tests.test_control_plane import ScriptedSession, _plan_llm
    ws = tmp_path / "ws"; ws.mkdir(); home.update(workspace=str(ws))
    plan = {"tasks": [{"id": "t1", "text": "make report", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "report.md"}}]}]}
    ScriptedSession.script = [([], "DONE: (lie)"), ([("write_file", {"path": "report.md", "content": "x"})], "DONE")]
    ScriptedSession.prompts = []
    ctl = Controller(home, session_factory=ScriptedSession, llm=_plan_llm(plan), quiet=True)
    obj = ctl.run(ctl.create("make a report"))
    assert obj.status == ObjectiveStatus.COMPLETED
    m = Memory(home)
    ep = [e for e in m.scan("episodic") if obj.id in e.tags]
    assert ep and ep[0].origin == OBSERVED and "report.md" in ep[0].text
    pr = m.scan("procedural")
    assert pr and pr[0].origin == OBSERVED and "VALIDATION_FAILURE" in pr[0].text
    d = WorldModel(home).data()
    assert d["entities"]["report.md"]["origin"] == OBSERVED


def test_contradiction_by_one_differing_slot(home):
    """'on the blue shelf' vs 'on the red shelf' is a contradiction, not a near-duplicate."""
    m = Memory(home)
    a = m.add("semantic", "the deploy key is on the blue shelf", origin=USER_PROVIDED)
    b = m.add("semantic", "the deploy key is on the red shelf", origin=MODEL_GENERATED)
    assert b.id in m.get(a.id).contradicts and a.id in m.get(b.id).contradicts
    assert m.get(b.id).verification == CONTRADICTED          # the weaker side loses
    assert len(m.contradictions()) == 1


def test_near_duplicate_different_wording_is_not_a_contradiction(home):
    m = Memory(home)
    m.add("semantic", "the deploy key lives on the blue shelf in the lab", origin=USER_PROVIDED)
    m.add("semantic", "the deploy key sits on the blue shelf inside the lab", origin=OBSERVED)
    assert m.contradictions() == []
