"""PyInstaller entry point for the packaged RAD backend sidecar.

Kept separate from rad/sidecar.py so the frozen main script is a single thin file and
PyInstaller collects the whole `rad` package through it.
"""
import sys

from rad.sidecar import main
# --- Ledger endpoints (rad.desktop_ledger data layer) ---
from rad.desktop_ledger import folded as _fold, summary as _lsum

def api_ledger():
    f = _fold()
    f["summary"] = _lsum()
    return f

if __name__ == "__main__":
    sys.exit(main())
