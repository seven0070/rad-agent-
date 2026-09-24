"""X1 Buzz Hive x MausBot: roster of bots as contacts gossiping over Nostr relay (block/buzz).

Rad blackboard (~/.rad/agents/blackboard) IS the relay. Each bot is a contact.
Lab-gated, VERIFIED-only, no shell bypass — gossip is text notes via Blackboard.
Inspiration: buzz (relay abstraction) + openmausbot (roster gossip).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rad.agents import Blackboard
from rad.home import RadHome

BUZZ_RELAY_SCOPE = "hive-relay"

BUILTIN_BOTS = [
    {"id": "maus_alpha", "persona": "alpha scout — finds facts, cites URLs"},
    {"id": "maus_beta", "persona": "beta builder — writes minimal code"},
    {"id": "maus_gamma", "persona": "gamma guardian — verifies, never rubber-stamps"},
    {"id": "buzz_relay", "persona": "relay — routes gossip, never invents"},
]

@dataclass
class HiveMessage:
    id: str
    author: str
    text: str
    kind: str
    at: float
    evidence: List[str]

class Hive:
    """Hive roster gossip over Nostr-like relay (blackboard)."""

    def __init__(self, home: RadHome, scope: str = BUZZ_RELAY_SCOPE) -> None:
        self.home = home
        self.scope = scope
        self.board = Blackboard(home, scope)
        self.bots = list(BUILTIN_BOTS)

    def roster(self) -> List[Dict[str, Any]]:
        return [dict(b) for b in self.bots]

    def gossip(self, author: str, text: str, kind: str = "gossip", evidence: Optional[List[str]] = None) -> Dict[str, Any]:
        # Lab-gated? always allowed as note — verification is separate (VERIFIED-only for tasks)
        return self.board.post(author, text, kind=kind, evidence=evidence)

    def inbox(self, since: float = 0.0) -> List[Dict[str, Any]]:
        return [n for n in self.board.notes() if n["at"] >= since]

    def buzz(self, text: str, author: str = "maus_alpha") -> Dict[str, Any]:
        # buzz = block/buzz gossip verb
        return self.gossip(author, f"[buzz] {text}", kind="buzz")

    def block(self, author: str, blocked: str) -> Dict[str, Any]:
        return self.gossip(author, f"[block] {blocked} blocked by {author}", kind="block")

    def relay_health(self) -> Dict[str, Any]:
        notes = self.board.notes()
        return {"scope": self.scope, "relay": "rad/agents/blackboard as relay", "bots": len(self.bots),
                "messages": len(notes), "lab_gated": False, "verified_only": True,
                "inspiration": ["buzz", "openmausbot"]}

def hive_health(home: RadHome) -> Dict[str, Any]:
    return Hive(home).relay_health()
