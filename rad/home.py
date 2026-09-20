"""RadHome — all Rad state lives in one folder (~/.rad by default).

Everything is a human-readable file you can open, edit, move, version.
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULTS: Dict[str, Any] = {
    "workspace": None,            # dir hands operate in (default: cwd at launch)
    "free_lock": False,           # paid providers impossible
    "auto": False,                # hands act without per-command confirm
    "force_provider": None,       # pin one provider
    "model": None,                # pin a model for the pinned/primary provider
    "edge0_url": "http://127.0.0.1:8000/v1",
    "edge0_tier": "10b",          # 10b (fast) | 35b (deep)
    "ollama_url": "http://127.0.0.1:11434",
    "lmstudio_url": "http://127.0.0.1:1234/v1",
    "vision_order": None,         # override vision provider order
    "tts": "auto",                # auto|piper|openai|off
    "stt": "auto",                # auto|whisper|openai|off
    "max_tool_rounds": 8,
    "max_context_chars": 24000,
    "memory_k": 5,                # memories injected per turn
    "sleep_threshold_hours": 24,  # auto-sleep when idle this long
    "drive_folder": "RadAgent",
    "watch_every_min": 30,
    "custom_providers": [],       # open door: any OpenAI-compatible endpoint
    "allow_outside_workspace": False,  # file tools may leave the workspace (off = boundary enforced)
    "allow_localhost_web": False,      # web/browser tools may reach loopback (local dev servers only)
    "plan_infer_done": False,
    "objective_parallel": 2,      # max ready tasks run concurrently (only with --auto)
    "accept_unverified_done": True,  # tasks w/o checks may complete on a DONE: claim (recorded UNVERIFIED)
    "evolution_require_approval": False,  # gated evolution also needs `rad evolve approve <id>` before promotion
    "evolution_suite": "smoke",     # lab suite used as the promotion gate
    "allow_api_fix": False,         # let GET /v1/doctor?fix=1 apply repairs
    "api_port": 7331,
    "tool_router": "existing",      # existing | needle (optional experimental; never sovereign)
}


def _read_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(tmp, 0o600)
    except Exception:
        pass
    if os.name == "nt" and path.exists():
        import stat
        try:
            os.chmod(path, stat.S_IWRITE)
        except Exception:
            pass
    tmp.replace(path)


class RadHome:
    """Filesystem home of the agent. Test-friendly via RAD_HOME env var."""

    def __init__(self, root: Optional[str] = None) -> None:
        self.root = Path(root or os.environ.get("RAD_HOME") or (Path.home() / ".rad"))
        self._make_tree()
        self.cfg = self.load_config()

    # ---------- tree ----------
    def _make_tree(self) -> None:
        for sub in (
            "",
            "memory", "memory/short", "memory/long/episodic",
            "memory/long/semantic", "memory/long/procedural",
            "memory/archive", "dna", "skills", "downloads",
            "logs", "models", "keys", "workspace",
        ):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.root / "keys", 0o700)
        except OSError:
            pass

    @property
    def config_path(self) -> Path:
        return self.root / "rad.json"

    @property
    def cost_path(self) -> Path:
        return self.root / "cost.json"

    @property
    def jobs_path(self) -> Path:
        return self.root / "jobs.json"

    @property
    def skills_registry(self) -> Path:
        return self.root / "skills" / "registry.json"

    @property
    def vault_key_path(self) -> Path:
        return self.root / ".vault.key"

    @property
    def vault_path(self) -> Path:
        return self.root / "keys" / "vault.enc"

    @property
    def keys_env_path(self) -> Path:
        return self.root / "keys" / "keys.env"

    @property
    def notifications_path(self) -> Path:
        return self.root / "notifications.md"

    @property
    def provider_health_path(self) -> Path:
        return self.root / "provider_health.json"

    @property
    def dna_dir(self) -> Path:
        return self.root / "dna"

    @property
    def memory_dir(self) -> Path:
        return self.root / "memory"

    # ---------- config ----------
    def load_config(self) -> Dict[str, Any]:
        cfg = dict(DEFAULTS)
        cfg.update(_read_json(self.config_path, {}))
        return cfg

    def save_config(self) -> None:
        _write_json(self.config_path, self.cfg)

    def update(self, **kw: Any) -> None:
        for k, v in kw.items():
            if k in DEFAULTS:
                self.cfg[k] = v
        self.save_config()

    # ---------- key vault ----------
    def _fernet(self):
        """Fernet cipher if cryptography is installed; else None (plain + warn)."""
        try:
            from cryptography.fernet import Fernet  # type: ignore
        except ImportError:
            return None
        if not self.vault_key_path.exists():
            key = Fernet.generate_key()
            self.vault_key_path.write_bytes(key)
            os.chmod(self.vault_key_path, 0o600)
        return Fernet(self.vault_key_path.read_bytes())

    def vault_get_all(self) -> Dict[str, str]:
        if not self.vault_path.exists():
            return {}
        raw = self.vault_path.read_text(encoding="utf-8")
        f = self._fernet()
        if f is None:
            return _read_json(Path("."), {}) if False else _try_json(raw)
        try:
            return json.loads(f.decrypt(raw.encode()).decode())
        except Exception:
            return {}

    def vault_set(self, provider: str, key: str) -> None:
        data = self.vault_get_all()
        data[provider] = key
        f = self._fernet()
        payload = json.dumps(data, indent=2)
        if f is not None:
            self.vault_path.write_text(f.encrypt(payload.encode()).decode())
        else:
            # No crypto lib: store as 0600 JSON with a loud note.
            _write_json(self.vault_path, data)
        os.chmod(self.vault_path, 0o600)

    def vault_remove(self, provider: str) -> None:
        data = self.vault_get_all()
        if data.pop(provider, None) is not None:
            f = self._fernet()
            payload = json.dumps(data, indent=2)
            self.vault_path.write_text(f.encrypt(payload.encode()).decode() if f else payload)
            os.chmod(self.vault_path, 0o600)

    # ---------- cost ----------
    def cost_data(self) -> Dict[str, Any]:
        return _read_json(self.cost_path, {})

    def add_cost(self, provider: str, model: str, tin: int, tout: int, price: float) -> None:
        data = self.cost_data()
        day = time.strftime("%Y-%m-%d")
        cell = data.setdefault(day, {}).setdefault(provider, {"in": 0, "out": 0, "cost": 0.0})
        cell["in"] += tin
        cell["out"] += tout
        cell["cost"] = round(cell["cost"] + price, 6)
        _write_json(self.cost_path, data)

    # ---------- skills registry ----------
    def skills(self) -> Dict[str, Any]:
        return _read_json(self.skills_registry, {})

    def save_skills(self, data: Dict[str, Any]) -> None:
        _write_json(self.skills_registry, data)

    # ---------- generic ----------
    def rel(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def workspace(self) -> Path:
        """Where file/shell tools operate.

        An explicit `workspace` setting wins. Otherwise RAD uses `~/.rad/workspace`
        (created on demand) so a clone-and-run never writes into the repository or
        whatever directory the user happened to be in.
        """
        ws = self.cfg.get("workspace")
        if ws:
            return Path(str(ws)).expanduser()
        p = self.root / "workspace"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def log(self, name: str, text: str) -> None:
        try:
            p = self.root / "logs" / f"{name}.log"
            with open(p, "a", encoding="utf-8") as f:
                f.write(text.rstrip() + "\n")
        except Exception:
            pass


def _try_json(raw: str) -> Dict[str, str]:
    try:
        d = json.loads(raw)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def mask(key: str) -> str:
    if not key:
        return "(none)"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}…{key[-4:]}"


def new_token(n: int = 8) -> str:
    return secrets.token_hex(n)[:n]
