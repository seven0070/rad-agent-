"""Verified coding loop helpers — machine checks, not model DONE: claims.

When an objective is coding/verification-shaped, RAD infers disk checks
(json_valid, pytest/test exit 0) and treats failed content/tests as a
repairable validation failure. A `DONE:` line is never an artifact path
or a substitute for the file.

Package-layout goals (e.g. files under `text_analyzer/`) get check paths
joined to that directory so root-only checks cannot thrash a package write
(RW-069 / Gen3 theme 1). Fallback *tasks* stay check-less (F-17).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from rad.control.tasks import Check

CODING_MARKERS_RE = re.compile(
    r"\b(code|coding|implement|function|bug|refactor|script|python|pytest|"
    r"unittest|word_counter|analyzer|verify)\b|\.py\b|test_\w+\.py|"
    r"\brun the tests?\b|\bwrite the tests?\b|\bfailing tests?\b",
    re.I,
)
JSON_PATH_RE = re.compile(r"\b([\w./-]+\.json)\b", re.I)
TEST_FILE_RE = re.compile(r"\b((?:[\w.-]+/)*test_\w+\.py)\b", re.I)
DONE_PREFIX_RE = re.compile(r"^\s*DONE\s*:", re.I)
# "under pkg/" (slash required so "under the …" is not a package name)
_PKG_UNDER_RE = re.compile(
    r"\bunder\s+(?:the\s+)?(?:directory\s+|dir\s+|package\s+|folder\s+)?([A-Za-z_][\w.-]*)/",
    re.I,
)
_PKG_BRACE_RE = re.compile(r"\b([A-Za-z_][\w.-]*)/\{")
_PKG_FILE_RE = re.compile(r"\b([A-Za-z_][\w.-]*)/(?:[\w.-]+/)*[\w.-]+\.\w+")
_SKIP_PKG_DIRS = frozenset({"tests", "test", "docs", "doc"})
_BARE_TEST_IN_CMD_RE = re.compile(r"(?<![/\w.-])(test_\w+\.py)\b", re.I)

BROKEN_ARTIFACT_KINDS = frozenset({
    "json_valid", "json_field", "json_min_len", "shell_ok", "shell_output",
})


def is_coding_or_verify_goal(text: str) -> bool:
    return bool(CODING_MARKERS_RE.search(text or ""))


def is_done_pollution_path(path: str) -> bool:
    """True when a tool path is a model DONE: claim, not a real file name."""
    raw = str(path or "").strip()
    if not raw:
        return False
    name = Path(raw).name
    return bool(DONE_PREFIX_RE.match(raw) or DONE_PREFIX_RE.match(name))


def is_done_pollution_content(text: str) -> bool:
    """True when the file body is only a DONE: claim (RW-062 pollution)."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines or len(lines) > 2:
        return False
    return all(DONE_PREFIX_RE.match(ln) or ln.lower() in ("done", "done.") for ln in lines)


def looks_like_broken_artifact(failed_checks: Iterable[Dict[str, Any]]) -> bool:
    """Artifacts were produced but json/tests failed — not a missing-file lie."""
    return any(r.get("kind") in BROKEN_ARTIFACT_KINDS for r in failed_checks)


def repair_hint(failed_checks: Iterable[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for r in failed_checks:
        kind = str(r.get("kind") or "check")
        detail = str(r.get("detail") or "")[:240]
        parts.append(f"{kind}: {detail}")
    body = " | ".join(parts) if parts else "no evidence of completion was produced"
    return (
        "Your previous attempt did NOT pass verification. Concrete failures: "
        + body
        + ". Fix the actual files/tests on disk. Do not write a path named DONE: "
          "and do not replace the artifact with a DONE: line."
    )


def infer_package_dir(goal: str, criteria: Optional[List[str]] = None) -> Optional[str]:
    """Directory the goal names as the package layout, or None for workspace-root files.

    Prefers an explicit `under pkg/` or `pkg/{…}` layout, else a unique
    non-test directory prefix that appears on **two or more** mentioned files.
    A single `pkg/foo.py` mention is not a layout (`tests/` alone is never one).
    """
    blob = (goal or "") + "\n" + "\n".join(criteria or [])
    m = _PKG_UNDER_RE.search(blob)
    if m:
        return m.group(1) + "/"
    m = _PKG_BRACE_RE.search(blob)
    if m:
        return m.group(1) + "/"
    dirs = [d for d in _PKG_FILE_RE.findall(blob) if d.lower() not in _SKIP_PKG_DIRS]
    uniq = list(dict.fromkeys(dirs))
    # A single `pkg/foo.py` mention is not a package layout (the rest of the
    # tree may live at the workspace root — realworld coding / multi_agent).
    if len(uniq) == 1 and len(dirs) >= 2:
        return uniq[0] + "/"
    return None


def align_rel_path(path: str, package_dir: Optional[str]) -> str:
    """Prefix a bare relative path with the package dir. Directed paths are kept."""
    if not package_dir or not path:
        return path
    raw = str(path).strip().replace("\\", "/")
    if is_done_pollution_path(raw):
        return path
    if Path(raw).is_absolute() or raw.startswith("/"):
        return path
    while raw.startswith("./"):
        raw = raw[2:]
    if not raw or "/" in raw:
        return path
    return package_dir.rstrip("/") + "/" + raw


def align_shell_command(command: str, package_dir: Optional[str]) -> str:
    """Rewrite bare `test_*.py` in a shell command to the package-relative path."""
    if not package_dir or not command:
        return command
    prefix = package_dir.rstrip("/") + "/"

    def _repl(m: re.Match) -> str:
        return prefix + m.group(1)

    return _BARE_TEST_IN_CMD_RE.sub(_repl, command)


def align_check(check: Check, package_dir: Optional[str]) -> Check:
    """Align path/command args on one check. Check *kind* is never remapped (F-26)."""
    if not package_dir:
        return check
    args = dict(check.args or {})
    changed = False
    if "path" in args:
        new_path = align_rel_path(str(args.get("path", "")), package_dir)
        if new_path != args.get("path"):
            args["path"] = new_path
            changed = True
    if "command" in args:
        new_cmd = align_shell_command(str(args.get("command", "")), package_dir)
        if new_cmd != args.get("command"):
            args["command"] = new_cmd
            changed = True
    if not changed:
        return check
    return Check(kind=check.kind, args=args, description=check.description)


def align_checks(checks: Iterable[Check], package_dir: Optional[str]) -> List[Check]:
    return [align_check(c, package_dir) for c in checks]


def infer_coding_checks(goal: str, criteria: Optional[List[str]] = None) -> List[Check]:
    """Structured objective checks for coding/verification goals.

    Fallback plans still emit *tasks* without checks (F-17 contract). This only
    fills *objective_checks* so invalid JSON / failing tests cannot become VERIFIED.
    Bare paths are joined to the goal's package directory when one is named.
    """
    blob = (goal or "") + "\n" + "\n".join(criteria or [])
    if not is_coding_or_verify_goal(blob):
        return []
    package_dir = infer_package_dir(goal, criteria)
    out: List[Check] = []
    seen = set()
    for m in JSON_PATH_RE.finditer(blob):
        path = align_rel_path(m.group(1), package_dir)
        if is_done_pollution_path(path):
            continue
        key = ("json_valid", path)
        if key in seen:
            continue
        seen.add(key)
        out.append(Check("json_valid", {"path": path}, f"{path} is valid JSON"))
    test_file = None
    m = TEST_FILE_RE.search(blob)
    if m:
        test_file = align_rel_path(m.group(1), package_dir)
    low = blob.lower()
    wants_tests = bool(test_file) or bool(re.search(r"\b(pytest|run the tests?|write the tests?)\b", low))
    if wants_tests:
        cmd = f"python3 {test_file}" if test_file else "python3 -m pytest -q"
        cmd = align_shell_command(cmd, package_dir)
        out.append(Check("shell_ok", {"command": cmd}, "tests exit 0"))
    return out[:6]
