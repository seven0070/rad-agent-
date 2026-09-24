"""Security and validation primitives for the local HTTP API.

Pure helpers with no route/domain imports, so `rad.api`, `rad.api_routes.*` and
`rad.api_services` can all depend on this module without import cycles.

Covers: body-size cap, path-containment check, the API error type, owner-only
secret file enforcement (chmod 0600 / Windows ACE stripping) and bearer-token
persistence. The security model itself is documented in `rad.api`'s module
docstring — nothing here weakens it.
"""
from __future__ import annotations

import os
import secrets
import subprocess
from pathlib import Path
from typing import Tuple

from rad.home import RadHome

MAX_BODY = 256 * 1024


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except (ValueError, TypeError):
        return False


class ApiError(Exception):
    def __init__(self, status: int, msg: str) -> None:
        super().__init__(msg)
        self.status = status


def restrict_secret(path: Path) -> None:
    """Owner-only secret file. POSIX chmod 0600. Windows stat cannot show 0600
    (chmod 0o600 still reports 0o666), so strip inherited ACEs and grant the
    current user R,W only."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    if os.name != "nt":
        return
    user = os.environ.get("USERNAME") or ""
    if not user:
        return
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:(R,W)"],
            capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def secret_is_private(path: Path) -> Tuple[bool, str]:
    mode = oct(path.stat().st_mode & 0o777)
    if os.name != "nt":
        return mode == "0o600", mode
    user = (os.environ.get("USERNAME") or "").lower()
    try:
        proc = subprocess.run(
            ["icacls", str(path)], capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, mode
    aces = []
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line or line.lower().startswith("successfully processed"):
            continue
        if "(" in line and ":" in line:
            aces.append(line)
    blob = "\n".join(aces).lower()
    broad = ("everyone", "builtin\\users", "authenticated users",
             "builtin\\administrators", "nt authority\\system")
    if not aces or any(b in blob for b in broad) or (user and user not in blob):
        return False, mode
    return True, mode


def token_for(home: RadHome, rotate: bool = False) -> str:
    p = home.root / "api.token"
    if p.exists() and not rotate:
        restrict_secret(p)
        return p.read_text(encoding="utf-8").strip()
    tok = secrets.token_urlsafe(32)
    p.write_text(tok, encoding="utf-8")
    restrict_secret(p)
    return tok
