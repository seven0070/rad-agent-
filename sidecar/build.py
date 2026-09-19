"""Build the RAD backend sidecar as a self-contained executable.

Packages ``rad/sidecar.py`` (serve + health on loopback) with PyInstaller into a single
binary named for the Tauri target triple, then places it where Tauri's
``bundle.externalBin`` expects it::

    desktop/src-tauri/binaries/rad-backend-<target-triple>[.exe]

Usage (from the repository root, after ``pip install -e .[sidecar]``)::

    python -m sidecar.build                      # current platform
    python -m sidecar.build --triple x86_64-pc-windows-msvc   # CI: pinned per runner
    python -m sidecar.build --workdir /tmp/build

Notes
-----
* Cross-building is not supported (PyInstaller is not a cross-compiler). CI builds on
  native runners and uploads each artifact; Tauri then selects the matching triple.
* The sidecar only ever binds loopback and only speaks the existing ``/v1/*`` API.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BINARIES_DIR = REPO / "desktop" / "src-tauri" / "binaries"
NAME = "rad-backend"

# Tauri target triples (what bundle.externalBin is suffixed with per platform)
TRIPLE_MAP = {
    ("Linux", "x86_64"): "x86_64-unknown-linux-gnu",
    ("Linux", "aarch64"): "aarch64-unknown-linux-gnu",
    ("Darwin", "arm64"): "aarch64-apple-darwin",
    ("Darwin", "x86_64"): "x86_64-apple-darwin",
    ("Windows", "AMD64"): "x86_64-pc-windows-msvc",
    ("Windows", "ARM64"): "aarch64-pc-windows-msvc",
}


def current_triple() -> str:
    key = (platform.system(), platform.machine())
    triple = TRIPLE_MAP.get(key)
    if not triple:
        raise SystemExit(f"unsupported build platform {key}; pass --triple explicitly "
                         f"and build on a matching native runner")
    return triple


def sidecar_filename(triple: str) -> str:
    return f"{NAME}-{triple}.exe" if triple.endswith("windows-msvc") else f"{NAME}-{triple}"


def build(triple: str, workdir: Path, verbose: bool = True) -> Path:
    """Run PyInstaller and return the path of the produced binary."""
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name", sidecar_filename(triple),
        "--distpath", str(workdir / "dist"),
        "--workpath", str(workdir / "work"),
        "--specpath", str(workdir / "spec"),
        "--paths", str(REPO),          # so `rad` resolves from this checkout
        str(REPO / "sidecar" / "entry.py"),
    ]
    if not verbose:
        cmd.insert(1, "-s")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=REPO)
    if r.returncode != 0:
        raise SystemExit(f"pyinstaller failed (rc={r.returncode}) for {triple}")
    out = workdir / "dist" / sidecar_filename(triple)
    if not out.exists():
        raise SystemExit(f"expected sidecar binary missing: {out}")
    print(f"[sidecar] built {out.name} in {time.time() - t0:.0f}s")
    return out


def place(binary: Path, triple: str, dest: Path = BINARIES_DIR) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / binary.name
    shutil.copy2(binary, target)
    if os.name != "nt":
        os.chmod(target, 0o755)
    print(f"[sidecar] placed at {target}")
    return target


def smoke(binary: Path, triple: str) -> None:
    """Sanity: the frozen binary parses --help and reports its serve/health subcommands."""
    r = subprocess.run([str(binary), "--help"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"sidecar smoke failed: {binary}\n{r.stderr[:800]}")
    for word in ("serve", "health"):
        if word not in r.stdout:
            raise SystemExit(f"sidecar smoke: missing subcommand {word!r}\n{r.stdout[:400]}")
    print(f"[sidecar] smoke OK ({triple})")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--triple", default=None, help="Tauri target triple (default: current platform)")
    p.add_argument("--workdir", default=str(REPO / "sidecar" / ".build"))
    p.add_argument("--dest", default=str(BINARIES_DIR))
    p.add_argument("--no-smoke", action="store_true", help="skip the --help smoke test")
    args = p.parse_args(argv)

    triple = args.triple or current_triple()
    workdir = Path(args.workdir)
    binary = build(triple, workdir)
    placed = place(binary, triple, Path(args.dest))
    if not args.no_smoke:
        smoke(placed, triple)
    print(f"[sidecar] done: {placed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
