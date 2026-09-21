"""Brain-assisted card extraction with quote verification + retry-on-fail.

The extractor is held to the same law as the agent: no claim without an
exact quote on disk. Bad quotes -> feedback -> retry. Integration: brain_fn
= callable(prompt) -> str (your chat/LLM loop).
"""
import json, re
from .cards import create_card, get_card
from .ingest import PAPERS_DIR, get_paper, get_paper_text

EXTRACTION_PROMPT = """You are extracting a Technique Card from a research paper.
Output ONLY valid JSON matching this schema — no prose, no markdown fences:

{{
  "card_type": "technique|benchmark|dataset|theory|survey",
  "claims": [
    {{"claim": "<one falsifiable sentence>",
      "evidence_quote": "<EXACT verbatim text copied from the paper below>",
      "claimed_gain": "<number/percent claimed, or 'none'>"}}
  ],
  "mechanism": "<2-3 sentences: HOW it works>",
  "implementation_surface": ["<rad subsystem touched>"],
  "coi_flags": ["<e.g. paper evaluates on its own benchmark>"]
}}

RULES:
1. evidence_quote MUST be copied character-for-character from the paper text.
2. 1-5 claims max — strongest falsifiable claims only.
3. If the paper proposes/evaluates a named benchmark, add a coi_flag.
4. "technique" only if it proposes a METHOD changing runtime behavior.

PAPER TEXT:
{paper_text}
"""

class ExtractionError(RuntimeError):
    pass

def extract_card_brain(slug: str, brain_fn, max_retries: int = 2) -> dict:
    meta = get_paper(slug)
    if not meta: raise ValueError(f"Paper {slug!r} not ingested")
    if get_card(slug): raise ValueError(f"Card already exists for {slug!r}")
    paper_text = (get_paper_text(slug) or "")[:60_000]

    feedback, last_errors = "", []
    for attempt in range(1 + max_retries):
        prompt = EXTRACTION_PROMPT.format(paper_text=paper_text)
        if feedback:
            prompt += f"\n\nPREVIOUS ATTEMPT FAILED. Fix these:\n{feedback}"
        parsed = _parse_json_loose(brain_fn(prompt))
        if parsed is None:
            last_errors = ["output was not valid JSON"]
            feedback = "Output ONLY the JSON object."
            continue
        errors = _validate(parsed, paper_text)
        if errors:
            last_errors = errors
            feedback = "These evidence_quotes were NOT found verbatim:\n" + \
                       "\n".join(f"- {e}" for e in errors) + \
                       "\nCopy quotes EXACTLY, character-for-character."
            continue
        card = create_card(slug, parsed["card_type"], parsed["claims"],
                           parsed["mechanism"], parsed["implementation_surface"],
                           coi_flags=parsed.get("coi_flags", []))
        card["extraction"] = {"method": "brain_assisted", "attempts": attempt + 1,
                              "errors_before_pass": len(last_errors) if attempt else 0}
        (PAPERS_DIR / slug / "card.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8")
        return card
    raise ExtractionError(f"Extraction failed after {1+max_retries} attempts: {last_errors}")

def _parse_json_loose(raw: str):
    raw = re.sub(r"^```(json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if 0 <= s < e:
            try: return json.loads(raw[s:e+1])
            except json.JSONDecodeError: return None
        return None

def _validate(parsed: dict, paper_text: str) -> list:
    errors = []
    norm = " ".join(paper_text.split()).lower()
    if parsed.get("card_type") not in {"technique","benchmark","dataset","theory","survey"}:
        errors.append(f"bad card_type: {parsed.get('card_type')!r}")
    claims = parsed.get("claims", [])
    if not claims:
        errors.append("no claims extracted")
    for i, c in enumerate(claims):
        q = " ".join(str(c.get("evidence_quote", "")).split()).lower()
        if len(q) < 20:
            errors.append(f"claim[{i}] quote too short to verify")
        elif q not in norm:
            errors.append(f"claim[{i}] quote not found verbatim: {q[:80]!r}")
    return errors
