"""Build the RAD backend sidecar as a self-contained executable.

Packages ``rad/sidecar.py`` (serve + health on loopback) with PyInstaller into a single
binary named for the Tauri target triple, then places it where Tauri's
``bundle.externalBin`` expects it::

    desktop/src-tauri/binaries/rad-backend-<target-triple>[.exe]

Usage (from the repository root)::

    python -m sidecar.build                      # current platform (isolated venv)
    python -m sidecar.build --triple x86_64-pc-windows-msvc   # CI: pinned per runner
    python -m sidecar.build --workdir /tmp/build
    python -m sidecar.build --no-venv           # use the current interpreter as-is

Isolation
---------
The freeze always runs inside a throwaway venv (same contract as
``scripts/build-sidecar.ps1``) unless ``--no-venv`` is passed. Host interpreters
often carry torch/matplotlib/sklearn; PyInstaller follows optional import chains
and OpenBLAS then OOMs under low RAM. A clean venv with only ``.[sidecar]``
matches CI and keeps the onefile graph stdlib + ``rad`` only.

Notes
-----
* Cross-building is not supported (PyInstaller is not a cross-compiler). CI builds on
  native runners and uploads each artifact; Tauri then selects the matching triple.
* The sidecar only ever binds loopback and only speaks the existing ``/v1/*`` API.
* ``--collect-submodules rad`` is required: PEP 562 lazy exports in
  ``rad.control`` (and similar) are invisible to static analysis.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
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

# Never pull host-only heavy stacks into the freeze (belt-and-suspenders if
# --no-venv is used on a polluted machine).
_EXCLUDES = (
    "matplotlib",
    "torch",
    "tensorflow",
    "sklearn",
    "scipy",
    "numpy",
    "pandas",
    "IPython",
    "jupyter",
    "pytest",
)


def current_triple() -> str:
    key = (platform.system(), platform.machine())
    triple = TRIPLE_MAP.get(key)
    if not triple:
        raise SystemExit(f"unsupported build platform {key}; pass --triple explicitly "
                         f"and build on a matching native runner")
    return triple


def sidecar_filename(triple: str) -> str:
    return f"{NAME}-{triple}.exe" if triple.endswith("windows-msvc") else f"{NAME}-{triple}"


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    r = subprocess.run(cmd, cwd=cwd or REPO, env=env)
    if r.returncode != 0:
        raise SystemExit(f"command failed (rc={r.returncode}): {' '.join(cmd)}")


def _ensure_venv(venv_dir: Path) -> Path:
    venv_python = _venv_python(venv_dir)
    if venv_python.exists():
        probe = subprocess.run(
            [str(venv_python), "-c", "import PyInstaller, rad"],
            cwd=REPO,
            capture_output=True,
        )
        if probe.returncode == 0:
            print(f"[sidecar] reusing venv {venv_dir}")
            return venv_python
        print("[sidecar] venv incomplete; recreating")
        shutil.rmtree(venv_dir, ignore_errors=True)

    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"[sidecar] creating venv {venv_dir}")
    _run([sys.executable, "-m", "venv", str(venv_dir)])
    _run([str(venv_python), "-m", "pip", "install", "-q", "-U", "pip"])
    _run([str(venv_python), "-m", "pip", "install", "-q", "-e", f"{REPO}[sidecar]"])
    return venv_python


def _freeze_env() -> dict:
    env = os.environ.copy()
    # Keep optional native libs from thrashing when a polluted host is used.
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("MPLBACKEND", "Agg")
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def build(triple: str, workdir: Path, verbose: bool = True,
          isolated: bool = True) -> Path:
    """Run PyInstaller and return the path of the produced binary."""
    workdir.mkdir(parents=True, exist_ok=True)

    if isolated:
        python = str(_ensure_venv(workdir / "venv"))
    else:
        python = sys.executable
        print(f"[sidecar] --no-venv: using {python}")

    cmd = [
        python, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name", sidecar_filename(triple),
        "--distpath", str(workdir / "dist"),
        "--workpath", str(workdir / "work"),
        "--specpath", str(workdir / "spec"),
        "--paths", str(REPO),          # so `rad` resolves from this checkout
        "--collect-submodules", "rad",  # PEP 562 lazy exports
        "--collect-all", "rad",
    ]
    for mod in _EXCLUDES:
        cmd.extend(("--exclude-module", mod))
    if not verbose:
        cmd.insert(1, "-s")
    cmd.append(str(REPO / "sidecar" / "entry.py"))

    t0 = time.time()
    r = subprocess.run(cmd, cwd=REPO, env=_freeze_env())
    if r.returncode != 0:
        raise SystemExit(f"pyinstaller failed (rc={r.returncode}) for {triple}")
    out = workdir / "dist" / sidecar_filename(triple)
    if not out.exists():
        raise SystemExit(f"expected sidecar binary missing: {out}")
    size = out.stat().st_size
    if size < 1024:
        raise SystemExit(f"sidecar binary is a stub ({size} bytes): {out}")
    print(f"[sidecar] built {out.name} ({size} bytes) in {time.time() - t0:.0f}s")
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
    p.add_argument("--no-venv", action="store_true",
                   help="freeze with the current interpreter (CI-clean hosts only)")
    p.add_argument("--verbose", action="store_true", help="PyInstaller console log")
    args = p.parse_args(argv)

    triple = args.triple or current_triple()
    workdir = Path(args.workdir)
    binary = build(triple, workdir, verbose=args.verbose, isolated=not args.no_venv)
    placed = place(binary, triple, Path(args.dest))
    if not args.no_smoke:
        smoke(placed, triple)
    print(f"[sidecar] done: {placed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
