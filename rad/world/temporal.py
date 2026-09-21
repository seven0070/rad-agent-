"""Temporal world-model edges.

Laws: contradictions are LINKED, never merged. Supersession rewrites
neither side — old edge gets valid_until + superseded_by, stays on disk.

CONTRACT: date comparisons are ISO-8601 strings (YYYY-MM-DD or full
timestamps) — lexicographic order == chronological order. Mixed formats
within one edge set are the caller's responsibility (L2 documented).
"""
import hashlib
from datetime import datetime, timezone

def _today() -> str:
    return datetime.now(timezone.utc).isoformat()[:10]

def edge_id(subject: str, predicate: str, object_: str) -> str:
    return hashlib.sha256(f"{subject}|{predicate}|{object_}".encode()).hexdigest()[:16]

def edge(subject, predicate, object_, *, valid_from=None, valid_until=None,
         origin="observed", confidence=0.8, source_event=None) -> dict:
    return {"edge_id": edge_id(subject, predicate, object_),
            "subject": subject, "predicate": predicate, "object": object_,
            "valid_from": valid_from, "valid_until": valid_until,
            "origin": origin, "confidence": confidence,
            "superseded_by": None, "source_event": source_event}

def is_valid(e: dict, at: str | None = None) -> bool:
    t = at or _today()
    if e.get("superseded_by"):
        return False
    if e.get("valid_from") and t < e["valid_from"]:
        return False
    if e.get("valid_until") and t >= e["valid_until"]:
        return False
    return True

def supersede(old: dict, new: dict, at: str | None = None) -> dict:
    """Old is REWRITTEN (marked), never deleted."""
    t = at or _today()
    old["valid_until"] = t
    old["superseded_by"] = new["edge_id"]
    old["superseded_at"] = t
    return old

def active_edges(edges: list, at: str | None = None) -> list:
    return [e for e in edges if is_valid(e, at)]

def conflicts(edges: list, at: str | None = None) -> list:
    """Same (subject,predicate), both valid at t, different objects -> LINK."""
    t = at or _today()
    live = [e for e in edges if is_valid(e, t)]
    seen, out = {}, []
    for e in live:
        key = (e["subject"], e["predicate"])
        if key in seen and seen[key]["object"] != e["object"]:
            out.append({"subject": e["subject"], "predicate": e["predicate"],
                        "a": seen[key]["edge_id"], "b": e["edge_id"],
                        "a_object": seen[key]["object"], "b_object": e["object"],
                        "law": "contradictions linked, not merged"})
        else:
            seen[key] = e
    return out

def to_kuzu_rows(edges: list) -> dict:
    """Integration shim: shapes for Kuzu COPY FROM."""
    return {"node_rows": [[e["subject"], e["object"]] for e in edges],
            "rel_rows": [[e["edge_id"], e["subject"], e["predicate"], e["object"],
                          e.get("valid_from"), e.get("valid_until"),
                          e.get("superseded_by"), e["confidence"]] for e in edges]}
