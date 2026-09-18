"""Storage layer — schema version, migrations, integrity, backups.

Everything RAD persists lives under `~/.rad` as JSON / JSONL / Markdown. This module gives that
tree an explicit **schema version** (`~/.rad/schema.json`), a list of ordered **migrations**
that run once and are recorded, an **integrity scan** that finds corrupt or half-written files
(reporting, never silently deleting), and **snapshot/restore** of the state that matters.

Design rules
* Migrations are idempotent and forward-only; each is recorded with a timestamp and a summary.
* A corrupt file is quarantined (renamed `*.corrupt-<ts>`) only when `repair=True`; the default
  is report-only. Nothing is ever deleted.
* Snapshots are plain tar.gz files under `~/.rad/backups/` (keys are *excluded* by default).
"""
from __future__ import annotations

import json
import os
import shutil
import tarfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from rad.home import DEFAULTS, RadHome, _read_json, _write_json

SCHEMA_VERSION = 3

# ---------------------------------------------------------------- config schema

@dataclass
class ConfigIssue:
    key: str
    problem: str
    value: Any
    fix: Optional[Any] = None       # value the doctor would set with --fix


CONFIG_TYPES: Dict[str, Tuple[type, ...]] = {
    "workspace": (str, type(None)), "free_lock": (bool,), "auto": (bool,), "force_provider": (str, type(None)),
    "model": (str, type(None)), "edge0_url": (str,), "edge0_tier": (str,), "ollama_url": (str,), "lmstudio_url": (str,),
    "vision_order": (list, type(None)), "tts": (str,), "stt": (str,), "max_tool_rounds": (int,),
    "max_context_chars": (int,), "memory_k": (int,), "sleep_threshold_hours": (int, float), "drive_folder": (str,),
    "watch_every_min": (int, float), "custom_providers": (list,), "allow_outside_workspace": (bool,),
    "plan_infer_done": (bool,), "objective_parallel": (int,), "accept_unverified_done": (bool,),
    "evolution_require_approval": (bool,), "evolution_suite": (str,), "allow_api_fix": (bool,), "api_port": (int,),
    "allow_localhost_web": (bool,), "tool_router": (str,),
}
CONFIG_RANGES: Dict[str, Tuple[Any, Any]] = {
    "max_tool_rounds": (1, 50), "max_context_chars": (2000, 400000), "memory_k": (0, 50),
    "objective_parallel": (1, 8), "api_port": (1024, 65535), "sleep_threshold_hours": (0, 24 * 30), "watch_every_min": (1, 24 * 60),
}
CONFIG_ENUMS: Dict[str, set] = {
    "edge0_tier": {"10b", "35b"}, "tts": {"auto", "piper", "openai", "off"}, "stt": {"auto", "whisper", "openai", "off"},
    "evolution_suite": {"smoke", "long", "adversarial", "all"},
    "tool_router": {"existing", "needle"},
}


def validate_config(cfg: Dict[str, Any]) -> List[ConfigIssue]:
    issues: List[ConfigIssue] = []
    for k, v in cfg.items():
        if k not in DEFAULTS:
            issues.append(ConfigIssue(k, "unknown key (ignored by RAD)", v, fix="__remove__"))
            continue
        types = CONFIG_TYPES.get(k)
        # a key without a declared type contract is accepted as-is; `types` must never be None here
        # (iterating None used to crash `rad doctor` on any newly added boolean setting)
        if types is not None and (not isinstance(v, types)
                                  or (isinstance(v, bool) and bool not in types)):
            issues.append(ConfigIssue(k, f"expected {'/'.join(t.__name__ for t in types)}", v, fix=DEFAULTS[k]))
            continue
        if k in CONFIG_RANGES and v is not None:
            lo, hi = CONFIG_RANGES[k]
            if not (lo <= v <= hi):
                issues.append(ConfigIssue(k, f"out of range [{lo}, {hi}]", v, fix=max(lo, min(hi, v))))
        if k in CONFIG_ENUMS and v not in CONFIG_ENUMS[k]:
            issues.append(ConfigIssue(k, f"must be one of {sorted(CONFIG_ENUMS[k])}", v, fix=DEFAULTS[k]))
        if k == "workspace" and v:
            p = Path(v).expanduser()
            if not p.exists():
                issues.append(ConfigIssue(k, "directory does not exist", v))
            elif not p.is_dir():
                issues.append(ConfigIssue(k, "not a directory", v))
    for k in ("edge0_url", "ollama_url", "lmstudio_url"):
        v = cfg.get(k)
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            issues.append(ConfigIssue(k, "must be an http(s) URL", v, fix=DEFAULTS[k]))
    return issues


# ---------------------------------------------------------------- migrations

@dataclass
class Migration:
    version: int
    name: str
    apply: Callable[[RadHome], Dict[str, Any]]      # returns a summary dict


def _m1_memory_frontmatter(home: RadHome) -> Dict[str, Any]:
    """v1: memory files gain origin/confidence/verification front-matter (Memory 2.0).
    Files without it are rewritten with defaults so every entry is explicit on disk."""
    from rad.memory import Memory
    mem = Memory(home)
    n = 0
    for e in mem.scan():
        raw = e.path.read_text(encoding="utf-8") if e.path and e.path.exists() else ""
        head = raw.split("---")[1] if raw.startswith("---") and raw.count("---") >= 2 else ""
        if "origin:" not in head:
            e.path.write_text(e.to_file(), encoding="utf-8")
            n += 1
    mem._invalidate()
    return {"memories_rewritten": n}


def _m2_dna_history(home: RadHome) -> Dict[str, Any]:
    """v2: every DNA generation file carries a `history` list (evolution provenance)."""
    n = 0
    for p in home.dna_dir.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "history" not in d:
            d["history"] = [{"gen": d.get("generation", 0), "note": "pre-migration", "at": p.stat().st_mtime}]
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            n += 1
    return {"dna_files_updated": n}


def _m3_world_provenance(home: RadHome) -> Dict[str, Any]:
    """v3: world-model entities/relations carry origin/confidence/status."""
    p = home.root / "world" / "graph.json"
    if not p.exists():
        return {"skipped": "no world graph"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"skipped": "world graph unreadable (see integrity)"}
    n = 0
    for coll in ("entities", "relations"):
        items = d.get(coll, {})
        it = items.values() if isinstance(items, dict) else items
        for x in it:
            if isinstance(x, dict) and "origin" not in x:
                x.setdefault("origin", "INFERRED"); x.setdefault("confidence", 0.5); x.setdefault("status", "active")
                n += 1
    if n:
        _write_json(p, d)
    return {"world_items_updated": n}


MIGRATIONS: List[Migration] = [
    Migration(1, "memory front-matter (origin/confidence/verification)", _m1_memory_frontmatter),
    Migration(2, "dna generation history", _m2_dna_history),
    Migration(3, "world model provenance", _m3_world_provenance),
]
assert [m.version for m in MIGRATIONS] == list(range(1, SCHEMA_VERSION + 1))


class Storage:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.schema_path = home.root / "schema.json"

    # ---- schema
    def schema(self) -> Dict[str, Any]:
        return _read_json(self.schema_path, {"version": 0, "applied": []})

    def version(self) -> int:
        return int(self.schema().get("version", 0))

    def is_fresh_home(self) -> bool:
        """A home with no state yet needs no migrations — stamp it at the current version."""
        state = [self.home.root / "memory" / "long", self.home.root / "objectives", self.home.root / "world"]
        if any(p.exists() and any(q.is_file() for q in p.rglob("*")) for p in state):
            return False
        gens = list(self.home.dna_dir.glob("gen*.json"))
        if len(gens) > 1:
            return False
        cur = _read_json(self.home.dna_dir / "current.json", {})
        return not cur or (cur.get("generation", 0) == 0 and not cur.get("lessons") and "history" in cur)

    def pending(self) -> List[Migration]:
        if self.version() == 0 and self.is_fresh_home():
            self._stamp_fresh()
        return [m for m in MIGRATIONS if m.version > self.version()]

    def _stamp_fresh(self) -> None:
        _write_json(self.schema_path, {"version": SCHEMA_VERSION,
                                       "applied": [{"version": SCHEMA_VERSION, "name": "fresh home", "at": time.time()}]})

    def migrate(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        sch = self.schema()
        if sch.get("version", 0) == 0 and self.is_fresh_home() and not dry_run:
            self._stamp_fresh()
            return [{"version": SCHEMA_VERSION, "name": "fresh home (stamped, nothing to migrate)"}]
        done = []
        for m in [m for m in MIGRATIONS if m.version > self.version()]:
            if dry_run:
                done.append({"version": m.version, "name": m.name, "dry_run": True})
                continue
            self.snapshot(label=f"pre-migration-v{m.version}")
            summary = m.apply(self.home)
            sch["version"] = m.version
            sch.setdefault("applied", []).append({"version": m.version, "name": m.name, "at": time.time(), "summary": summary})
            _write_json(self.schema_path, sch)
            done.append({"version": m.version, "name": m.name, "summary": summary})
        return done

    # ---- integrity
    def integrity(self, repair: bool = False) -> List[Dict[str, Any]]:
        """Find unreadable JSON, leftover .tmp files, orphan objective dirs, unreadable memory files."""
        root = self.home.root
        findings: List[Dict[str, Any]] = []

        def bad(path: Path, problem: str, fixable: bool = True):
            f = {"path": str(path.relative_to(root)), "problem": problem, "fixable": fixable, "repaired": False}
            if repair and fixable:
                q = path.with_name(path.name + f".corrupt-{int(time.time())}")
                path.rename(q); f["repaired"] = True; f["quarantined_as"] = q.name
            findings.append(f)

        for p in root.rglob("*.json"):
            if any(part in ("backups", "models", "downloads") for part in p.relative_to(root).parts):
                continue
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                bad(p, f"invalid JSON: {str(e)[:60]}")
        for p in root.rglob("*.tmp"):
            bad(p, "leftover temp file from interrupted write")
        for p in root.rglob("*.jsonl"):
            if "backups" in p.parts:
                continue
            broken = 0
            try:
                for ln in p.read_text(encoding="utf-8").splitlines():
                    if ln.strip():
                        try:
                            json.loads(ln)
                        except Exception:
                            broken += 1
            except Exception:
                broken = -1
            if broken:
                findings.append({"path": str(p.relative_to(root)), "problem": f"{broken} unparsable line(s)", "fixable": False, "repaired": False})
        objs = root / "objectives"
        if objs.exists():
            for d in objs.iterdir():
                if d.is_dir() and not (d / "objective.json").exists():
                    findings.append({"path": str(d.relative_to(root)), "problem": "objective dir without objective.json", "fixable": False, "repaired": False})
        for p in (root / "memory" / "long").rglob("*.md"):
            txt = p.read_text(encoding="utf-8", errors="replace")
            if not txt.startswith("---"):
                findings.append({"path": str(p.relative_to(root)), "problem": "memory file without front-matter", "fixable": False, "repaired": False})
        for p in (root / "keys",):
            if p.exists():
                mode = oct(p.stat().st_mode & 0o777)
                if p.stat().st_mode & 0o077:
                    f = {"path": "keys/", "problem": f"permissions {mode} too open", "fixable": True, "repaired": False}
                    if repair:
                        os.chmod(p, 0o700); f["repaired"] = True
                    findings.append(f)
        return findings

    # ---- backups
    def snapshot(self, label: str = "", include_keys: bool = False) -> Path:
        bdir = self.home.root / "backups"
        bdir.mkdir(exist_ok=True)
        name = f"{time.strftime('%Y%m%d-%H%M%S')}{('_' + label) if label else ''}.tar.gz"
        out = bdir / name
        skip = {"backups", "models", "downloads", "logs", "lab"} | (set() if include_keys else {"keys", ".vault.key"})
        with tarfile.open(out, "w:gz") as tar:
            for child in sorted(self.home.root.iterdir()):
                if child.name in skip:
                    continue
                tar.add(child, arcname=child.name)
        os.chmod(out, 0o600)
        # keep the newest 10
        for old in sorted(bdir.glob("*.tar.gz"))[:-10]:
            old.unlink(missing_ok=True)
        return out

    def snapshots(self) -> List[Path]:
        bdir = self.home.root / "backups"
        return sorted(bdir.glob("*.tar.gz")) if bdir.exists() else []

    def restore(self, archive: Path) -> List[str]:
        """Restore a snapshot over the current home (keys untouched). A safety snapshot of the
        current state is taken first. Returns restored top-level entries."""
        self.snapshot(label="pre-restore")
        restored = []
        with tarfile.open(archive, "r:gz") as tar:
            members = [m for m in tar.getmembers() if not m.name.startswith(("/", "..")) and ".." not in m.name.split("/")]
            tops = {m.name.split("/")[0] for m in members}
            for t in tops:
                target = self.home.root / t
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
            try:
                tar.extractall(self.home.root, members=members, filter="data")
            except TypeError:
                tar.extractall(self.home.root, members=members)
            restored = sorted(tops)
        self.home.cfg = self.home.load_config()
        return restored

    # ---- sizes (for doctor)
    def usage(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for child in sorted(self.home.root.iterdir()):
            if child.is_dir():
                n, size = 0, 0
                for p in child.rglob("*"):
                    if p.is_file():
                        n += 1; size += p.stat().st_size
                out[child.name] = {"files": n, "bytes": size}
        return out
