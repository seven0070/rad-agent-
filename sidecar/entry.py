"""PyInstaller entry point for the packaged RAD backend sidecar.

Kept separate from rad/sidecar.py so the frozen main script is a single thin file and
PyInstaller collects the whole `rad` package through it.
"""
import sys

from rad.sidecar import main

if __name__ == "__main__":
    sys.exit(main())
