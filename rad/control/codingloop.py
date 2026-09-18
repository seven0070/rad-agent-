"""Verified coding loop helpers — machine checks, not model DONE: claims.

When an objective is coding/verification-shaped, RAD infers disk checks
(json_valid, pytest/test exit 0) and treats failed content/tests as a
repairable validation failure. A `DONE:` line is never an artifact path
or a substitute for the file.

Package-layout goals (e.g. files under `text_analyzer/`, or an ASCII tree
`text_analyzer/` + `├── file`) get check paths joined to that directory so
root-only checks cannot thrash a package write (RW-069 / RW-073 / Gen3
theme 1). Multi-file goals also infer exact line-count and non-empty JSON
contracts so weak artifacts cannot become VERIFIED (RW-071 / Gen3 theme 2).
Fallback *tasks* stay check-less (F-17). First-task thrash (RW-075): a missing
`requirements.txt` from `pip install -r` is not an environment prerequisite, and
an invented tool named `DONE` / `DONE: …` is a protocol mistake, not a failed
contract (Gen3 theme 3 slice B).
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
TXT_PATH_RE = re.compile(r"\b((?:[\w.-]+/)*[\w.-]+\.txt)\b", re.I)
LINE_COUNT_RE = re.compile(r"\b(?:exact\s+)?(\d+)[ -]lines?\b", re.I)
DONE_PREFIX_RE = re.compile(r"^\s*DONE\s*:", re.I)
DONE_TOOL_RE = re.compile(r"^\s*DONE(?:\s*:.*)?\s*$", re.I)
_PIP_REQ_ERR = re.compile(
    r"Could not open requirements file|"
    r"No such file or directory:\s*['\"][^'\"]*requirements[^'\"]*['\"]",
    re.I,
)
_PIP_INSTALL_R = re.compile(r"\bpip(?:3)?\b(?:\s+\S+)*\s+install\s+-r\b", re.I)
_COMMAND_NOT_FOUND = re.compile(r"command not found", re.I)
# "under pkg/" (slash required so "under the …" is not a package name)
_PKG_UNDER_RE = re.compile(
    r"\bunder\s+(?:the\s+)?(?:directory\s+|dir\s+|package\s+|folder\s+)?([A-Za-z_][\w.-]*)/",
    re.I,
)
_PKG_BRACE_RE = re.compile(r"\b([A-Za-z_][\w.-]*)/\{")
_PKG_FILE_RE = re.compile(r"\b([A-Za-z_][\w.-]*)/(?:[\w.-]+/)*[\w.-]+\.\w+")
_SKIP_PKG_DIRS = frozenset({"tests", "test", "docs", "doc"})
# ASCII / box-drawing tree: `pkg/` on its own line, then ├── / └── / |-- children.
_TREE_HEAD_RE = re.compile(r"^[ \t]*([A-Za-z_][\w.-]*)/[ \t]*$")
_TREE_BRANCH_RE = re.compile(
    r"^[ \t]*(?:"
    r"(?:[│|][ \t]*)?[├└]─{1,4}"
    r"|"
    r"(?:\|--|`--|\+--)"
    r")[ \t]+(\S+)"
)
_TREE_CONT_RE = re.compile(r"^[ \t]*[│|]+[ \t]*$")
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


def is_done_protocol_tool(name: str) -> bool:
    """True when the model invoked DONE / DONE: … as if it were a tool (RW-075)."""
    return bool(DONE_TOOL_RE.match(str(name or "").strip()))


def is_pip_requirements_file_missing(output: str = "", command: str = "") -> bool:
    """True when pip -r failed because the requirements file does not exist.

    That is not a missing environment dependency for stdlib-only coding (RW-075).
    `pip: command not found` stays a genuine ENVIRONMENT signal (F-18).
    """
    out = output or ""
    cmd = command or ""
    if _COMMAND_NOT_FOUND.search(out):
        return False
    if _PIP_REQ_ERR.search(out):
        return True
    if _PIP_INSTALL_R.search(cmd) and re.search(r"no such file|ENOENT|not found", out, re.I):
        return True
    return False


def is_first_task_thrash_noise(tool: str, output: str = "", command: str = "") -> bool:
    """Approach noise that must not fail a task whose machine checks passed."""
    if is_done_protocol_tool(tool):
        return True
    return is_pip_requirements_file_missing(output, command)


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
          "and do not replace the artifact with a DONE: line. "
          "Do not call a tool named DONE. Do not pip install -r a missing requirements.txt "
          "for stdlib-only coding."
    )


def _ascii_tree_package_dir(blob: str) -> Optional[str]:
    """`pkg/` on its own line followed by two or more tree children (`├── file`).

    Markdown dash lists (`- file`) are not a tree. `tests/` / `docs/` heads are
    skipped. A single child is not a layout (same bar as two `pkg/foo` mentions).
    """
    lines = (blob or "").splitlines()
    for i, line in enumerate(lines):
        m = _TREE_HEAD_RE.match(line)
        if not m:
            continue
        name = m.group(1)
        if name.lower() in _SKIP_PKG_DIRS:
            continue
        files: List[str] = []
        for later in lines[i + 1:]:
            if not later.strip() or _TREE_CONT_RE.match(later):
                continue
            bm = _TREE_BRANCH_RE.match(later)
            if not bm:
                break
            files.append(bm.group(1))
        if len(files) >= 2:
            return name + "/"
    return None


def infer_package_dir(goal: str, criteria: Optional[List[str]] = None) -> Optional[str]:
    """Directory the goal names as the package layout, or None for workspace-root files.

    Prefers an explicit `under pkg/` or `pkg/{…}` layout, else a unique
    non-test directory prefix that appears on **two or more** mentioned files,
    else an ASCII / box-drawing tree (`pkg/` + `├── file` children).
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
    return _ascii_tree_package_dir(blob)


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
    line_m = LINE_COUNT_RE.search(blob)
    if line_m:
        n = int(line_m.group(1))
        txts: List[str] = []
        for tm in TXT_PATH_RE.finditer(blob):
            path = align_rel_path(tm.group(1), package_dir)
            if is_done_pollution_path(path) or path in txts:
                continue
            txts.append(path)
        chosen = next((p for p in txts if Path(p).name.lower() == "input.txt"), None)
        if chosen is None and txts:
            chosen = txts[0]
        if chosen:
            key = ("file_line_count", chosen)
            if key not in seen:
                seen.add(key)
                out.append(Check(
                    "file_line_count", {"path": chosen, "n": n},
                    f"{chosen} has exactly {n} lines",
                ))
    return out[:6]


def merge_coding_checks(existing: Optional[Iterable[Check]],
                        inferred: Optional[Iterable[Check]]) -> List[Check]:
    """Add inferred coding checks the planner omitted. Check *kinds* are never remapped (F-26)."""
    out: List[Check] = list(existing or [])
    seen = set()
    json_paths = set()
    line_paths = set()
    has_shell = False
    for c in out:
        args = c.args or {}
        path = str(args.get("path", "")).replace("\\", "/")
        cmd = str(args.get("command", ""))
        seen.add((c.kind, path or cmd))
        if c.kind in ("json_valid", "json_field", "json_min_len") and path:
            json_paths.add(path)
        if c.kind == "file_line_count" and path:
            line_paths.add(path)
        if c.kind in ("shell_ok", "shell_output"):
            has_shell = True
    for c in inferred or []:
        args = c.args or {}
        path = str(args.get("path", "")).replace("\\", "/")
        cmd = str(args.get("command", ""))
        key = (c.kind, path or cmd)
        if key in seen:
            continue
        if c.kind == "json_valid" and path in json_paths:
            continue
        if c.kind == "file_line_count" and path in line_paths:
            continue
        if c.kind == "shell_ok" and has_shell:
            continue
        seen.add(key)
        out.append(c)
        if c.kind in ("json_valid", "json_field", "json_min_len") and path:
            json_paths.add(path)
        if c.kind == "file_line_count" and path:
            line_paths.add(path)
        if c.kind in ("shell_ok", "shell_output"):
            has_shell = True
    return out[:8]
