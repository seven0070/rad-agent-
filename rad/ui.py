"""Tiny terminal UI helpers. No dependencies."""
from __future__ import annotations

import sys

try:
    import tty  # noqa: F401  (platform probe only)
except Exception:  # pragma: no cover
    tty = None


def _tty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


class C:
    """ANSI colors, auto-disabled when not a TTY or NO_COLOR is set."""

    def __init__(self) -> None:
        import os

        self.on = _tty() and "NO_COLOR" not in os.environ and os.environ.get("TERM", "xterm") != "dumb"

    def _wrap(self, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if self.on else s

    def bold(self, s: str) -> str:
        return self._wrap("1", s)

    def dim(self, s: str) -> str:
        return self._wrap("2", s)

    def red(self, s: str) -> str:
        return self._wrap("31", s)

    def green(self, s: str) -> str:
        return self._wrap("32", s)

    def yellow(self, s: str) -> str:
        return self._wrap("33", s)

    def blue(self, s: str) -> str:
        return self._wrap("34", s)

    def magenta(self, s: str) -> str:
        return self._wrap("35", s)

    def cyan(self, s: str) -> str:
        return self._wrap("36", s)


col = C()

BANNER = r"""
      _    ____  _        _
  __ / \  |  _ \/ |      / \
 / _` __ \| |_) | | /\/\ / _ \
 \__,_||_|____/|_|/__/__\_/ \_\
"""


def print_banner(version: str) -> None:
    print(col.cyan(BANNER))
    print(col.dim(f"  rad v{version} — open door, free first, self-evolving"))


def ask(prompt: str, default: str = "n") -> bool:
    d = "Y/n" if default.lower() == "y" else "y/N"
    try:
        ans = input(f"{prompt} [{d}] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not ans:
        return default.lower() == "y"
    return ans in ("y", "yes")


def fail(msg: str) -> None:
    print(col.red(f"✗ {msg}"), file=sys.stderr)


def ok(msg: str) -> None:
    print(col.green(f"✓ {msg}"))


def warn(msg: str) -> None:
    print(col.yellow(f"⚠ {msg}"))


def info(msg: str) -> None:
    print(col.dim(msg))
