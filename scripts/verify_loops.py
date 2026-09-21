#!/usr/bin/env python3
"""Phase close-loops verification — 9 checks, offline."""
import json, sys, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


PAPER = ("Self-Refine is an approach where the same LLM provides feedback for "
         "its output and uses it to refine itself, iteratively improving results. "
         "It requires no supervised training data and no reinforcement learning, "
         "using a single LLM as generator, refiner and feedback provider. "
         "Evaluations show around twenty percent absolute average improvement "
         "across many tasks with strong gains on dialogue and code optimization.")


@check("locator: exact-normalized hit returns ratio 1.0")
def loc_exact():
    from rad.papers.quote_locator import locate_verbatim
    r = locate_verbatim(PAPER, "uses it to refine itself, iteratively")
    assert r and r["ratio"] == 1.0 and "iteratively" in r["verbatim"]


@check("locator: paraphrase located with ratio >= 0.60, span is real paper text")
def loc_fuzzy():
    from rad.papers.quote_locator import locate_verbatim
    r = locate_verbatim(
        PAPER,
        "The model gives feedback on its own output and refines itself in an iterative loop."
    )
    assert r is not None and r["ratio"] >= 0.60, r
    assert "refine" in r["verbatim"]            # the pinned span is real paper text


@check("locator: garbage hint returns None (law holds — no pin, no pass)")
def loc_garbage():
    from rad.papers.quote_locator import locate_verbatim
    assert locate_verbatim(PAPER, "quantum blockchain synergy synergy quantum") is None


@check("locator: deterministic — same inputs, same span")
def loc_det():
    from rad.papers.quote_locator import locate_verbatim
    # This hint has enough overlap with 'using a single LLM as generator, refiner and feedback provider'
    hint = "single LLM as generator, refiner and feedback provider"
    a = locate_verbatim(PAPER, hint)
    b = locate_verbatim(PAPER, hint)
    assert a is not None, f"locator returned None for hint: {hint!r}"
    assert a == b and a["ratio"] == b["ratio"]


@check("extract2: think-strip + JSON parse recovery")
def extract_parse():
    from rad.papers.extract2 import _parse_json
    dirty = '<think>hmm let me think about { this a lot</think>\n```json\n{"a": 1}\n```'
    p = _parse_json(dirty)
    assert p == {"a": 1}, p


@check("extract2: full v2 flow on tmp paper with stub brain (locator pins real span)")
def extract_v2_flow():
    from rad.papers import ingest as ing, cards as cds, extract2 as ex2
    tmp = Path(tempfile.mkdtemp())
    ing.PAPERS_DIR = tmp
    cds.PAPERS_DIR = tmp
    ex2.PAPERS_DIR = tmp      # patch module-level if present
    d = tmp / "t9"
    d.mkdir(parents=True)
    (d / "paper.md").write_text(PAPER, encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(
        {"slug": "t9", "title": "T9", "source_url": "u", "sha256": "x"}),
        encoding="utf-8")

    def stub_brain(prompt):
        return json.dumps({
            "card_type": "technique",
            "claims": [{
                "claim": "iterative self-refinement works",
                "evidence_hint": "the model refines itself in an iterative loop",
                "claimed_gain": "~20%"
            }],
            "mechanism": "feedback then refine",
            "implementation_surface": ["x"],
            "coi_flags": []
        })

    card = ex2.extract_card_v2("t9", stub_brain)
    c0 = card["claims"][0]
    assert c0["quote_verified"] is True, c0
    assert c0["locator_ratio"] >= 0.60
    assert c0["evidence_quote"] in PAPER


@check("telemetry: wrap counts calls/tokens/time without altering return")
def telemetry_wrap():
    from rad.integrate import telemetry as tm
    calls = {"n": 0}

    def bf(p):
        calls["n"] += 1
        return "x" * 40

    wrapped, stats = tm.wrap(bf)
    out = wrapped("hello world")            # 11 chars -> est 2 tokens (11//4=2)
    assert out == "x" * 40 and calls["n"] == 1
    assert stats["calls"] == 1
    assert stats["est_prompt_tokens"] == 2
    assert stats["est_reply_tokens"] == 10  # 40//4=10
    assert stats["wall_s"] >= 0


@check("telemetry: attach_to_result is claim-neutral and labeled estimate")
def telemetry_attach():
    from rad.integrate import telemetry as tm
    wrapped, stats = tm.wrap(lambda p: "ok")
    wrapped("q")
    res = tm.attach_to_result({"verdict": "tie"}, stats)
    assert res["verdict"] == "tie"
    assert res["brain_telemetry"]["calls"] == 1
    assert "estimates" in res["cost_note"]


@check("imports: close-loops modules importable")
def imports():
    import importlib
    errs = []
    for m in ["rad.papers.quote_locator", "rad.papers.extract2",
              "rad.integrate.telemetry"]:
        try:
            importlib.import_module(m)
        except Exception as e:
            errs.append(f"{m}: {e}")
    assert not errs, errs


def main():
    print(f"\n=== CLOSE-LOOPS VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception:
            fails += 1
            print(f"  FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(CHECKS) - fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
