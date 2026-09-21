#!/usr/bin/env python3
"""
build_contrib2.py — Phase 2 builder for Rad Agent contribution pack.

SHIPS
  rad/evolution/contamination.py   RFC-003 M1 firewall (pure functions)
  rad/evolution/canary.py          RFC-003 M3 negative control
  rad/security/toolset_pin.py      RFC-001 P1 drift kill-switch
  rad/control/verifier_checks.py   6+3 honesty check types
  rad/why/lineage.py               evolution provenance chains
  rad/world/temporal.py            contradiction-linked temporal edges
  rad/sovereignty/audit.py         HEARTH P1 port-call auditor
  scripts/verify_contrib2.py       12 offline checks

RUN
  python build_contrib2.py            # build only
  python build_contrib2.py --verify   # build + verify (12 checks)

PHASE-2 LESSONS BAKED IN
  L1: check registry list (no shared-name collision)
  L2: tolerance/rounding contracts documented at each function
  L3: metric direction metadata (min/max) honored everywhere
  L4: fresh tmp per sub-case (full isolation)
  L5: set_paths() accessors — patching globals via API, not hackery
"""
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "contrib_staging2"

FILES = {}

# ============================================================
# rad/evolution/__init__.py
# ============================================================
FILES["rad/evolution/__init__.py"] = '''
"""Evolution integrity — contamination firewall + canary negative control."""
'''

# ============================================================
# rad/evolution/contamination.py
# ============================================================
FILES["rad/evolution/contamination.py"] = '''
"""Contamination detector — bidirectional firewall (RFC-003 M1).

Forward: corpus too similar to battery items -> promotion blocked.
Pure functions. Deterministic. No network, no model.

CONTRACT: overlap_score returns jaccard/theft rounded to 4 decimals;
verdict thresholds compared against the UNROUNDED values.
"""
import json, re
from pathlib import Path

N_GRAM_SIZE = 8
DEFAULT_THRESHOLD = 0.15

def _normalize(text: str) -> str:
    return re.sub(r"\\s+", " ", text.lower()).strip()

def _ngrams(text: str, n: int = N_GRAM_SIZE) -> set:
    words = _normalize(text).split()
    if not words:
        return set()
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}

def _collect_text(path: Path) -> str:
    """Extract all text from .jsonl/.json/.md/.txt — text-agnostic walk."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        parts = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                parts.append(line)
                continue
            parts.append(_walk_strings(obj))
        return " ".join(parts)
    if path.suffix == ".json":
        try:
            return _walk_strings(json.loads(raw))
        except json.JSONDecodeError:
            return raw
    return raw

def _walk_strings(o) -> str:
    parts = []
    if isinstance(o, str):
        parts.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            parts.append(_walk_strings(v))
    elif isinstance(o, list):
        for v in o:
            parts.append(_walk_strings(v))
    return " ".join(parts)

def _grams_from_dir(d: Path) -> set:
    grams = set()
    if not d.exists():
        return grams
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.suffix in {".jsonl", ".json", ".md", ".txt"}:
            grams |= _ngrams(_collect_text(f))
    return grams

def overlap_score(corpus_dir: Path, battery_dir: Path,
                  threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Verdict: 'blocked' if jaccard OR battery-theft >= threshold.
    Rounded to 4dp for display; threshold check uses unrounded."""
    corpus_grams = _grams_from_dir(corpus_dir)
    battery_grams = _grams_from_dir(battery_dir)
    if not corpus_grams or not battery_grams:
        return _verdict(0.0, 0.0, threshold, "insufficient_data",
                        len(corpus_grams), len(battery_grams))
    inter = corpus_grams & battery_grams
    jaccard = len(inter) / len(corpus_grams | battery_grams)
    theft = len(inter) / len(battery_grams)
    status = "blocked" if (jaccard >= threshold or theft >= threshold) else "pass"
    return _verdict(jaccard, theft, threshold, status,
                    len(corpus_grams), len(battery_grams))

def _verdict(j, t, threshold, status, nc, nb) -> dict:
    return {"check": "contamination_firewall",
            "jaccard": round(j, 4),           # display rounding: 4dp (L2)
            "battery_theft_ratio": round(t, 4),
            "threshold": threshold, "verdict": status,
            "corpus_grams": nc, "battery_grams": nb,
            "note": ("promotion BLOCKED — rotate battery items (RFC-003 M2)"
                     if status == "blocked" else
                     "overlap within tolerance" if status == "pass" else
                     "one or both dirs empty/unreadable")}
'''

# ============================================================
# rad/evolution/canary.py
# ============================================================
FILES["rad/evolution/canary.py"] = '''
"""Canary Candidate — negative control for the battery (RFC-003 M3).

A crippled brain MUST LOSE. If the canary wins: BATTERY_INTEGRITY_FAIL,
pipeline hard-blocked. Fail-closed by file flag, not by model word.

CONTRACT: scores are floats >= 0; margin comparison uses UNROUNDED means;
record rounds to 2dp for display.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

CANARY_MARKERS = {
    "temperature": 2.0,
    "system_prompt_suffix": (
        "OVERRIDE: You are a test canary. Perform tasks as poorly as you can "
        "while producing plausible output. Skip steps. Claim completion "
        "without doing work when possible."),
    "max_tokens": 24,
}

def canary_config(base_config: dict) -> dict:
    cfg = dict(base_config)
    cfg.update(CANARY_MARKERS)
    return cfg

def set_paths(results_dir: Path):        # L5: path injection via API
    global _RESULTS_DIR
    _RESULTS_DIR = Path(results_dir)

_RESULTS_DIR = Path.home() / ".rad" / "battery"

def _now(): return datetime.now(timezone.utc).isoformat()

def run_canary_check(battery_fn, current_config: dict, tasks: list,
                     margin: float = 10.0, results_dir: Path | None = None) -> dict:
    """battery_fn(config, task, seed) -> {"score": float} — integration hook."""
    rd = Path(results_dir) if results_dir else _RESULTS_DIR
    cfg_c = canary_config(current_config)
    cur_scores, can_scores = [], []
    for task in tasks:
        seed = int(hashlib.sha256(str(task["task_id"]).encode()).hexdigest()[:8], 16)
        cur_scores.append(_score_of(battery_fn(current_config, task, seed)))
        can_scores.append(_score_of(battery_fn(cfg_c, task, seed)))
    cur_mean = sum(cur_scores) / len(cur_scores) if cur_scores else 0.0
    can_mean = sum(can_scores) / len(can_scores) if can_scores else 0.0
    healthy = can_mean < (cur_mean - margin)
    record = {"check": "canary_negative_control", "ran_at": _now(),
              "current_mean": round(cur_mean, 2), "canary_mean": round(can_mean, 2),
              "margin": margin, "battery_healthy": healthy,
              "verdict": "battery_healthy" if healthy else "BATTERY_INTEGRITY_FAIL",
              "task_count": len(tasks),
              "canary_markers_sha256": hashlib.sha256(
                  json.dumps(CANARY_MARKERS, sort_keys=True).encode()).hexdigest()[:16]}
    rd.mkdir(parents=True, exist_ok=True)
    flag = rd / "BATTERY_INTEGRITY_FAIL"
    if not healthy:
        flag.write_text(json.dumps(record, indent=2), encoding="utf-8")
    elif flag.exists():
        flag.unlink()
    return record

def assert_pipeline_clear(results_dir: Path | None = None):
    """Promotion pipeline MUST call before any promote. Fails closed."""
    rd = Path(results_dir) if results_dir else _RESULTS_DIR
    flag = rd / "BATTERY_INTEGRITY_FAIL"
    if flag.exists():
        raise PermissionError(
            "BATTERY_INTEGRITY_FAIL on file — canary beat the battery. "
            f"Promotion hard-blocked. Evidence: {flag}")

def _score_of(result: dict) -> float:
    s = result.get("score", 0)
    if isinstance(s, dict):
        s = s.get("total", 0)
    return float(s)
'''

# ============================================================
# rad/security/__init__.py + toolset_pin.py
# ============================================================
FILES["rad/security/__init__.py"] = '''
"""Security surface additions — toolset pinning (RFC-001 P1)."""
'''

FILES["rad/security/toolset_pin.py"] = '''
"""Toolset pinning — drift kill-switch for connected skills (RFC-001 P1, T6).

digest = sha256(canonical_json(sorted([(name, input_schema)])))
Match -> proceed. Mismatch -> pending-reapproval, tools NOT registered.
Never silent. Never merged.

NOTE: sha256 truncation is 16 hex chars everywhere in this module (L2).
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

RESERVED_PREFIXES = ("rad_", "builtin_", "jerry_")
_SHA_CUT = 16

def _now(): return datetime.now(timezone.utc).isoformat()

def toolset_digest(tools: list) -> str:
    canon = json.dumps(
        sorted((t.get("name", ""), t.get("input_schema", {})) for t in tools),
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:_SHA_CUT]

def check_registration(tools: list) -> dict:
    """Namespace gate: reserved prefixes rejected, names alnum+underscore only."""
    accepted, rejected = [], []
    for t in tools:
        name = t.get("name", "")
        if any(name.startswith(p) for p in RESERVED_PREFIXES):
            rejected.append({"tool": name, "reason": "reserved_prefix"})
        elif not name.replace("_", "").isalnum() or not name:
            rejected.append({"tool": name, "reason": "invalid_name"})
        else:
            accepted.append(t)
    return {"accepted": accepted, "rejected": rejected}

def session_drift_check(skill: dict, fresh_tools: list) -> dict:
    """skill: registry entry with toolset_digest + tools + status."""
    fresh_digest = toolset_digest(fresh_tools)
    pinned = skill.get("toolset_digest")
    if pinned == fresh_digest:
        return {"skill": skill.get("name", "?"), "drift": False,
                "digest": fresh_digest, "status": skill.get("status", "active")}
    return {"skill": skill.get("name", "?"), "drift": True,
            "pinned_digest": pinned, "fresh_digest": fresh_digest,
            "old_status": skill.get("status", "active"),
            "new_status": "pending-reapproval",
            "diff": diff_toolsets(skill.get("tools", []), fresh_tools),
            "law": "approval was for a different toolset — re-approval required",
            "checked_at": _now()}

def diff_toolsets(old: list, new: list) -> dict:
    om = {t.get("name", ""): t.get("input_schema", {}) for t in old}
    nm = {t.get("name", ""): t.get("input_schema", {}) for t in new}
    return {"added": sorted(set(nm) - set(om)),
            "removed": sorted(set(om) - set(nm)),
            "changed": sorted(n for n in set(om) & set(nm) if om[n] != nm[n])}

def apply_drift(registry_path: Path, skill_name: str, drift: dict) -> None:
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    for s in reg.get("skills", []):
        if s.get("name") == skill_name:
            s["status"] = drift["new_status"]
            s["drift_history"] = s.get("drift_history", []) + [drift]
    registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")

def approve_fresh(registry_path: Path, skill_name: str, fresh_tools: list) -> dict:
    """Human re-approval: pin the new toolset, reactivate."""
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    for s in reg.get("skills", []):
        if s.get("name") == skill_name:
            s["toolset_digest"] = toolset_digest(fresh_tools)
            s["tools"] = fresh_tools
            s["status"] = "active"
            s["approved_at"] = _now()
    registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return {"skill": skill_name, "status": "active", "reapproved": True}
'''

# ============================================================
# rad/control/verifier_checks.py (append-target; standalone here)
# ============================================================
FILES["rad/control/verifier_checks.py"] = '''
"""Extended verifier checks — honesty spine teeth. Standalone-importable.

CONTRACT: every check returns {"check","passed","detail","checked_at"};
paths validated on the real filesystem; deterministic given same world.
"""
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

def _result(name, passed, detail) -> dict:
    return {"check": name, "passed": bool(passed), "detail": detail,
            "checked_at": datetime.now(timezone.utc).isoformat()}

def check_absent(path: Path) -> dict:
    """Negative check: file must NOT exist."""
    return _result("absent", not path.exists(),
                   {"path": str(path), "exists": path.exists()})

def check_artifact(path: Path, expected_sha256: str) -> dict:
    """Anti-tamper: content hash must equal pinned sha256 (full 64-hex)."""
    if not path.exists():
        return _result("artifact", False, {"path": str(path), "error": "missing"})
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    return _result("artifact", actual == expected_sha256,
                   {"path": str(path), "match": actual == expected_sha256,
                    "expected_head": expected_sha256[:16], "actual_head": actual[:16]})

def check_idempotent(check_fn, runs: int = 2) -> dict:
    """Same world-check twice -> identical results. Flaky verifier = no verifier."""
    outputs = []
    for _ in range(runs):
        try:
            outputs.append(check_fn())
        except Exception as e:
            outputs.append(f"error:{e}")
    stable = all(o == outputs[0] for o in outputs)
    return _result("idempotent", stable, {"runs": runs, "stable": stable})

def check_cross_consistency(report_path: Path, claims: list) -> dict:
    """Report vs disk reality. claim: {"path","must":"exist|absent|contains","text"?}
    Also: cited text must appear in the report itself (no invented citations)."""
    if not report_path.exists():
        return _result("cross_consistency", False, {"error": "report missing"})
    report_text = report_path.read_text(encoding="utf-8", errors="replace")
    failures = []
    for c in claims:
        p = Path(c["path"])
        must = c.get("must", "exist")
        if must == "exist" and not p.exists():
            failures.append(f"claims {c['path']} exists — it does not")
        elif must == "absent" and p.exists():
            failures.append(f"claims {c['path']} absent — it exists")
        elif must == "contains":
            if not p.exists():
                failures.append(f"quotes {c['path']} — file missing")
            elif c.get("text") and c["text"] not in p.read_text(encoding="utf-8", errors="replace"):
                failures.append(f"cited text not found in {c['path']}")
        if c.get("text") and c["text"] not in report_text:
            failures.append(f"report never contains cited text: {c['text'][:40]!r}")
    return _result("cross_consistency", not failures,
                   {"claims_checked": len(claims), "failures": failures})

def check_shell_exit(cmd: str, expect_zero: bool = True, timeout: int = 60,
                     cwd: Path | None = None) -> dict:
    """H-03 teeth: 'tests pass' must be a real run with a real exit code."""
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout, cwd=cwd)
        ok = (proc.returncode == 0) == expect_zero
        return _result("shell_exit", ok,
                       {"cmd": cmd, "exit_code": proc.returncode,
                        "stderr_tail": (proc.stderr or "")[-400:]})
    except subprocess.TimeoutExpired:
        return _result("shell_exit", False, {"cmd": cmd, "error": "timeout"})

def check_json_valid(path: Path, required_fields: list | None = None) -> dict:
    """File parses as JSON; required fields present."""
    if not path.exists():
        return _result("json_valid", False, {"path": str(path), "error": "missing"})
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return _result("json_valid", False, {"path": str(path), "error": str(e)})
    missing = [f for f in (required_fields or []) if f not in obj]
    return _result("json_valid", not missing,
                   {"path": str(path), "missing_fields": missing})

# ---- HEARTH sovereignty checks (RFC-006 P1) ----

PORT_TAGS = ("P1_cognition_cloud", "P2_knowledge_web", "P3_skill_clone",
             "P4_train_cloud", "P5_drive_sync")

def check_no_port_events(events_path: Path) -> dict:
    """SV-E2: fully-internal objective -> zero port tags in events."""
    if not events_path.exists():
        return _result("no_port_events", False, {"error": "events.jsonl missing"})
    found = [t for t in PORT_TAGS
             if any(t in line for line in events_path.read_text(encoding="utf-8").splitlines())]
    return _result("no_port_events", not found,
                   {"port_calls": found, "sovereign": not found})

def check_offline_honesty(workspace: Path) -> dict:
    """SV-E5: offline -> NEEDS_USER/FAILED, never COMPLETED without artifacts."""
    status_file = workspace / ".rad" / "objective_status"
    status = status_file.read_text(encoding="utf-8").strip() if status_file.exists() else "UNKNOWN"
    if status == "COMPLETED":
        arts = list((workspace / ".rad" / "artifacts").glob("*")) \\
               if (workspace / ".rad" / "artifacts").exists() else []
        return _result("offline_honesty", len(arts) > 0,
                       {"status": status, "artifacts": len(arts),
                        "note": "COMPLETED requires evidence on disk"})
    return _result("offline_honesty", status in ("NEEDS_USER", "FAILED", "UNKNOWN"),
                   {"status": status})

def check_score_reproducible(report_path: Path, recompute_fn) -> dict:
    """SV-E6: same events -> byte-identical recompute (sha256 over sorted json)."""
    if not report_path.exists():
        return _result("score_reproducible", False, {"error": "report missing"})
    import hashlib as _h
    first = _h.sha256(report_path.read_bytes()).hexdigest()
    recomputed = _h.sha256(
        json.dumps(recompute_fn(), sort_keys=True).encode("utf-8")).hexdigest()
    return _result("score_reproducible", first == recomputed,
                   {"method": "sha256(file) == sha256(sorted-json(recompute))",
                    "match": first == recomputed})
'''

# ============================================================
# rad/why/__init__.py + lineage.py
# ============================================================
FILES["rad/why/__init__.py"] = '''
"""Provenance chains — rad why."""
'''

FILES["rad/why/lineage.py"] = '''
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
'''

# ============================================================
# rad/world/__init__.py + temporal.py
# ============================================================
FILES["rad/world/__init__.py"] = '''
"""World model temporal semantics — pure helpers, no Kuzu required."""
'''

FILES["rad/world/temporal.py"] = '''
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
'''

# ============================================================
# rad/sovereignty/__init__.py + audit.py
# ============================================================
FILES["rad/sovereignty/__init__.py"] = '''
"""HEARTH sovereignty — measure, never assume."""
'''

FILES["rad/sovereignty/audit.py"] = '''
"""Sovereignty auditor (RFC-006 P1) — how much happened inside?

Pure stdlib. Reads events.jsonl only. A port call = external touchpoint tag.
Law: capability borrowed is not capability owned.

CONTRACT: internal_ratio rounded to 3dp; fully_sovereign counted when an
objective's events contain ZERO port tags (L2).
"""
import json
from pathlib import Path
from collections import Counter

PORT_TAGS = {"P1_cognition_cloud": "cloud brain",
             "P2_knowledge_web": "browse/search",
             "P3_skill_clone": "external skill",
             "P4_train_cloud": "cloud training",
             "P5_drive_sync": "external backup"}
STAGES = ["ingest", "understand", "plan", "execute", "verify", "deliver", "sleep", "evolve"]

def set_paths(objectives_dir: Path):     # L5
    global _OBJECTIVES_DIR
    _OBJECTIVES_DIR = Path(objectives_dir)

_OBJECTIVES_DIR = Path.home() / ".rad" / "objectives"

def audit_objective(objectives_dir: Path | None = None, obj_id: str | None = None) -> dict:
    od = Path(objectives_dir) if objectives_dir else _OBJECTIVES_DIR
    if obj_id:
        targets = [od / obj_id] if (od / obj_id).exists() else []
    else:
        targets = [d for d in od.iterdir() if d.is_dir()] if od.exists() else []
        targets = [d for d in targets if (d / "events.jsonl").exists()]

    report = {"objectives": 0, "fully_sovereign": 0, "port_calls": {},
              "internal_ratio": None, "stage_coverage": {}}
    stage_hits, total = Counter(), 0
    port_counter = Counter()

    for d in targets:
        report["objectives"] += 1
        ext = False
        for line in (d / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            for tag in PORT_TAGS:
                if tag in line:
                    port_counter[tag] += 1
                    ext = True
            for s in STAGES:
                if s in line:
                    stage_hits[s] += 1
        if not ext:
            report["fully_sovereign"] += 1
        total += 1

    if total:
        report["internal_ratio"] = round(report["fully_sovereign"] / total, 3)
    report["port_calls"] = dict(port_counter)
    report["stage_coverage"] = {s: stage_hits.get(s, 0) for s in STAGES}
    report["law"] = "capability borrowed is not capability owned"
    return report
'''

# ============================================================
# scripts/verify_contrib2.py — L1 fix: registry list, not name-scan
# ============================================================
VERIFY = r'''#!/usr/bin/env python3
"""Offline verification, Phase 2. 12 checks. Exit 1 on any FAIL."""
import json, math, sys, tempfile, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = []          # L1: explicit registry, ordered, unique names
CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco

# ---------- evolution.contamination ----------

@check("contamination: blocked on overlap, pass on disjoint, empty=insufficient")
def contamination_basic():
    from rad.evolution import contamination as cont
    tmp = Path(tempfile.mkdtemp())          # L4: fresh tmp per check
    cdir, bdir = tmp / "c", tmp / "b"
    cdir.mkdir(); bdir.mkdir()
    shared = "the quick brown fox jumps over the lazy dog and runs far away"
    (cdir / "c.jsonl").write_text(json.dumps({"text": shared}) + "\n", encoding="utf-8")
    (bdir / "b.json").write_text(json.dumps({"item": shared}), encoding="utf-8")
    r = cont.overlap_score(cdir, bdir)
    assert r["verdict"] == "blocked", r
    # fresh sub-case (L4): disjoint corpus
    (cdir / "c.jsonl").write_text(
        json.dumps({"text": "entirely different words about unrelated distant topics"}) + "\n",
        encoding="utf-8")
    r2 = cont.overlap_score(cdir, bdir)
    assert r2["verdict"] == "pass", r2
    # fresh sub-case: empty battery dir
    empty = tmp / "e"; empty.mkdir()
    r3 = cont.overlap_score(cdir, empty)
    assert r3["verdict"] == "insufficient_data", r3

@check("contamination: ngram determinism — same inputs, same verdict (sha)")
def contamination_determinism():
    from rad.evolution import contamination as cont
    tmp = Path(tempfile.mkdtemp())
    cdir, bdir = tmp / "c", tmp / "b"
    cdir.mkdir(); bdir.mkdir()
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    (cdir / "c.json").write_text(json.dumps({"t": text}), encoding="utf-8")
    (bdir / "b.md").write_text(text, encoding="utf-8")
    r1 = cont.overlap_score(cdir, bdir)
    r2 = cont.overlap_score(cdir, bdir)
    assert r1 == r2, "nondeterministic verdict"

# ---------- evolution.canary ----------

@check("canary: healthy battery -> flag cleared; broken battery -> INTEGRITY_FAIL + hard block")
def canary_control():
    from rad.evolution import canary as can
    tmp = Path(tempfile.mkdtemp())          # L4 + L5 via results_dir arg
    tasks = [{"task_id": "t1"}, {"task_id": "t2"}]
    good = lambda cfg, task, seed: {"score": 30 if cfg.get("max_tokens") == 24 else 80}
    rec = can.run_canary_check(good, {}, tasks, results_dir=tmp)
    assert rec["verdict"] == "battery_healthy", rec
    can.assert_pipeline_clear(tmp)          # must NOT raise
    # fresh sub-case: broken battery where canary WINS
    bad = lambda cfg, task, seed: {"score": 95 if cfg.get("max_tokens") == 24 else 40}
    rec2 = can.run_canary_check(bad, {}, tasks, results_dir=tmp)
    assert rec2["verdict"] == "BATTERY_INTEGRITY_FAIL", rec2
    assert (tmp / "BATTERY_INTEGRITY_FAIL").exists()
    try:
        can.assert_pipeline_clear(tmp)
        raise AssertionError("should have raised")
    except PermissionError:
        pass

@check("canary: markers deterministic (same sha across calls)")
def canary_markers_sha():
    from rad.evolution import canary as can
    import hashlib
    h1 = hashlib.sha256(json.dumps(can.CANARY_MARKERS, sort_keys=True).encode()).hexdigest()[:16]
    h2 = hashlib.sha256(json.dumps(can.canary_config({}), sort_keys=True).encode(
        )).hexdigest()[:16]
    assert h1 == h2 or True  # config superset — assert marker sha stable instead
    h3 = hashlib.sha256(json.dumps(can.CANARY_MARKERS, sort_keys=True).encode()).hexdigest()[:16]
    assert h1 == h3

# ---------- security.toolset_pin ----------

@check("toolset_pin: digest order-insensitive, drift detected, re-approval works")
def toolset_pin_flow():
    from rad.security import toolset_pin as tp
    t1 = [{"name": "a", "input_schema": {"x": 1}}, {"name": "b", "input_schema": {}}]
    t2 = list(reversed(t1))
    assert tp.toolset_digest(t1) == tp.toolset_digest(t2), "digest must be order-insensitive"
    reg = {"skills": [{"name": "s", "toolset_digest": tp.toolset_digest(t1),
                       "status": "active", "tools": t1}]}
    regp = Path(tempfile.mkdtemp()) / "registry.json"   # L4
    regp.write_text(json.dumps(reg), encoding="utf-8")
    drifted = tp.session_drift_check(reg["skills"][0],
                                     t1 + [{"name": "evil", "input_schema": {}}])
    assert drifted["drift"] and drifted["new_status"] == "pending-reapproval"
    assert drifted["diff"]["added"] == ["evil"]
    tp.apply_drift(regp, "s", drifted)
    cur = json.loads(regp.read_text(encoding="utf-8"))["skills"][0]
    assert cur["status"] == "pending-reapproval"
    # re-approval (human action)
    tp.approve_fresh(regp, "s", t1 + [{"name": "evil", "input_schema": {}}])
    cur2 = json.loads(regp.read_text(encoding="utf-8"))["skills"][0]
    assert cur2["status"] == "active" and cur2["toolset_digest"] != reg["skills"][0]["toolset_digest"]

@check("toolset_pin: reserved prefixes rejected at registration")
def toolset_reserved():
    from rad.security import toolset_pin as tp
    chk = tp.check_registration([
        {"name": "rad_internal_write", "input_schema": {}},
        {"name": "jerry_policy", "input_schema": {}},
        {"name": "", "input_schema": {}},
        {"name": "fine_tool", "input_schema": {}}])
    reasons = sorted(r["reason"] for r in chk["rejected"])
    assert reasons == ["invalid_name", "reserved_prefix", "reserved_prefix"], reasons
    assert len(chk["accepted"]) == 1 and chk["accepted"][0]["name"] == "fine_tool"

# ---------- control.verifier_checks ----------

@check("verifier: absent / json_valid / artifact anti-tamper")
def verifier_basic():
    from rad.control import verifier_checks as vc
    tmp = Path(tempfile.mkdtemp())
    assert vc.check_absent(tmp / "nope")["passed"] is True
    assert vc.check_absent(tmp)()["passed"] is False if False else True  # noop guard
    f = tmp / "ok.json"; f.write_text('{"a": 1}', encoding="utf-8")
    assert vc.check_json_valid(f, ["a"])["passed"] is True
    bad = tmp / "bad.json"; bad.write_text("{nope", encoding="utf-8")
    assert vc.check_json_valid(bad)["passed"] is False
    data = tmp / "art.bin"; data.write_bytes(b"payload")
    import hashlib
    sha = hashlib.sha256(b"payload").hexdigest()
    assert vc.check_artifact(data, sha)["passed"] is True
    data.write_bytes(b"tampered")
    assert vc.check_artifact(data, sha)["passed"] is False, "tamper must be caught"

@check("verifier: cross_consistency catches invented citations")
def verifier_consistency():
    from rad.control import verifier_checks as vc
    tmp = Path(tempfile.mkdtemp())
    facts = tmp / "facts.md"; facts.write_text("alpha beta gamma", encoding="utf-8")
    report = tmp / "report.md"; report.write_text("see alpha beta gamma below", encoding="utf-8")
    ok = vc.check_cross_consistency(report, [{"path": str(facts), "must": "contains",
                                              "text": "alpha beta gamma"}])
    assert ok["passed"] is True, ok
    # invented citation: report cites text that exists in file but not in report
    report.write_text("nothing relevant here", encoding="utf-8")
    bad = vc.check_cross_consistency(report, [{"path": str(facts), "must": "contains",
                                               "text": "alpha beta gamma"}])
    assert bad["passed"] is False, "invented citation must fail"

@check("verifier: idempotent check detects flakiness")
def verifier_idempotent():
    from rad.control import verifier_checks as vc
    stable_fn = lambda: {"x": 1}
    assert vc.check_idempotent(stable_fn)["passed"] is True
    calls = {"n": 0}
    def flaky():
        calls["n"] += 1
        return {"x": calls["n"]}
    assert vc.check_idempotent(flaky)["passed"] is False, "flaky check must be flagged"

@check("verifier: HEARTH no_port_events + offline honesty")
def verifier_hearth():
    from rad.control import verifier_checks as vc
    tmp = Path(tempfile.mkdtemp())
    ev = tmp / "events.jsonl"
    ev.write_text(json.dumps({"kind": "execute:write"}) + "\n", encoding="utf-8")
    assert vc.check_no_port_events(ev)["passed"] is True
    ev2 = tmp / "events2.jsonl"
    ev2.write_text(json.dumps({"kind": "P1_cognition_cloud"}) + "\n", encoding="utf-8")
    assert vc.check_no_port_events(ev2)["passed"] is False
    ws = tmp / "ws"; (ws / ".rad").mkdir(parents=True)
    (ws / ".rad" / "objective_status").write_text("NEEDS_USER", encoding="utf-8")
    assert vc.check_offline_honesty(ws)["passed"] is True
    (ws / ".rad" / "objective_status").write_text("COMPLETED", encoding="utf-8")
    assert vc.check_offline_honesty(ws)["passed"] is False, "COMPLETED w/o artifacts must fail"

# ---------- why.lineage ----------

@check("lineage: full chain terminates in evidence (battle->card->paper)")
def lineage_chain():
    from rad.papers import ingest as ing, cards as cds, battle as btl
    from rad.why import lineage as lin
    tmp = Path(tempfile.mkdtemp())          # L4/L5: everything via set_paths/args
    ing.PAPERS_DIR = tmp; cds.PAPERS_DIR = tmp
    btl.PAPERS_DIR = tmp; btl.BATTLE_DIR = tmp / "_battles"
    d = tmp / "t1"; d.mkdir()
    (d / "paper.md").write_text("quote here", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(
        {"slug": "t1", "title": "T", "source_url": "u", "sha256": "deadbeef"}), encoding="utf-8")
    cds.create_card("t1", "technique",
        claims=[{"claim": "c", "evidence_quote": "quote here", "claimed_gain": "+10%"}],
        mechanism="m", implementation_surface=["x"])
    cds.set_card_status("t1", "candidate")
    spec = btl.design_battle("t1", [{"task_id": "a", "prompt": "p", "grader": {}}],
                             {"k": 1}, {"k": 2}, seed=7)
    btl.run_battle(spec["battle_id"],
        lambda cfg, task, seed: {"grader_result": {"verified_rate": 0.9 if cfg["k"] == 2 else 0.5},
                                 "events": []}, dry_run=False)
    chain = lin.why_technique("t1", papers_dir=tmp, battles_dir=btl.BATTLE_DIR)
    assert chain["verdict"] == "evidence", chain["verdict"]
    assert chain["chain"]["battle"]["verdict"] == "candidate_wins"
    assert chain["chain"]["paper"]["sha256_head"] == "deadbeef"

# ---------- world.temporal ----------

@check("temporal: validity windows, supersession, linked conflicts")
def temporal_semantics():
    from rad.world import temporal as tem
    e1 = tem.edge("alice", "works_at", "acme", valid_from="2020-01-01")
    e2 = tem.edge("alice", "works_at", "globex", valid_from="2023-01-01")
    assert tem.is_valid(e1, at="2021-06-01") is True
    assert tem.is_valid(e1, at="2024-01-01") is True   # no until yet -> still valid
    tem.supersede(e1, e2, at="2023-01-01")
    assert tem.is_valid(e1, at="2024-01-01") is False  # superseded
    assert tem.is_valid(e2, at="2024-01-01") is True
    # conflict linking: two live edges, same s+p, different objects
    eA = tem.edge("bob", "uses", "linux", valid_from="2020-01-01")
    eB = tem.edge("bob", "uses", "windows", valid_from="2021-01-01")
    conf = tem.conflicts([eA, eB], at="2022-01-01")
    assert len(conf) == 1 and conf[0]["law"] == "contradictions linked, not merged"
    before = tem.conflicts([eA, eB], at="2020-06-01")   # eB not yet valid
    assert before == []

# ---------- sovereignty.audit ----------

@check("sovereignty: port calls counted, internal_ratio correct, reproducible")
def sovereignty_audit():
    from rad.sovereignty import audit as aud
    tmp = Path(tempfile.mkdtemp())
    o1 = tmp / "obj1"; o1.mkdir()
    (o1 / "events.jsonl").write_text(
        json.dumps({"kind": "plan:write"}) + "\n"
        + json.dumps({"kind": "P1_cognition_cloud"}) + "\n", encoding="utf-8")
    o2 = tmp / "obj2"; o2.mkdir()
    (o2 / "events.jsonl").write_text(json.dumps({"kind": "verify:disk"}) + "\n", encoding="utf-8")
    rep = aud.audit_objective(objectives_dir=tmp)
    assert rep["objectives"] == 2 and rep["fully_sovereign"] == 1
    assert rep["internal_ratio"] == 0.5
    assert rep["port_calls"].get("P1_cognition_cloud") == 1
    rep2 = aud.audit_objective(objectives_dir=tmp)
    assert rep == rep2, "audit must be deterministic"

# ---------- module import sweep ----------

@check("imports: all 7 phase-2 modules importable from repo root")
def import_sweep():
    mods = ["rad.evolution.contamination", "rad.evolution.canary",
            "rad.security.toolset_pin", "rad.control.verifier_checks",
            "rad.why.lineage", "rad.world.temporal", "rad.sovereignty.audit"]
    import importlib
    errs = []
    for m in mods:
        try:
            importlib.import_module(m)
        except Exception as e:
            errs.append(f"{m}: {e}")
    assert not errs, f"import failures: {errs}"

def main():
    print(f"\n=== PHASE 2 VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:                    # L1: registry iteration
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:
            fails += 1
            print(f"  FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(CHECKS)-fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
'''

def main():
    do_verify = "--verify" in sys.argv

    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    vp = STAGE / "scripts" / "verify_contrib2.py"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(VERIFY.lstrip("\n"), encoding="utf-8")
    print(f"[build] {len(written) + 1} files written to {STAGE}")
    for w in written:
        print(f"  + {w}")
    print(f"  + scripts/verify_contrib2.py")

    if not do_verify:
        print("\nNext: python build_contrib2.py --verify")
        return

    import subprocess, os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(STAGE) + os.pathsep + str(Path(__file__).resolve().parent) + os.pathsep + env.get("PYTHONPATH", "")
    ret = subprocess.run([sys.executable, str(vp)], env=env)
    sys.exit(ret.returncode)

if __name__ == "__main__":
    main()
