"""Challenge Rounds — B proves A's work live, without trusting A.

Sovereignty: challenger sees artifacts only. Determinism: same seed+grader+
artifacts = same verdict. Bundles: HMAC-signed, verify + optional recheck.

CONTRACT (L2): artifact hashes truncated 16 hex; signature full 64 hex.
"""
import hashlib, hmac, json
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()
def _sha16(b) -> str:
    if isinstance(b, str): b = b.encode("utf-8")
    return hashlib.sha256(b).hexdigest()[:16]

def set_paths(base: Path):               # L5
    global _BASE
    _BASE = Path(base)
_BASE = Path.home() / ".rad" / "federation"

# ---------- evidence bundles ----------

def make_bundle(agent_id: str, secret: bytes, claims: list) -> dict:
    """claims: [{"path","sha256","check","passed"}] — disk-derived only."""
    body = {"agent": agent_id,
            "issued_at": _now(), "claims": claims}
    payload = json.dumps(body, sort_keys=True).encode("utf-8")
    return {"body": body, "signature": hmac.new(secret, payload,
            hashlib.sha256).hexdigest(), "algo": "hmac-sha256"}

def verify_bundle(bundle: dict, secret: bytes, recheck_fn=None) -> dict:
    payload = json.dumps(bundle["body"], sort_keys=True).encode("utf-8")
    origin_ok = hmac.compare_digest(
        hmac.new(secret, payload, hashlib.sha256).hexdigest(),
        bundle.get("signature", ""))
    truth_ok, failures = True, []
    if recheck_fn:
        for c in bundle["body"].get("claims", []):
            if not recheck_fn(c):
                truth_ok = False
                failures.append(c.get("path", "?"))
    return {"origin_verified": origin_ok, "truth_verified": truth_ok,
            "failed_rechecks": failures,
            "verdict": "TRUSTED" if origin_ok and truth_ok else "REJECTED"}

# ---------- challenge rounds ----------

def issue_challenge(challenger: str, task: str, seed: int,
                    grader_name: str, artifact_spec: dict) -> dict:
    cid = f"ch-{_sha16(f'{challenger}{task}{seed}'.encode())}"
    return {"type": "challenge.v0", "challenge_id": cid,
            "challenger": challenger, "task": task, "task_sha256": _sha16(task),
            "seed": seed, "grader": grader_name, "artifact_spec": artifact_spec,
            "issued_at": _now(), "status": "open"}

def respond_challenge(challenge: dict, run_fn) -> dict:
    """run_fn(task, seed, workspace) -> {"events": [...]}. Runs under A's own
    Jerry. Only artifact hashes + bounded events leave."""
    import tempfile
    ws = Path(tempfile.mkdtemp(prefix="chal-"))
    result = run_fn(challenge["task"], challenge["seed"], ws)
    artifacts = {}
    for rel in challenge["artifact_spec"].get("files", []):
        f = ws / rel
        if f.exists():
            artifacts[rel] = _sha16(f.read_bytes())
    return {"type": "response.v0", "challenge_id": challenge["challenge_id"],
            "artifacts": artifacts,
            "events": list(result.get("events", []))[:100],
            "workspace": str(ws), "responded_at": _now()}

def grade_challenge(challenge: dict, response: dict,
                    artifact_fetcher, grader_fn, ledger_fn=None) -> dict:
    """grader_fn(workspace) -> bool — runs LOCALLY on fetched artifacts."""
    ws = Path(response["workspace"])
    have = set(artifact_fetcher(response.get("artifacts", {})).keys())
    need = set(challenge["artifact_spec"].get("files", []))
    ok = bool(grader_fn(ws)) and need.issubset(have)
    verdict = {"type": "verdict.v0", "challenge_id": challenge["challenge_id"],
               "passed": ok, "regraded_by": challenge["challenger"],
               "graded_at": _now(),
               "determinism": "same seed+grader+artifacts reproduce this verdict"}
    if ledger_fn:
        ledger_fn(verdict)
    return verdict

def cross_audit(run_a, run_b, grader_fn, n_rounds: int = 2,
                ledger_fn=None) -> dict:
    """N4 atom: symmetric challenges. run_x(task, seed, workspace) -> events.
    A governor is only credible while 'you check me' holds."""
    results = {"a_of_b": [], "b_of_a": []}
    def one(challenger, run_fn, task, seed):
        c = issue_challenge(challenger, task, seed, "disk_facts",
                            {"files": ["facts.md"]})
        resp = respond_challenge(c, run_fn)
        return grade_challenge(c, resp, lambda h: h, grader_fn, ledger_fn)
    for i in range(n_rounds):
        results["a_of_b"].append(one("A", run_b, "write 3 verified facts to facts.md", i))
        results["b_of_a"].append(one("B", run_a, "write 3 verified facts to facts.md", i))
    a_ok = all(v["passed"] for v in results["a_of_b"])
    b_ok = all(v["passed"] for v in results["b_of_a"])
    results["standing"] = {"A": "verified" if b_ok else "demoted",
                           "B": "verified" if a_ok else "demoted"}
    return results
