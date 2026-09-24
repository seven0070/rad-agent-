"""Memory routes: list, recall, remember."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError
from rad.api_services import mem_entry


class MemoryMixin:
    """GET/POST /memory, GET /memory/recall."""

    def _route_memory(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                      ) -> Optional[Tuple[int, Any]]:
        if p == ["memory", "recall"] and m == "GET":
            from rad.memory import Memory
            k = max(1, min(20, int(q.get("k", 5) or 5)))
            return 200, {"memories": [mem_entry(e) for e in Memory(self.home).recall(q.get("q", ""), k=k)]}
        if p == ["memory"] and m == "POST":
            from rad.memory import Memory
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            layer = b.get("layer", "semantic")
            if layer not in ("episodic", "semantic", "procedural"):
                raise ApiError(400, "layer must be episodic|semantic|procedural")
            e = Memory(self.home).add(layer, text, origin="USER_PROVIDED", source="api")
            return 201, mem_entry(e)
        if p == ["memory"] and m == "GET":
            from rad.memory import Memory
            mem = Memory(self.home)
            layer = q.get("layer") or ""
            layers = (layer,) if layer in ("working", "episodic", "semantic", "procedural") \
                else ("working", "episodic", "semantic", "procedural")
            n = max(1, min(200, int(q.get("n", 50) or 50)))
            out: Dict[str, Any] = {}
            for l in layers:
                try:
                    items = list(mem.scan(l))
                except Exception:
                    items = []
                out[l] = [mem_entry(e) for e in items[-n:]]
            return 200, {"memories": out}
        return None
