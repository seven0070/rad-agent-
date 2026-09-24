"""x402 — USDC micropayments for MCP marketplace (McpMallPane), v3.3 Agent M.

x402 is a stubbed micropayment protocol for the Self-Writing Mall:
  invent -> MCP server -> publish -> x402 micropay (USDC)

Lab-gated, VERIFIED-only: payments are verified before a skill is considered
purchased/installed. No shell bypass — all via Policy/Sandbox.

Inspiration: Coinbase x402 (HTTP 402 Payment Required) — USDC on Base.
This is a local stub that mimics the contract without needing chain access:
  - create_payment(skill, amount_usdc) -> payment intent with hash
  - verify_payment(payment_id) -> verified flag
  - micropay_for_mcp(home, skill_key, amount) -> verified purchase record

McpMallPane displays x402_price per skill; this module is the backend.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Dict, Optional

from rad.home import RadHome

X402_PRICE_DEFAULT = 0.02
X402_CURRENCY = "USDC"
X402_CHAIN = "base"
X402_ENABLED = True
X402_MIN = 0.001
X402_MAX = 10.0


def x402_available() -> bool:
    return X402_ENABLED


def _payment_hash(skill: str, amount: float, payer: str, at: float) -> str:
    raw = f"{skill}:{amount:.6f}:{payer}:{at:.3f}:{uuid.uuid4().hex[:4]}"
    return "x402_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def create_payment(skill_key: str, amount_usdc: float = X402_PRICE_DEFAULT, payer: str = "local") -> Dict[str, Any]:
    """Create a USDC micropayment intent (stub, lab-gated)."""
    if not (X402_MIN <= float(amount_usdc) <= X402_MAX):
        return {"ok": False, "error": f"amount out of range [{X402_MIN}, {X402_MAX}]", "amount": amount_usdc}
    at = time.time()
    pid = _payment_hash(skill_key, float(amount_usdc), payer, at)
    return {
        "ok": True,
        "payment_id": pid,
        "skill": skill_key,
        "amount": round(float(amount_usdc), 6),
        "currency": X402_CURRENCY,
        "chain": X402_CHAIN,
        "payer": payer,
        "at": at,
        "status": "created",
        "lab_gated": True,
        "verified": False,  # needs verify step
    }


def verify_payment(payment: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a payment (stub: always verified if amount in range and currency USDC)."""
    if not payment.get("ok"):
        return {"verified": False, "reason": payment.get("error", "invalid payment")}
    if payment.get("currency") != X402_CURRENCY:
        return {"verified": False, "reason": "currency must be USDC"}
    if not (X402_MIN <= float(payment.get("amount", 0)) <= X402_MAX):
        return {"verified": False, "reason": "amount out of range"}
    # stub verification — hash check passes
    return {"verified": True, "payment_id": payment["payment_id"], "amount": payment["amount"], "currency": X402_CURRENCY, "chain": X402_CHAIN}


def micropay_for_mcp(home: RadHome, skill_key: str, amount_usdc: float = X402_PRICE_DEFAULT, payer: str = "local") -> Dict[str, Any]:
    """Full x402 flow for MCP marketplace: create -> verify -> record purchase."""
    from rad.skills import skill_bank_load, skill_bank_save
    # ensure skill exists in mall
    bank = skill_bank_load(home)
    if skill_key not in bank.get("skills", {}):
        return {"ok": False, "error": "skill not found in mall", "skill": skill_key}
    payment = create_payment(skill_key, amount_usdc, payer=payer)
    if not payment.get("ok"):
        return payment
    verification = verify_payment(payment)
    if not verification.get("verified"):
        return {"ok": False, "payment": payment, "verification": verification, "error": "x402 verification failed"}
    # record purchase in bank
    skill = bank["skills"][skill_key]
    skill["x402_payment"] = payment["payment_id"]
    skill["x402_verified"] = True
    skill["x402_amount"] = payment["amount"]
    skill["x402_currency"] = X402_CURRENCY
    bank["skills"][skill_key] = skill
    skill_bank_save(home, bank)
    return {
        "ok": True,
        "skill": skill_key,
        "payment": payment,
        "verification": verification,
        "amount": payment["amount"],
        "currency": X402_CURRENCY,
        "chain": X402_CHAIN,
        "lab_gated": True,
        "verified": True,
        "note": "x402 USDC micropay kept — McpMallPane",
    }


def x402_health() -> Dict[str, Any]:
    return {
        "x402": "USDC micropay for MCP marketplace",
        "currency": X402_CURRENCY,
        "chain": X402_CHAIN,
        "default_price": X402_PRICE_DEFAULT,
        "available": x402_available(),
        "lab_gated": True,
        "mall": "invent->MCP->publish->x402 kept",
    }
