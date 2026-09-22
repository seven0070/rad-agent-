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


if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_print(text: str, stream=None) -> None:
    target = stream or sys.stdout
    try:
        print(text, file=target)
    except UnicodeEncodeError:
        # Fallback if the underlying terminal does not support unicode characters
        ascii_text = text.replace("✓", "[OK]").replace("✗", "[X]").replace("⚠", "[!]").replace("●", "*").replace("○", "o")
        try:
            print(ascii_text, file=target)
        except Exception:
            print(text.encode("ascii", "replace").decode("ascii"), file=target)


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
    _safe_print(col.red(f"✗ {msg}"), stream=sys.stderr)


def ok(msg: str) -> None:
    _safe_print(col.green(f"✓ {msg}"))


def warn(msg: str) -> None:
    _safe_print(col.yellow(f"⚠ {msg}"))


def info(msg: str) -> None:
    _safe_print(col.dim(msg))
