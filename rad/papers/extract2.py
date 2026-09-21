"""extract2 — chunked, think-tolerant, locator-based card extraction.

Fixes extract.py's three failure modes against small local brains:
  1. 60k prompt      -> front-loaded ~12k chars (abstract+intro carry claims)
  2. <think> leakage -> strip think blocks before JSON parse
  3. copyist demand  -> brain paraphrase = LOCATOR HINT; quote_locator pins
                        the real verbatim span (law preserved, enforced in code)

LAW (unchanged): quote_verified=True iff a verbatim paper span is pinned.
"""
import json, re
from datetime import datetime, timezone
from .ingest import PAPERS_DIR, get_paper, get_paper_text
from .cards import create_card, get_card
from .quote_locator import locate_verbatim

PROMPT_CHARS = 12_000

PROMPT = """Extract a Technique Card from this paper excerpt. Output ONLY a JSON object:
{{"card_type": "technique|benchmark|dataset|theory|survey",
  "claims": [{{"claim": "<falsifiable sentence>",
               "evidence_hint": "<paraphrase or near-quote of the passage that supports it>",
               "claimed_gain": "<number/percent or 'none'>"}}],
  "mechanism": "<2-3 sentences, how it works>",
  "implementation_surface": ["<subsystem>"],
  "coi_flags": []}}
1-3 strongest claims. evidence_hint may paraphrase — do not worry about exact wording.

PAPER EXCERPT:
{paper}
"""


def _strip_think(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)


def _parse_json(raw: str):
    raw = _strip_think(raw).strip()
    raw = re.sub(r"^```(json)?\s*|\s*```$", "", raw, flags=re.MULTILINE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if 0 <= s < e:
            try:
                return json.loads(raw[s:e + 1])
            except json.JSONDecodeError:
                return None
        return None


def extract_card_v2(slug: str, brain_fn, max_retries: int = 1) -> dict:
    """Locator-based extraction. Every pinned claim carries a verbatim span."""
    if get_card(slug):
        raise ValueError(f"card already exists for {slug!r}")
    full = get_paper_text(slug) or ""
    meta = get_paper(slug)
    if not meta:
        raise ValueError(f"paper {slug!r} not ingested")
    excerpt = full[:PROMPT_CHARS]

    last_err = None
    for attempt in range(1 + max_retries):
        parsed = _parse_json(brain_fn(PROMPT.format(paper=excerpt)))
        if parsed is None:
            last_err = "unparseable JSON (after think-strip)"
            continue
        # locate + pin verbatim spans (the law, enforced here)
        pinned = []
        for c in parsed.get("claims", [])[:3]:
            loc = locate_verbatim(full, str(c.get("evidence_hint", "")))
            if loc:
                pinned.append({"claim": str(c.get("claim", "")).strip(),
                               "evidence_quote": loc["verbatim"],
                               "claimed_gain": str(c.get("claimed_gain", "")),
                               "locator_ratio": loc["ratio"]})
        if not pinned:
            last_err = "no claim's hint located verbatim in paper (ratios too low)"
            continue
        card = create_card(slug=slug, card_type=parsed.get("card_type", "technique"),
                           claims=pinned, mechanism=str(parsed.get("mechanism", "")),
                           implementation_surface=parsed.get("implementation_surface", []),
                           coi_flags=parsed.get("coi_flags", []))
        # Patch locator_ratio into each claim on the persisted card (create_card strips extra keys)
        from . import ingest as _ing
        live_dir = _ing.PAPERS_DIR
        for i, c in enumerate(card["claims"]):
            c["locator_ratio"] = pinned[i]["locator_ratio"]
        card["extraction"] = {"method": "locator_v2", "attempts": attempt + 1,
                              "pinned": len(pinned),
                              "ratios": [p["locator_ratio"] for p in pinned],
                              "at": datetime.now(timezone.utc).isoformat()}
        (live_dir / slug / "card.json").write_text(json.dumps(card, indent=2),
                                                   encoding="utf-8")
        return card
    raise RuntimeError(f"extract2 failed after retries: {last_err}")
