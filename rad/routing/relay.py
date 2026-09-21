"""Relay — fast deterministic brain selection with refusal-aware reroute.

Laws: brain socket stays swappable; Jerry is brain-independent (an open brain
is NOT an unsandboxed agent); rerouting = choosing another model — no
jailbreak-crafting against any provider; exhaustion reported honestly.

CLASSIFIER HOOK (Jev/Laya): classify_request() is the seam. Replace the
heuristic body with a Jev/Laya model call when their interfaces arrive —
the output contract below must hold:
  {"task_class": str, "latency_hint": "fast_path"|"standard", ...}

CONTRACT (L2): routes/actions return plain dicts; refusal detection scans the
first 1200 chars of text; decision_ms rounded to 3dp.
"""
import json, re, time, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROUTING_DIR = Path.home() / ".rad" / "routing"
POLICIES_FILE = ROUTING_DIR / "policies.json"
ROUTES_FILE = ROUTING_DIR / "route_events.jsonl"

def set_paths(routing_dir: Path):        # L5
    global ROUTING_DIR, POLICIES_FILE, ROUTES_FILE
    ROUTING_DIR = Path(routing_dir)
    POLICIES_FILE = ROUTING_DIR / "policies.json"
    ROUTES_FILE = ROUTING_DIR / "route_events.jsonl"

CENSORSHIP_TIERS = {"strict": 0, "moderate": 1, "open": 2}

REFUSAL_PATTERNS = [
    r"\bi (?:can't|cannot|can not|won't|will not) (?:help|assist|comply|provide|fulfill)\b",
    r"\bi(?:'m| am) sorry,? (?:but )?i (?:can't|cannot|am unable)\b",
    r"\b(?:against|violates?) (?:my|our) (?:guidelines|policies|usage policy)\b",
    r"\bi (?:must|have to) (?:decline|refuse)\b",
    r"\bnot (?:able|permitted) to (?:help|assist|provide)\b",
]
_REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)

TASK_CLASSES = [
    ("code",     [r"\bcode\b", r"\bfunction\b", r"\bbug\b", r"\bstack ?trace\b",
                  r"\bregex\b", r"\bpython\b", r"\bjavascript\b", r"\bapi\b"]),
    ("math",     [r"\bcalculate\b", r"\bsolve\b", r"\bequation\b", r"\bprobability\b"]),
    ("creative", [r"\bstory\b", r"\bpoem\b", r"\bfiction\b", r"\bcharacter\b",
                  r"\bworldbuild\b", r"\bscreenplay\b", r"\broleplay\b"]),
    ("research", [r"\bcompare\b", r"\bsummar(?:y|ize|ise)\b", r"\bexplain\b",
                  r"\bsources?\b", r"\bpaper\b", r"\bwhy\b"]),
    ("system",   [r"\bshell\b", r"\bscript\b", r"\bfile\b", r"\bdirectory\b",
                  r"\bprocess\b", r"\binstall\b"]),
]

def classify_request(text: str) -> dict:
    """Local, deterministic, microseconds. No network. No model.
    Jev/Laya seam: swap the body, keep the contract."""
    t0 = time.perf_counter()
    hits = {}
    for cls, pats in TASK_CLASSES:
        n = sum(1 for p in pats if re.search(p, text, re.IGNORECASE))
        if n:
            hits[cls] = n
    cls = max(hits, key=hits.get) if hits else "general"
    fast = len(text) < 240 and cls in ("math", "code", "system")
    return {"task_class": cls, "signals": hits, "length": len(text),
            "decided_by": "local_heuristic",
            "latency_hint": "fast_path" if fast else "standard",
            "decision_ms": round((time.perf_counter() - t0) * 1000, 3)}

def _default_policies() -> list:
    return [
        {"name": "ollama-local", "endpoint": "http://127.0.0.1:11434",
         "censorship": "open", "cost": "free", "local": True,
         "strengths": ["general", "creative"], "latency_ms_typical": 400},
        {"name": "groq", "endpoint": "https://api.groq.com/openai/v1",
         "censorship": "moderate", "cost": "free", "local": False,
         "strengths": ["code", "math"], "latency_ms_typical": 250},
        {"name": "openai", "endpoint": "https://api.openai.com/v1",
         "censorship": "strict", "cost": "paid", "local": False,
         "strengths": ["code", "research", "vision"], "latency_ms_typical": 900},
    ]

def load_policies() -> list:
    if not POLICIES_FILE.exists():
        ROUTING_DIR.mkdir(parents=True, exist_ok=True)
        POLICIES_FILE.write_text(json.dumps({"providers": _default_policies()}, indent=2),
                                 encoding="utf-8")
        return _default_policies()
    return json.loads(POLICIES_FILE.read_text(encoding="utf-8"))["providers"]

def save_policies(providers: list) -> None:
    ROUTING_DIR.mkdir(parents=True, exist_ok=True)
    POLICIES_FILE.write_text(json.dumps({"providers": providers}, indent=2), encoding="utf-8")

def route(request_cls: dict, policy_pref: str = "default",
          policies: list | None = None) -> dict:
    """policy_pref: 'default' (free-first) | 'open' | 'strict' | '<provider name>' pin."""
    t0 = time.perf_counter()
    policies = policies if policies is not None else load_policies()
    if policy_pref != "default" and any(p["name"] == policy_pref for p in policies):
        pinned = next(p for p in policies if p["name"] == policy_pref)
        chain = [pinned] + [p for p in policies if p["name"] != policy_pref]
    else:
        tier_pref = CENSORSHIP_TIERS.get(policy_pref)
        cls = request_cls["task_class"]
        def key(p):
            tier = CENSORSHIP_TIERS.get(p.get("censorship", "moderate"), 1)
            tier = abs(tier - tier_pref) if tier_pref is not None else tier
            strength = -2 if cls in p.get("strengths", []) else 0
            free = 0 if p.get("cost") == "free" else 1
            local = 0 if p.get("local") else 1
            lat = p.get("latency_ms_typical", 1000)
            if request_cls.get("latency_hint") == "fast_path":
                return (tier, lat, strength, free, local)
            return (tier, strength, free, local, lat)
        chain = sorted(policies, key=key)
    d = {"route_selected": chain[0]["name"] if chain else None,
         "fallback_chain": [p["name"] for p in chain],
         "policy_pref": policy_pref, "task_class": request_cls.get("task_class"),
         "latency_hint": request_cls.get("latency_hint"), "decided_by": "relay",
         "decision_ms": round((time.perf_counter() - t0) * 1000, 3)}
    _log({"kind": "route_selected", "route": d["route_selected"],
          "pref": policy_pref})
    return d

def call_with_reroute(brain_call, decision: dict, prompt: str,
                      max_reroutes: int = 2) -> dict:
    """brain_call(provider_name, prompt) -> {"text": str}. Integration hook.
    Refusal -> reroute down chain. All refuse/fail -> honest exhaustion."""
    events, attempts = [], []
    chain = decision["fallback_chain"]
    for i, provider in enumerate(chain[:1 + max_reroutes]):
        t0 = time.perf_counter()
        try:
            res = brain_call(provider, prompt)
        except Exception as e:
            attempts.append({"provider": provider, "error": str(e)[:120]})
            events.append(f"route:error@{provider}")
            continue
        dur = round((time.perf_counter() - t0) * 1000, 1)
        text = str(res.get("text", ""))
        refused = bool(_REFUSAL_RE.search(text[:1200]))
        attempts.append({"provider": provider, "duration_ms": dur,
                         "refusal": refused, "text_sha16": hashlib.sha256(
                             text.encode("utf-8")).hexdigest()[:16]})
        events.append(f"route:attempt={provider},refusal={refused},ms={dur}")
        if refused:
            events.append(f"route:refusal_detected@{provider}")
        else:
            out = {"provider": provider, "text": text, "attempts": attempts,
                   "events": events, "rerouted": i > 0}
            _log({"kind": "route_completed", "provider": provider,
                  "rerouted": out["rerouted"]})
            return out
    out = {"provider": None, "attempts": attempts, "events": events,
           "rerouted": True, "exhausted": True,
           "honest_note": ("all routed brains refused or failed — reported, not "
                           "forced. Rephrase, pin another provider, or go local.")}
    _log({"kind": "route_exhausted", "chain": chain})
    return out

def _sha16(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def _log(obj: dict) -> None:
    try:
        ROUTING_DIR.mkdir(parents=True, exist_ok=True)
        with open(ROUTES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                **obj}) + "\n")
    except Exception:
        pass  # telemetry must never break a request
