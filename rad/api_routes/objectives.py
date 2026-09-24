"""Objective routes: list/create/detail, lifecycle actions, views, tasks."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError
from rad.api_services import (
    artifact_content,
    create_objective,
    live_payload,
    may_run,
    obj_summary,
    observations_payload,
    plan_payload,
    recovery_payload,
)


class ObjectivesMixin:
    """GET/POST /objectives, /objectives/{id}[/sub], GET /tasks."""

    def _route_objectives(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                          ) -> Optional[Tuple[int, Any]]:
        if p == ["objectives"] and m == "GET":
            store = self._ctl().store
            objs = store.list(active_only=q.get("active") == "1")
            rows = []
            for o in objs:
                try:
                    rows.append(obj_summary(o, store.load_tasks(o.id)))
                except Exception:
                    rows.append(obj_summary(o))
            return 200, {"objectives": rows}
        if p == ["objectives"] and m == "POST":
            return create_objective(self.home, self._ctl, b, self._background)
        if len(p) >= 2 and p[0] == "objectives":
            ctl = self._ctl()
            obj = ctl.store.resolve(p[1])
            if not obj:
                raise ApiError(404, f"no objective {p[1]}")
            if len(p) == 2 and m == "GET":
                d = obj.to_dict(); d["tasks"] = ctl.store.load_tasks(obj.id)
                return 200, d
            if len(p) == 3 and m == "POST" and p[2] in ("resume", "pause", "cancel", "run"):
                if p[2] == "pause":
                    o = ctl.pause(obj.id)
                elif p[2] == "cancel":
                    o = ctl.cancel(obj.id)
                else:
                    if not may_run(self.home):
                        raise ApiError(409, "config auto=false: HTTP cannot answer confirmation prompts; run `rad objective run` in a terminal or set auto")
                    if p[2] == "run":
                        # Controller.run plans a PENDING objective if it has no plan yet;
                        # resume assumes a plan exists. Same background-thread semantics.
                        self._background(obj.id, lambda: ctl.run(obj))
                        return 202, {"id": obj.id, "status": "starting"}
                    self._background(obj.id, lambda: ctl.resume(obj.id))
                    return 202, {"id": obj.id, "status": "resuming"}
                return 200, obj_summary(o or obj)
            if len(p) == 3 and m == "GET" and p[2] == "events":
                from rad.control.events import EventLog
                since = int(q.get("since_seq", 0) or 0)
                evs = [e.__dict__ for e in EventLog(ctl.store.events_path(obj.id)).read(kind=q.get("kind") or None)
                       if e.seq > since]
                return 200, {"events": evs[-int(q.get("n", 500) or 500):]}
            if len(p) == 3 and m == "GET" and p[2] == "trace":
                return 200, {"objective": obj_summary(obj), "tasks": ctl.store.load_tasks(obj.id),
                             "verification": obj.verification}
            if len(p) == 3 and m == "GET" and p[2] == "why":
                from rad.control.provenance import Provenance
                pv = Provenance(ctl.store.dir(obj.id))
                claim = q.get("q", "")
                if not claim:
                    raise ApiError(400, "q=<artifact path | claim text> required")
                art = pv.artifact(claim)
                return 200, {"artifact": art} if art else pv.why(claim)
            if len(p) == 3 and m == "GET" and p[2] == "artifacts":
                from rad.control.observer import Observer
                reg = Observer(ctl.store.dir(obj.id)).artifacts()
                rows = sorted(reg.values(), key=lambda a: (-a.get("version", 0), a.get("at", 0)))
                return 200, {"objective_id": obj.id, "count": len(rows), "artifacts": rows}
            if len(p) == 3 and m == "GET" and p[2] == "artifact-content":
                return artifact_content(self.home, ctl, obj, q.get("ref", ""))
            if len(p) == 3 and m == "GET" and p[2] == "plan":
                return 200, plan_payload(ctl, obj)
            if len(p) == 3 and m == "GET" and p[2] == "recovery":
                return 200, recovery_payload(ctl, obj)
            if len(p) == 3 and m == "GET" and p[2] == "observations":
                return 200, observations_payload(ctl, obj, q)
            if len(p) == 3 and m == "GET" and p[2] == "live":
                return 200, live_payload(ctl, obj, q)
            raise ApiError(404, "unknown objective route")
        if p == ["tasks"] and m == "GET":
            store = self._ctl().store
            status = q.get("status")
            rows = []
            for o in store.list(active_only=False):
                if q.get("objective") and o.id != q["objective"] and q["objective"] != "last":
                    continue
                for t in store.load_tasks(o.id):
                    if status and str(t.get("status")) != status:
                        continue
                    rows.append({**t, "objective_id": o.id, "goal": o.goal[:80]})
            return 200, {"tasks": rows[-int(q.get("n", 200) or 200):]}
        return None
