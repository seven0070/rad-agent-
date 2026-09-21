"""Replication Ledger — claimed vs measured, append-only, open.

Losses are data. `export_ledger()` emits the open replication dataset.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from .ingest import PAPERS_DIR
from .battle import BATTLE_DIR

LEDGER_FILE = PAPERS_DIR / "_ledger.jsonl"

def record_battle_outcome(battle_id: str) -> dict:
    bdir = BATTLE_DIR / battle_id
    if not (bdir / "result.json").exists():
        raise ValueError(f"No result for battle {battle_id!r}")
    result = json.loads((bdir / "result.json").read_text(encoding="utf-8"))
    spec = json.loads((bdir / "spec.json").read_text(encoding="utf-8"))
    cf = PAPERS_DIR / spec["slug"] / "card.json"
    card = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    claimed = [{"claim": c["claim"], "claimed_gain": c["claimed_gain"]}
               for c in card.get("claims", []) if c.get("claimed_gain")]
    measured = {m: {"baseline": d["baseline_mean"], "candidate": d["candidate_mean"],
                    "delta": d["delta"], "n": d["n"]}
                for m, d in result.get("scores", {}).items()}
    claimed_positive = any(("+" in g["claimed_gain"]) or ("%" in g["claimed_gain"]) or
                           ("improve" in g["claimed_gain"].lower()) or
                           any(char.isdigit() for char in g["claimed_gain"])
                           for g in claimed if g["claimed_gain"].lower() != "none")
    measured_positive = result.get("verdict") == "candidate_wins"
    if result.get("verdict") == "tie":
        verdict = "INCONCLUSIVE"
    else:
        verdict = ("CONFIRMED" if claimed_positive and measured_positive else
                   "NOT_REPLICATED" if claimed_positive else "NO_CLAIM_TO_TEST")
    entry = {"ledger_ts": datetime.now(timezone.utc).isoformat(),
             "battle_id": battle_id, "slug": spec["slug"],
             "paper_title": card.get("source", {}).get("title", ""),
             "paper_url": card.get("source", {}).get("url", ""),
             "paper_sha256": card.get("source", {}).get("sha256", ""),
             "seed": spec["seed"], "task_count": spec.get("task_count", 0),
             "claimed": claimed, "measured": measured,
             "battle_verdict": result.get("verdict", ""),
             "replication_verdict": verdict,
             "pareto_tradeoff": result.get("pareto_tradeoff", False),
             "claim_metrics": result.get("claim_metrics"),
             "coi_flags": card.get("coi_flags", [])}
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def record_amendment(battle_id: str, field: str, was: str, now: str, reason: str) -> dict:
    """Append-only ledger amendment. Never rewrites history; links corrections."""
    current_entries = {e["battle_id"]: e for e in read_ledger(apply_amendments=True)}
    if battle_id not in current_entries:
        raise ValueError(f"Battle {battle_id!r} not found in ledger")
    current_val = current_entries[battle_id].get(field)
    if current_val != was:
        raise ValueError(f"Amendment baseline mismatch for {battle_id} field {field!r}: "
                         f"expected was={current_val!r}, got was={was!r}")
    amendment = {
        "amendment_of": battle_id,
        "field": field,
        "was": was,
        "now": now,
        "reason": reason,
        "amended_at": datetime.now(timezone.utc).isoformat(),
    }
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(amendment) + "\n")
    return amendment

def read_ledger(apply_amendments: bool = True) -> list:
    if not LEDGER_FILE.exists(): return []
    raw = [json.loads(l) for l in LEDGER_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not apply_amendments:
        return raw
    entries = []
    by_id = {}
    for item in raw:
        if "amendment_of" in item:
            target_id = item["amendment_of"]
            if target_id in by_id:
                target = by_id[target_id]
                field = item.get("field")
                if field:
                    target[field] = item.get("now")
                target.setdefault("amendments", []).append(item)
        else:
            by_id[item.get("battle_id")] = item
            entries.append(item)
    return entries

def export_ledger(output_path=None) -> str:
    entries = read_ledger()
    verdicts = {}
    for e in entries:
        v = e.get("replication_verdict", "UNKNOWN")
        verdicts[v] = verdicts.get(v, 0) + 1
    data = {"format": "rad-replication-ledger", "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(entries),
            "summary": {"total_battles": len(entries), "verdicts": verdicts,
                        "replication_rate": round(verdicts.get("CONFIRMED", 0)/len(entries), 3) if entries else 0,
                        "papers_tested": len({e.get("slug") for e in entries})},
            "entries": entries}
    text = json.dumps(data, indent=2)
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    return text
