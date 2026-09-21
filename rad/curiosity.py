"""The curiosity drive — ONE self-chosen exploration per sleep, reported at wake.



Bounded by construction: one pick, one artifact, zero side effects beyond

its own folder. Picks from real inputs (papers not yet carded, unresolved

contradictions) — curiosity with receipts, never idle wandering.



CONTRACT: deterministic given same inputs + rng seed. Write target is

quarantined: ~/.rad/curiosity/ — Jerry never needs to care.

"""

import json, random

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def set_paths(home: Path):   # L5

    global _DIR; _DIR = Path(home) / "curiosity"

_DIR = Path.home() / ".rad" / "curiosity"



def candidates(papers_dir: Path, ledger_file: Path | None = None) -> list:
    """Real inputs only: papers without cards are unexplored territory."""
    cands = []
    if papers_dir.exists() and papers_dir.is_dir():
        if papers_dir.name != "papers" and not papers_dir.name.startswith("_") and not (papers_dir / "card.json").exists():
            cands.append({"kind": "uncarded_paper", "slug": papers_dir.name})
            return cands
        for d in sorted(papers_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                if not (d / "card.json").exists():
                    cands.append({"kind": "uncarded_paper", "slug": d.name})
    return cands



def explore_once(papers_dir: Path, brain_fn=None, rng: random.Random | None = None,

                 home: Path | None = None) -> dict:

    """Pick ONE unexplored item; if a brain is attached, draft one open

    question about it. No side effects beyond the curiosity note file."""

    rng = rng or random.Random()

    out = Path(home) / "curiosity" if home else _DIR

    out.mkdir(parents=True, exist_ok=True)

    cands = candidates(papers_dir)

    if not cands:

        record = {"type": "curiosity.v1", "at": _now(), "pick": None,

                  "note": "nothing unexplored — honest rest"}

    else:

        pick = rng.choice(cands)

        question = None

        if brain_fn:

            try:

                question = brain_fn(f"Research paper slug: {pick['slug']}\n"

                                    "Write ONE sharp open question worth exploring.")

            except Exception:

                question = None          # brain unavailable — curiosity degrades, never fakes

        record = {"type": "curiosity.v1", "at": _now(), "pick": pick,

                  "open_question": question, "source": "brain" if question else "deterministic"}

    (out / "last_exploration.json").write_text(json.dumps(record, indent=2),

                                               encoding="utf-8")

    return record



def wake_report() -> str:

    f = _DIR / "last_exploration.json" if _DIR.exists() else None

    if not f or not f.exists():

        return "wake: no exploration on record"

    r = json.loads(f.read_text(encoding="utf-8"))

    if not r.get("pick"):

        return "wake: nothing unexplored — rested"

    q = r.get("open_question") or "(question pending — brain was offline)"

    return f"wake: while you were away, curiosity marked {r['pick']['slug']} — {q[:120]}"

