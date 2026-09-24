"""DAO swarm with x402 — signature weird.

Agents coordinate via DAO proposal/vote, micropay via x402 stub.
Lab-gated, VERIFIED-only — votes are blackboard notes, x402 is stubbed.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

from rad.agents import Blackboard
from rad.home import RadHome

DAO_SCOPE = "dao-swarm"

def propose(home: RadHome, author: str, proposal: str, amount_x402: float = 0.01) -> Dict[str, Any]:
    board = Blackboard(home, DAO_SCOPE)
    note = board.post(author, f"[DAO PROPOSE] {proposal} — x402:${amount_x402:.3f}", kind="dao_propose")
    return {"proposal_id": note["id"], "proposal": proposal, "x402": amount_x402, "author": author, "at": note["at"], "lab_gated": True}

def vote(home: RadHome, voter: str, proposal_id: str, yay: bool = True) -> Dict[str, Any]:
    board = Blackboard(home, DAO_SCOPE)
    note = board.post(voter, f"[DAO VOTE] {proposal_id} -> {'YAY' if yay else 'NAY'}", kind="dao_vote")
    return {"vote_id": note["id"], "proposal_id": proposal_id, "voter": voter, "yay": yay, "lab_gated": True}

def dao_health(home: RadHome) -> Dict[str, Any]:
    board = Blackboard(home, DAO_SCOPE)
    notes = board.notes()
    return {"dao": "swarm DAO with x402", "scope": DAO_SCOPE, "proposals": len([n for n in notes if n["kind"] == "dao_propose"]), "votes": len([n for n in notes if n["kind"] == "dao_vote"]), "x402": "stub — micropay kept", "lab_gated": True}
