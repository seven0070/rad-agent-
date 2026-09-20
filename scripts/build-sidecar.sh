#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# build-sidecar.sh — builds the `rad` CLI as a PyInstaller onefile executable
# and installs it where Tauri's externalBin (`binaries/rad` in
# desktop/src-tauri/tauri.conf.json) expects it:
#
#   desktop/src-tauri/binaries/rad-<target-triple>
#
# Config note (Tauri integration contract):
#   The PyInstaller onefile console app IS the rad CLI itself. Tauri invokes
#   the sidecar directly by path -- it must NOT be called with `-m`/`--module`.
#
# Usage:
#   scripts/build-sidecar.sh [TARGET_TRIPLE]
#
# TARGET_TRIPLE is one of: darwin-arm64, darwin-x64, linux-x64, linux-arm64.
# When omitted it is inferred from the host (`uname`).
#
# Requirements: python3 (3.10+), pip, network access to PyPI.
# Exit code is non-zero on any failure (`set -euo pipefail`).
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BIN_DIR="$REPO_ROOT/desktop/src-tauri/binaries"

map_triple() {
  case "${1:-}" in
    darwin-arm64) echo "rad-aarch64-apple-darwin" ;;
    darwin-x64)   echo "rad-x86_64-apple-darwin" ;;
    linux-x64)    echo "rad-x86_64-unknown-linux-gnu" ;;
    linux-arm64)  echo "rad-aarch64-unknown-linux-gnu" ;;
    *)
      if [ -n "${1:-}" ]; then
        echo "error: unknown target triple '$1' (expected darwin-arm64|darwin-x64|linux-x64|linux-arm64)" >&2
        exit 2
      fi
      # Infer from the host when no explicit triple was given.
      case "$(uname -s)-$(uname -m)" in
        Darwin-arm64)  echo "rad-aarch64-apple-darwin" ;;
        Darwin-x86_64) echo "rad-x86_64-apple-darwin" ;;
        Linux-x86_64)  echo "rad-x86_64-unknown-linux-gnu" ;;
        Linux-aarch64) echo "rad-aarch64-unknown-linux-gnu" ;;
        *)
          echo "error: cannot infer target triple from host '$(uname -s) $(uname -m)'; pass an explicit TARGET_TRIPLE" >&2
          exit 2
          ;;
      esac
      ;;
  esac
}

OUT_NAME="$(map_triple "${1:-}")"
OUT_PATH="$BIN_DIR/$OUT_NAME"

echo "[sidecar] Repo root: $REPO_ROOT"
echo "[sidecar] Target:    $OUT_PATH"

# --- 1. Verify Python 3.10+ ---------------------------------------------------
command -v python3 >/dev/null 2>&1 || { echo "error: python3 not found on PATH" >&2; exit 1; }
PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
MAJOR="${PY_VERSION%.*}"; MINOR="${PY_VERSION#*.}"
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
  echo "error: Python 3.10+ required, found $PY_VERSION" >&2
  exit 1
fi
echo "[sidecar] Python $PY_VERSION via python3"

# --- 2. Clean venv + build under a temp dir ------------------------------------
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/rad-sidecar.XXXXXX")"
VENV_DIR="$TMP_ROOT/venv"
DIST_DIR="$TMP_ROOT/dist"
trap 'rm -rf "$TMP_ROOT"' EXIT

VENV_PYTHON="$VENV_DIR/bin/python"

echo "[sidecar] Creating clean venv at $TMP_ROOT"
python3 -m venv "$VENV_DIR"

# Install editable package with dev extras from the repo root, then PyInstaller
# into the isolated venv. PyInstaller is deliberately not part of the runtime/
# dev dependency set (rad stays dependency-free).
(
  cd "$REPO_ROOT"
  echo "[sidecar] pip install (venv): -U pip, -e '.[dev]', pyinstaller"
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -e '.[dev]'
  "$VENV_PYTHON" -m pip install pyinstaller
)

echo "[sidecar] PyInstaller onefile build (console app = the rad CLI)"
"$VENV_PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name rad \
  --collect-all rad \
  --collect-submodules rad \
  --distpath "$DIST_DIR" \
  --specpath "$TMP_ROOT" \
  "$REPO_ROOT/rad/__main__.py"

[ -f "$DIST_DIR/rad" ] || { echo "error: PyInstaller output not found: $DIST_DIR/rad" >&2; exit 1; }

# --- 3. Install into the Tauri externalBin directory ----------------------------
mkdir -p "$BIN_DIR"
cp "$DIST_DIR/rad" "$OUT_PATH"
chmod +x "$OUT_PATH"

SIZE_BYTES="$(stat -c %s "$OUT_PATH" 2>/dev/null || stat -f %z "$OUT_PATH")"
SIZE_MB="$(awk "BEGIN { printf \"%.2f\", $SIZE_BYTES / 1048576 }")"
echo "[sidecar] OK: $OUT_PATH ($SIZE_MB MB)"
echo "[sidecar] Smoke: $OUT_PATH"
echo "[sidecar] Tauri calls the sidecar directly (no -m / --module)."