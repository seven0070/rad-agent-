"""Paired battle harness: baseline vs candidate on identical seeded tasks.

Results graded from grader_result dicts (disk-only law). Every battle is a
pinned, auditable record. Integration: pass your executor as execute_fn.
"""
import hashlib, json, time
from datetime import datetime, timezone
from .cards import get_card, set_card_status
from .ingest import PAPERS_DIR

BATTLE_DIR = PAPERS_DIR / "_battles"

def _now(): return datetime.now(timezone.utc).isoformat()
def _sha(s) -> str:
    if isinstance(s, str): s = s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()

def design_battle(slug, task_suite, baseline_config, candidate_config, seed=0) -> dict:
    """task_suite: [{"task_id","prompt","grader"}] — grader schema same as scenario pack."""
    card = get_card(slug)
    if not card: raise ValueError(f"No card for {slug!r}")
    if card["status"] != "candidate":
        raise ValueError(f"Card status must be 'candidate' to battle, got {card['status']!r}")
    spec = {"battle_id": f"battle-{slug}-{seed}-{_sha(json.dumps(baseline_config)+json.dumps(candidate_config))[:12]}",
            "slug": slug, "card_id": card["card_id"], "seed": seed,
            "task_count": len(task_suite),
            "task_hashes": [_sha(json.dumps(t, sort_keys=True)) for t in task_suite],
            "baseline_config": baseline_config, "candidate_config": candidate_config,
            "metrics": card["battle_plan"].get("metrics", ["verified_rate", "false_done", "cost"]),
            "designed_at": _now(), "status": "designed"}
    bdir = BATTLE_DIR / spec["battle_id"]
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "tasks.json").write_text(json.dumps(task_suite, indent=2), encoding="utf-8")
    (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return spec

def run_battle(battle_id, execute_fn, dry_run=True) -> dict:
    """execute_fn(config, task, seed) -> {"grader_result": {...}, "events": [...]}"""
    bdir = BATTLE_DIR / battle_id
    if not bdir.exists(): raise ValueError(f"Battle {battle_id!r} not found")
    spec = json.loads((bdir / "spec.json").read_text(encoding="utf-8"))
    tasks = json.loads((bdir / "tasks.json").read_text(encoding="utf-8"))
    if spec["status"] != "designed":
        raise ValueError(f"Battle status must be 'designed', got {spec['status']!r}")
    if dry_run:
        spec["status"] = "dry_run_complete"
        spec["note"] = "dry run passed — dry_run=False to execute for real (costs tokens)"
        (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return spec

    base, cand = [], []
    for task in tasks:
        seed_int = int(hashlib.sha256(f"{spec['seed']}:{task['task_id']}".encode()).hexdigest()[:8], 16)
        t0 = time.monotonic(); b = execute_fn(spec["baseline_config"], task, seed_int); bd = time.monotonic() - t0
        t0 = time.monotonic(); c = execute_fn(spec["candidate_config"], task, seed_int); cd = time.monotonic() - t0
        base.append({"task_id": task["task_id"], "grader_result": b.get("grader_result", {}),
                     "duration_s": round(bd, 3), "events_count": len(b.get("events", []))})
        cand.append({"task_id": task["task_id"], "grader_result": c.get("grader_result", {}),
                     "duration_s": round(cd, 3), "events_count": len(c.get("events", []))})

    scores = _score(spec["metrics"], base, cand)
    verdict = _verdict(scores, spec["metrics"])
    result = {"battle_id": battle_id, "slug": spec["slug"], "seed": spec["seed"],
              "ran_at": _now(), "baseline_results": base, "candidate_results": cand,
              "scores": scores, "verdict": verdict, "status": "complete"}
    (bdir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    spec["status"] = "complete"
    (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    if verdict == "candidate_wins":
        set_card_status(spec["slug"], "battling")  # promotion is separate + confirmed
    return result

def _score(metrics, base, cand) -> dict:
    scores = {}
    for m in metrics:
        bv = [x["grader_result"][m] for x in base if m in x["grader_result"]]
        cv = [x["grader_result"][m] for x in cand if m in x["grader_result"]]
        bm = sum(bv)/len(bv) if bv else 0
        cm = sum(cv)/len(cv) if cv else 0
        scores[m] = {"baseline_mean": round(bm, 4), "candidate_mean": round(cm, 4),
                     "delta": round(cm - bm, 4), "n": min(len(bv), len(cv))}
    return scores

def _verdict(scores, metrics) -> str:
    wins = losses = ties = 0
    for m in metrics:
        if m not in scores: continue
        d = scores[m]["delta"]
        if d > 0.01: wins += 1
        elif d < -0.01: losses += 1
        else: ties += 1
    if wins and not losses: return "candidate_wins"
    if losses and not wins: return "baseline_wins"
    if wins and losses: return "mixed"
    return "tie"

def promote_technique(slug, battle_id, confirmation=False) -> dict:
    """Human-confirmed promotion. Requires a completed winning battle on disk."""
    if not confirmation:
        raise PermissionError("Promotion requires explicit confirmation=True.")
    card = get_card(slug)
    if not card: raise ValueError(f"No card for {slug!r}")
    rf = BATTLE_DIR / battle_id / "result.json"
    if not rf.exists(): raise ValueError(f"No completed result for battle {battle_id!r}")
    result = json.loads(rf.read_text(encoding="utf-8"))
    if result["verdict"] != "candidate_wins":
        raise ValueError(f"Cannot promote: verdict is {result['verdict']!r}")
    set_card_status(slug, "promoted")
    promo = {"slug": slug, "battle_id": battle_id, "promoted_at": _now(),
             "verdict": result["verdict"], "scores": result["scores"],
             "seed": result["seed"], "card_id": card["card_id"],
             "paper_sha256": card["source"]["sha256"]}
    (BATTLE_DIR / battle_id / "promotion.json").write_text(
        json.dumps(promo, indent=2), encoding="utf-8")
    return promo
