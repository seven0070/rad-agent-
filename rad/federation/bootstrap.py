"""Federation bootstrap — Rad #2 peer exchange prep.

Makes N2 a 30-minute job: generate identity + secret, write peers.json,
emit the exact commands for the second machine.

CONTRACT: secrets generated locally, never transmitted by this module.
"""
import base64, json, secrets
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

def set_paths(home: Path):
    global _HOME; _HOME = Path(home)
_HOME = Path.home() / ".rad"

def init_local(agent_id: str) -> dict:
    """Create local federation identity + secret. Idempotent."""
    root = Path(_HOME); fdir = root / "federation"
    fdir.mkdir(parents=True, exist_ok=True)
    idf = fdir / "identity.json"
    if idf.exists():
        return json.loads(idf.read_text(encoding="utf-8"))
    secret = secrets.token_bytes(32)
    ident = {"agent_id": agent_id,
             "secret_b64": base64.b64encode(secret).decode(),
             "created_at": _now()}
    idf.write_text(json.dumps(ident, indent=2), encoding="utf-8")
    return ident

def add_peer(agent_id: str, secret_b64: str) -> list:
    """Register a peer (exchange secrets out-of-band: USB, signal, carrier pigeon)."""
    root = Path(_HOME); fdir = root / "federation"
    fdir.mkdir(parents=True, exist_ok=True)
    pf = fdir / "peers.json"
    peers = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else []
    peers = [p for p in peers if p["agent_id"] != agent_id]
    peers.append({"agent_id": agent_id, "secret_b64": secret_b64,
                  "added_at": _now()})
    pf.write_text(json.dumps(peers, indent=2), encoding="utf-8")
    return peers

def runbook() -> str:
    return (
        "N2 BOOTSTRAP RUNBOOK:\n"
        "  machine A: python -c \"from rad.federation.bootstrap import init_local; "
        "print(init_local('A')['secret_b64'])\"\n"
        "  machine B: same with 'B'\n"
        "  exchange secrets out-of-band; each side: add_peer(other_id, other_secret)\n"
        "  either side: cross_audit(run_a, run_b, grader_fn) -> first inter-agent verdict")
