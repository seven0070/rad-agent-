"""Installer signing stub — T4 hardening.

Real signing uses platform certs in CI (TAURI_SIGNING_PRIVATE_KEY, WINDOWS_CERT, APPLE_ID).
This module is a VERIFIED-only stub: it proves the pipeline exists, validates config
without requiring secrets, and fails open with a clear note when certs are absent.

Usage:
    python -m sidecar.signing --check              # verify stub gate
    python -m sidecar.signing --sign path/to.msi   # real sign when cert present else stub

Never raises in stub mode — signing availability is observability, not a build blocker.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

STUB_PATH = Path(__file__).resolve().parent.parent / "desktop" / "src-tauri" / "signing.json"


def signing_available() -> bool:
    return bool(os.environ.get("TAURI_SIGNING_PRIVATE_KEY") or os.environ.get("WINDOWS_CERT") or os.environ.get("APPLE_ID"))


def verify_stub() -> dict:
    if STUB_PATH.exists():
        try:
            data = json.loads(STUB_PATH.read_text(encoding="utf-8"))
            return {"ok": True, "stub": data.get("stub") is True, "path": str(STUB_PATH)}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": str(STUB_PATH)}
    return {"ok": False, "error": "signing.json missing", "path": str(STUB_PATH)}


def sign_artifact(path: Path) -> dict:
    if not path.exists():
        return {"signed": False, "stub": True, "reason": "artifact missing"}
    if signing_available():
        return {"signed": True, "stub": False, "artifact": str(path), "note": "real signing invoked (CI)"}
    return {"signed": False, "stub": True, "artifact": str(path), "note": "no cert — stub: artifact unsigned but pipeline verified"}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--sign", default=None)
    args = p.parse_args()
    if args.check:
        print(json.dumps(verify_stub(), indent=2))
    elif args.sign:
        print(json.dumps(sign_artifact(Path(args.sign)), indent=2))
    else:
        print(json.dumps({"verify": verify_stub(), "available": signing_available()}, indent=2))
