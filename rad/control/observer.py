"""Observer — every action produces an Observation; artifacts are first-class.

Observations are what the Verifier and Recovery engine reason over. They are
persisted per objective so a crashed run can be inspected and replayed.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import _write_json


@dataclass
class Observation:
    id: str
    objective_id: str
    task_id: str
    action_id: str
    tool: str
    args: Dict[str, Any]
    status: str                 # success | error | blocked | declined
    output: str
    duration_ms: int
    at: float = field(default_factory=time.time)
    artifacts: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def new(cls, **kw: Any) -> "Observation":
        return cls(id="obs_" + uuid.uuid4().hex[:8], **kw)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Artifact:
    id: str
    objective_id: str
    task_id: str
    type: str                   # file | url | text
    location: str
    creator: str                # tool name
    sha256: str = ""
    size: int = 0
    version: int = 1
    parent: Optional[str] = None
    at: float = field(default_factory=time.time)
    verification: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def classify_output(tool: str, out: str) -> str:
    low = (out or "").lower()
    if low.startswith("blocked by safety policy"):
        return "blocked"
    if low.startswith("user declined"):
        return "declined"
    if low.startswith(("tool error", "fetch failed", "not found:", "unknown tool", "[see failed",
                       "not a directory", "[timeout")):
        return "error"
    if tool == "run_shell" and re.search(r"\[exit=[1-9]\d*\]\s*$", out or ""):
        return "error"
    return "success"


class Observer:
    def __init__(self, objective_dir: Path) -> None:
        self.dir = objective_dir / "observations"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_path = objective_dir / "artifacts.json"
        self._lock = threading.RLock()

    # ------------------------------------------------------------ observe
    @staticmethod
    def snapshot(workspace: Path, limit: int = 5000) -> Dict[str, float]:
        """{relpath: mtime} for files in the workspace (cheap; skips VCS/deps dirs)."""
        out: Dict[str, float] = {}
        skip = {".git", "node_modules", ".venv", "__pycache__", ".rad"}
        try:
            for p in workspace.rglob("*"):
                if any(part in skip for part in p.parts):
                    continue
                if p.is_file():
                    out[str(p.relative_to(workspace))] = p.stat().st_mtime
                    if len(out) >= limit:
                        break
        except Exception:
            pass
        return out

    def record(self, objective_id: str, task_id: str, action_id: str, tool: str,
               args: Dict[str, Any], output: str, duration_ms: int,
               workspace: Path, before: Optional[Dict[str, float]] = None) -> Observation:
        status = classify_output(tool, output)
        obs = Observation.new(objective_id=objective_id, task_id=task_id, action_id=action_id,
                              tool=tool, args=args, status=status, output=(output or "")[:20000],
                              duration_ms=duration_ms)
        # artifacts: anything write_file produced, or files the shell reported creating
        if tool == "write_file" and status == "success":
            p = Path(str(args.get("path", "")))
            if not p.is_absolute():
                p = workspace / p
            art = self.register_artifact(objective_id, task_id, "file", str(p), tool)
            if art:
                obs.artifacts.append(art.id)
        # shell: register files that appeared or changed during the command
        if tool == "run_shell" and before is not None and status == "success":
            after = self.snapshot(workspace)
            changed = [rel for rel, mt in after.items() if before.get(rel) != mt][:20]
            for rel in changed:
                art = self.register_artifact(objective_id, task_id, "file", str(workspace / rel), tool)
                if art:
                    obs.artifacts.append(art.id)
        # evidence: web fetches are evidence sources
        if tool in ("fetch_page", "web_search") and status == "success":
            obs.evidence.append({"source": args.get("url") or args.get("query", ""),
                                 "tool": tool, "at": obs.at, "trusted": False})
        _write_json(self.dir / f"{obs.id}.json", obs.to_dict())
        return obs

    def load(self, obs_id: str) -> Optional[Observation]:
        p = self.dir / f"{obs_id}.json"
        try:
            return Observation(**json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            return None

    def for_task(self, task_id: str) -> List[Observation]:
        out = []
        for p in sorted(self.dir.glob("obs_*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if d.get("task_id") == task_id:
                out.append(Observation(**d))
        out.sort(key=lambda o: o.at)
        return out

    # ------------------------------------------------------------ artifacts
    def artifacts(self) -> Dict[str, Dict[str, Any]]:
        try:
            return json.loads(self.artifacts_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def register_artifact(self, objective_id: str, task_id: str, type_: str, location: str,
                          creator: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Artifact]:
        with self._lock:
            return self._register_artifact(objective_id, task_id, type_, location, creator, metadata)

    def _register_artifact(self, objective_id, task_id, type_, location, creator, metadata) -> Optional[Artifact]:
        reg = self.artifacts()
        sha, size = "", 0
        if type_ == "file":
            p = Path(location)
            if not p.exists():
                return None
            data = p.read_bytes()
            sha, size = hashlib.sha256(data).hexdigest(), len(data)
        # lineage: same location → new version with parent link
        parent, version = None, 1
        for a in reg.values():
            if a["location"] == location:
                if a["version"] >= version:
                    parent, version = a["id"], a["version"] + 1
        art = Artifact(id="art_" + uuid.uuid4().hex[:8], objective_id=objective_id, task_id=task_id,
                       type=type_, location=location, creator=creator, sha256=sha, size=size,
                       version=version, parent=parent, metadata=metadata or {})
        reg[art.id] = art.to_dict()
        _write_json(self.artifacts_path, reg)
        return art

    def mark_verified(self, art_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            reg = self.artifacts()
            if art_id in reg:
                reg[art_id]["verification"] = result
                _write_json(self.artifacts_path, reg)
