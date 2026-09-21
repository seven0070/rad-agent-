"""rad why — provenance for evolution decisions.

why_technique(slug) walks: promotion -> battle result -> battle spec ->
technique card -> paper meta. Terminates at pinned evidence or 'none'.
Works against ANY papers dir (never hardcodes home) — set_paths() supported.

CONTRACT: digests reported at 16-hex truncation (L2).
"""
import json
from pathlib import Path

PAPERS_DIR = Path.home() / ".rad" / "papers"

def set_paths(papers_dir: Path):     # L5
    global PAPERS_DIR
    PAPERS_DIR = Path(papers_dir)

def why_technique(slug: str, papers_dir: Path | None = None,
                  battles_dir: Path | None = None) -> dict:
    root = Path(papers_dir) if papers_dir else PAPERS_DIR
    battles = Path(battles_dir) if battles_dir else (root / "_battles")
    chain, meta = {}, None

    promo = _find_json(battles, "promotion.json", slug)
    battle_id = promo.get("battle_id") if promo else _latest_battle(battles, slug)

    if battle_id:
        bdir = battles / battle_id
        result = _read(bdir / "result.json")
        if result:
            chain["battle"] = {"verdict": result.get("verdict"),
                               "scores": result.get("scores"),
                               "seed": result.get("seed"),
                               "ran_at": result.get("ran_at")}
        spec = _read(bdir / "spec.json")
        if spec:
            chain["battle_spec"] = {"seed": spec.get("seed"),
                                    "task_count": spec.get("task_count")}
    if promo:
        chain["promotion"] = {"promoted_at": promo.get("promoted_at"),
                              "verdict": promo.get("verdict")}

    card = _read(root / slug / "card.json")
    if card:
        chain["card"] = {"card_id": card.get("card_id"), "type": card.get("type"),
                         "claims_verified": [c.get("quote_verified")
                                             for c in card.get("claims", [])],
                         "coi_flags": card.get("coi_flags", [])}

    meta = _read(root / slug / "meta.json")
    if meta:
        chain["paper"] = {"title": meta.get("title"), "url": meta.get("source_url"),
                          "sha256_head": str(meta.get("sha256", ""))[:16],
                          "ingested_at": meta.get("ingested_at")}

    verdict = "none"
    if "battle" in chain:
        verdict = "evidence"
    elif "card" in chain and any(chain["card"]["claims_verified"]):
        verdict = "quote_only"

    return {"question": f"why technique {slug!r}?", "chain": chain,
            "root_evidence": {"file": f"{slug}/paper.md",
                              "sha256_head": str((meta or {}).get("sha256", ""))[:16]}
                           if meta else None,
            "verdict": verdict}

def _read(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _find_json(battles: Path, name: str, slug: str):
    if not battles.exists():
        return None
    for d in sorted(battles.iterdir(), reverse=True):
        if slug in d.name:
            r = _read(d / name)
            if r:
                return r
    return None

def _latest_battle(battles: Path, slug: str):
    if not battles.exists():
        return None
    for d in sorted(battles.iterdir(), reverse=True):
        if slug in d.name and (d / "result.json").exists():
            return d.name
    return None
