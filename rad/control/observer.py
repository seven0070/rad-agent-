"""Observer — every action produces an Observation; artifacts are first-class.

Observations are what the Verifier and Recovery engine reason over. They are
persisted per objective so a crashed run can be inspected and replayed.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
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
    error: str = ""                       # the failure text, when status != success
    env: Dict[str, Any] = field(default_factory=dict)   # where it ran: workspace, python, platform
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
    provenance: Dict[str, Any] = field(default_factory=dict)   # created_by → task → objective, lineage

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
               workspace: Path, before: Optional[Dict[str, float]] = None,
               evidence: Optional[List[Dict[str, Any]]] = None) -> Observation:
        status = classify_output(tool, output)
        obs = Observation.new(objective_id=objective_id, task_id=task_id, action_id=action_id,
                              tool=tool, args=args, status=status, output=(output or "")[:20000],
                              duration_ms=duration_ms, evidence=list(evidence or []),
                              error=((output or "")[:2000] if status != "success" else ""),
                              env={"workspace": str(workspace), "python": platform.python_version(),
                                   "platform": sys.platform, "cwd": os.getcwd()[:300]})
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
        # keep the bytes of the version we are superseding so a broken edit can be rolled back
        if parent:
            self._backup_version(reg[parent], version)
        art = Artifact(id="art_" + uuid.uuid4().hex[:8], objective_id=objective_id, task_id=task_id,
                       type=type_, location=location, creator=creator, sha256=sha, size=size,
                       version=version, parent=parent, metadata=metadata or {},
                       provenance={"created_by": creator, "tool": creator, "task_id": task_id,
                                   "objective_id": objective_id, "version": version,
                                   "parent": parent, "at": time.time()})
        reg[art.id] = art.to_dict()
        _write_json(self.artifacts_path, reg)
        return art

    # ------------------------------------------------------------ versions / rollback
    def versions_dir(self) -> Path:
        d = self.dir.parent / "artifact_versions"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _backup_version(self, art: Dict[str, Any], next_version: int) -> None:
        """Copy the current file to artifact_versions/<artifact>_v<version> before overwriting."""
        try:
            loc = Path(art.get("location", ""))
            if not loc.exists() or not loc.is_file():
                return
            dest = self.versions_dir() / f"{art['id']}_v{art.get('version', 1)}({next_version}).bak"
            if not dest.exists():
                import shutil
                shutil.copy2(loc, dest)
        except Exception:
            pass

    def version_files(self, art_id: str) -> List[Path]:
        return sorted(self.versions_dir().glob(f"{art_id}_v*.bak"))

    def rollback_artifact(self, art_id: str) -> bool:
        """Restore the newest backup of an artifact over the current file."""
        import shutil
        reg = self.artifacts()
        art = reg.get(art_id)
        if not art:
            return False
        backups = self.version_files(art_id)
        if not backups:
            return False
        try:
            shutil.copy2(backups[-1], Path(art["location"]))
        except Exception:
            return False
        art["verification"] = {"ok": True, "kind": "rolled_back", "detail": f"restored {backups[-1].name}"}
        art["version"] = int(art.get("version", 1))
        reg[art_id] = art
        _write_json(self.artifacts_path, reg)
        return True

    # ------------------------------------------------------------ listing
    def observations(self, status: Optional[str] = None) -> List[Observation]:
        out: List[Observation] = []
        for p in sorted(self.dir.glob("obs_*.json")):
            o = self.load(p.stem)
            if o and (status is None or o.status == status):
                out.append(o)
        out.sort(key=lambda o: o.at)
        return out

    def mark_verified(self, art_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            reg = self.artifacts()
            if art_id in reg:
                reg[art_id]["verification"] = result
                _write_json(self.artifacts_path, reg)
