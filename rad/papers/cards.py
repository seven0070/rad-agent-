"""Technique Cards — the bridge between a paper and a testable candidate.

Law: no claim without an exact quote on disk.
"""
import json
from datetime import datetime, timezone
from .ingest import PAPERS_DIR, get_paper, get_paper_text

CARD_VERSION = 1
VALID_TYPES = {"technique", "benchmark", "dataset", "theory", "survey"}
VALID_STATUS = {"extracted", "candidate", "battling", "promoted", "rejected", "retracted"}

def _now(): return datetime.now(timezone.utc).isoformat()

def create_card(slug, card_type, claims, mechanism, implementation_surface,
                battle_plan=None, coi_flags=None) -> dict:
    """Every claim MUST carry evidence_quote; verified against paper text (flag, not block)."""
    if card_type not in VALID_TYPES:
        raise ValueError(f"card_type must be one of {VALID_TYPES}")
    meta = get_paper(slug)
    if not meta:
        raise ValueError(f"Paper {slug!r} not ingested. Run ingest first.")
    paper_text = get_paper_text(slug) or ""
    norm_paper = " ".join(paper_text.split()).lower()

    verified = []
    for c in claims:
        quote = str(c.get("evidence_quote", "")).strip()
        if not quote:
            raise ValueError(f"Claim without evidence_quote: {str(c.get('claim'))[:60]!r}")
        verified.append({"claim": str(c.get("claim", "")).strip(),
                         "evidence_quote": quote,
                         "claimed_gain": c.get("claimed_gain", ""),
                         "quote_verified": " ".join(quote.split()).lower() in norm_paper})

    card = {"card_version": CARD_VERSION, "card_id": f"TC-{slug[:20]}",
            "source": {"slug": slug, "title": meta["title"],
                       "url": meta["source_url"], "sha256": meta["sha256"]},
            "type": card_type, "claims": verified, "mechanism": mechanism,
            "implementation_surface": implementation_surface,
            "battle_plan": battle_plan or {"baseline": "current", "suite": "realworld",
                "metrics": ["verified_rate", "false_done", "cost"],
                "note": "default — customize before battle"},
            "coi_flags": coi_flags or [], "status": "extracted",
            "created_at": _now(), "updated_at": _now()}
    (PAPERS_DIR / slug / "card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card

def get_card(slug: str):
    f = PAPERS_DIR / slug / "card.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

def list_cards(status=None) -> list:
    if not PAPERS_DIR.exists(): return []
    out = []
    for d in sorted(PAPERS_DIR.iterdir()):
        c = get_card(d.name) if (d / "card.json").exists() else None
        if c and (status is None or c.get("status") == status):
            out.append(c)
    return out

_LEGAL = {"extracted": {"candidate", "rejected"}, "candidate": {"battling", "rejected"},
          "battling": {"promoted", "rejected"}, "promoted": {"retracted"},
          "rejected": set(), "retracted": set()}

def set_card_status(slug, new_status) -> dict:
    if new_status not in VALID_STATUS:
        raise ValueError(f"Invalid status: {new_status!r}")
    card = get_card(slug)
    if not card:
        raise ValueError(f"No card for {slug!r}")
    cur = card["status"]
    if new_status not in _LEGAL.get(cur, set()):
        raise ValueError(f"Illegal transition: {cur!r} -> {new_status!r}")
    card["status"] = new_status
    card["updated_at"] = _now()
    (PAPERS_DIR / slug / "card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card

def check_coi(card, benchmark_names) -> list:
    """COI firewall: a paper proposing benchmark X is never validated on X."""
    flags = []
    title_l = card["source"]["title"].lower()
    from .ingest import get_paper_text
    snippet = (get_paper_text(card["source"]["slug"]) or "")[:3000].lower()
    for b in benchmark_names:
        bl = b.lower()
        if bl in title_l or bl in snippet:
            flags.append(f"COI: paper mentions benchmark {b!r} — cannot validate on it")
    if flags:
        card["coi_flags"] = sorted(set(card.get("coi_flags", [])) | set(flags))
        (PAPERS_DIR / card["source"]["slug"] / "card.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8")
    return flags
