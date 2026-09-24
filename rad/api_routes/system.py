"""System routes: ledger, vitals, health, doctor, status."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from rad import __version__
from rad.api_security import ApiError
from rad.api_services import status_payload


class SystemMixin:
    """GET /ledger, /vitals, /health, /doctor, /status."""

    def _route_system(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                      ) -> Optional[Tuple[int, Any]]:
        if p == ["ledger"] and m == "GET":
            from rad.desktop_ledger import folded as _fold, summary as _lsum, set_paths
            set_paths(self.home.root)
            f = _fold()
            f["summary"] = _lsum()
            return 200, f
        if p == ["vitals"] and m == "GET":
            from rad.vitals import collect as _collect, report as _report
            from rad import curiosity as _cu

            root = getattr(self.home, "root", Path.home() / ".rad")
            v = _collect(root)
            canary_f = Path(root) / "cadence" / "last_canary.json"
            canary = (json.loads(canary_f.read_text(encoding="utf-8"))
                      if canary_f.exists() else None)
            cur_f = Path(root) / "curiosity" / "last_exploration.json"
            cur_last = (json.loads(cur_f.read_text(encoding="utf-8"))
                        if cur_f.exists() else None)
            return 200, {
                "vitals": v,
                "human": _report(v),
                "curiosity": {"report": _cu.wake_report(), "last": cur_last},
                "cadence": canary,
            }
        if p == ["health"] and m == "GET":
            from rad.storage import Storage
            st = Storage(self.home); st.pending()
            return 200, {"ok": True, "version": __version__, "schema": st.version(),
                         "running": sorted(k for k, t in self._runs.items() if t.is_alive())}
        if p == ["doctor"] and m == "GET":
            from rad.doctor import Doctor
            fix = q.get("fix") == "1" and bool(self.home.cfg.get("allow_api_fix"))
            fs = Doctor(self.home, fix=fix, probe_network=q.get("probe") == "1").run()
            return 200, {"findings": [f.__dict__ for f in fs], "fix_applied": fix}
        if p == ["status"] and m == "GET":
            return 200, status_payload(self.home, self._ctl, self._runs)
        return None
