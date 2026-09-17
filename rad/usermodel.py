"""User model — a structured, inspectable picture of the user, separate from raw memories.

    ~/.rad/user.json
    {
      "preferences": {"editor": {"value": "vim", "origin": "USER_PROVIDED", "confidence": 0.9, ...}},
      "goals": [...], "projects": [...], "constraints": [...], "routines": [...],
      "communication": {...}, "active_priorities": [...]
    }

Every field carries origin/confidence/source/at, like memories. The user can inspect and
correct it (`rad user`, `rad user set <section> <key> <value>`, `rad user forget …`).
It is injected into the system prompt as a compact block; nothing here is ever
silently promoted from a model guess to a fact.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from rad.home import RadHome, _write_json
from rad.memory import INFERRED, MODEL_GENERATED, ORIGIN_CONFIDENCE, ORIGINS, USER_PROVIDED

SECTIONS = ("preferences", "goals", "projects", "constraints", "routines", "communication",
            "active_priorities", "permissions")
DICT_SECTIONS = {"preferences", "communication", "permissions"}
LIST_SECTIONS = set(SECTIONS) - DICT_SECTIONS


def _fact(value: Any, origin: str, source: str, confidence: Optional[float]) -> Dict[str, Any]:
    if origin not in ORIGINS:
        origin = INFERRED
    return {"value": value, "origin": origin, "source": source,
            "confidence": ORIGIN_CONFIDENCE[origin] if confidence is None else confidence,
            "at": time.time()}


class UserModel:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "user.json"

    def data(self) -> Dict[str, Any]:
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        if not isinstance(d, dict):
            d = {}
        for s in SECTIONS:
            want = dict if s in DICT_SECTIONS else list
            if not isinstance(d.get(s), want):
                d[s] = want()
        return d

    def save(self, d: Dict[str, Any]) -> None:
        d["updated"] = time.time()
        _write_json(self.path, d)

    # ------------------------------------------------------------ write
    def set(self, section: str, key: str, value: Any, origin: str = USER_PROVIDED,
            source: str = "user", confidence: Optional[float] = None) -> bool:
        """Set a keyed fact. A weaker origin never overwrites a stronger one."""
        if section not in DICT_SECTIONS:
            raise ValueError(f"{section} is not a keyed section; use add()")
        d = self.data()
        cur = d[section].get(key)
        new = _fact(value, origin, source, confidence)
        if cur and ORIGIN_CONFIDENCE.get(cur["origin"], 0) > ORIGIN_CONFIDENCE[new["origin"]] \
                and cur["value"] != value:
            # keep the trusted value but remember the disagreement
            cur.setdefault("disputed_by", []).append(new)
            d[section][key] = cur
            self.save(d)
            return False
        d[section][key] = new
        self.save(d)
        return True

    def add(self, section: str, value: str, origin: str = USER_PROVIDED, source: str = "user",
            confidence: Optional[float] = None) -> bool:
        if section not in LIST_SECTIONS:
            raise ValueError(f"{section} is a keyed section; use set()")
        d = self.data()
        for item in d[section]:
            if str(item["value"]).strip().lower() == value.strip().lower():
                if ORIGIN_CONFIDENCE[origin] > ORIGIN_CONFIDENCE.get(item["origin"], 0):
                    item.update(origin=origin, source=source,
                                confidence=ORIGIN_CONFIDENCE[origin] if confidence is None else confidence)
                    self.save(d)
                return False
        d[section].append(_fact(value.strip(), origin, source, confidence))
        self.save(d)
        return True

    def forget(self, section: str, key_or_value: str) -> bool:
        d = self.data()
        if section in DICT_SECTIONS:
            if key_or_value in d[section]:
                del d[section][key_or_value]
                self.save(d)
                return True
            return False
        before = len(d[section])
        d[section] = [i for i in d[section]
                      if str(i["value"]).lower() != key_or_value.lower()
                      and not str(i["value"]).lower().startswith(key_or_value.lower())]
        if len(d[section]) != before:
            self.save(d)
            return True
        return False

    def learn_from_text(self, text: str, caller=None, source: str = "chat") -> int:
        """Extract user facts from a message. LLM-backed when available (→ MODEL_GENERATED,
        low confidence); a small deterministic set of patterns otherwise (→ INFERRED)."""
        import re
        n = 0
        if caller is not None:
            try:
                raw = caller(
                    "From the text below extract ONLY durable facts about the USER themselves "
                    "(not about the world). Reply ONLY JSON: {\"preferences\": {\"key\": \"value\"}, "
                    "\"goals\": [], \"projects\": [], \"constraints\": [], \"routines\": [], "
                    "\"communication\": {\"key\": \"value\"}}. Empty if none.\n\n" + text[:3000])
                m = re.search(r"\{.*\}", raw or "", re.S)
                got = json.loads(m.group(0)) if m else {}
                for k, v in (got.get("preferences") or {}).items():
                    n += self.set("preferences", str(k)[:40], str(v)[:120], MODEL_GENERATED, source)
                for k, v in (got.get("communication") or {}).items():
                    n += self.set("communication", str(k)[:40], str(v)[:120], MODEL_GENERATED, source)
                for sec in ("goals", "projects", "constraints", "routines"):
                    for v in (got.get(sec) or [])[:5]:
                        n += self.add(sec, str(v)[:160], MODEL_GENERATED, source)
                return n
            except Exception:
                pass
        low = text.strip()
        pats = [
            (r"\bi (?:prefer|like|love|always use)\s+(.{3,60}?)(?:[.,;]|$)", "preferences", "likes"),
            (r"\bmy (?:goal|aim|objective) is to\s+(.{3,100}?)(?:[.;]|$)", "goals", None),
            (r"\bi(?:'m| am) (?:working on|building)\s+(.{3,80}?)(?:[.,;]|$)", "projects", None),
            (r"\b(?:never|don't|do not)\s+(.{3,80}?)(?:[.;]|$)", "constraints", None),
            (r"\bcall me\s+([A-Z][\w-]+)", "communication", "name"),
            (r"\b(?:reply|answer|respond) (?:in|with)\s+(short|brief|detailed|long) (?:answers|replies)", "communication", "verbosity"),
        ]
        for pat, sec, key in pats:
            for m in re.finditer(pat, low, re.I):
                val = m.group(1).strip()
                if sec in DICT_SECTIONS:
                    n += self.set(sec, key, val, INFERRED, source)
                else:
                    n += self.add(sec, val, INFERRED, source)
        return n

    # ------------------------------------------------------------ read
    def context_block(self, max_items: int = 10) -> str:
        d = self.data()
        lines: List[str] = []
        for k, f in list(d["communication"].items())[:4]:
            lines.append(f"- communication.{k}: {f['value']} ({f['origin'].lower()})")
        for k, f in list(d["preferences"].items())[:4]:
            lines.append(f"- prefers {k}: {f['value']} ({f['origin'].lower()})")
        for sec in ("active_priorities", "goals", "projects", "constraints"):
            for f in d[sec][:3]:
                lines.append(f"- {sec[:-1] if sec.endswith('s') else sec}: {f['value']} ({f['origin'].lower()})")
        if not lines:
            return ""
        return "User model (inspect/correct with `rad user`; model_generated = unconfirmed guess):\n" + \
            "\n".join(lines[:max_items])

    def show(self) -> str:
        from rad.ui import col
        d = self.data()
        out = []
        empty = True
        for sec in SECTIONS:
            items = d[sec]
            if not items:
                continue
            empty = False
            out.append(f"  {col.bold(sec)}")
            if sec in DICT_SECTIONS:
                for k, f in items.items():
                    disp = col.yellow(" (disputed)") if f.get("disputed_by") else ""
                    meta = col.dim(f"{f['origin'].lower()} c={f['confidence']:.2f}")
                    out.append(f"    {k:<18} {f['value']}  {meta}{disp}")
            else:
                for f in items:
                    meta = col.dim(f"{f['origin'].lower()} c={f['confidence']:.2f}")
                    out.append(f"    • {f['value']}  {meta}")
        if empty:
            out.append("  (empty — `rad user set preferences editor vim`, or it learns from chat)")
        return "\n".join(out)
