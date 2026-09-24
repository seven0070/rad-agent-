"""Verified coding loop helpers — machine checks, not model DONE: claims.

When an objective is coding/verification-shaped, RAD infers disk checks
(json_valid, pytest/test exit 0) and treats failed content/tests as a
repairable validation failure. A `DONE:` line is never an artifact path
or a substitute for the file.

Package-layout goals (e.g. files under `text_analyzer/`, or an ASCII tree
`text_analyzer/` + `├── file`) get check paths joined to that directory so
root-only checks cannot thrash a package write (RW-069 / RW-073 / Gen3
theme 1). Multi-file goals also infer exact line-count, named-file
`file_exists`, and `json_field` for keys the goal names so weak artifacts
(`{}` summary, missing README.md / analyzer.py) cannot become VERIFIED
(RW-071 / Gen3 theme 2; G4-7 / RW-096 / RW-097). Fallback *tasks* stay
check-less (F-17). First-task thrash (RW-075): a missing
`requirements.txt` from `pip install -r` is not an environment prerequisite, and
an invented tool named `DONE` / `DONE: …` is a protocol mistake, not a failed
contract (Gen3 theme 3 slice B). mkdir / create **already exists** after
`write_file` created the tree is the same family of action noise (RW-077 /
Gen3 theme 3 slice C) — it must not fail a task whose directory/file checks
passed. Premature `python …/test_*.py` (interpreter cannot open a `.py` script
the agent has not written yet) is sequencing, not a broken host environment
(RW-079 / Gen3 theme 3 slice D). Missing optional checksum/hex binaries
(`xxd`, `hexdump`, `sha256sum` and close variants) used only for inspection
theater are model/tool-choice, not a broken RAD host (RW-085 / theme 3
slice F) — python + write_file exist.
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
NAMED_PKG_FILE_RE = re.compile(r"\b((?:[\w.-]+/)*[\w.-]+\.(?:py|md))\b", re.I)
TEST_PY_NAME_RE = re.compile(r"(?:^|/)test_\w+\.py$", re.I)
TXT_PATH_RE = re.compile(r"\b((?:[\w.-]+/)*[\w.-]+\.txt)\b", re.I)
LINE_COUNT_RE = re.compile(r"\b(?:exact\s+)?(\d+)[ -]lines?\b", re.I)
JSON_PAREN_RE = re.compile(
    r"([\w./-]+\.json)\b[^\n]{0,80}?\(([^)]{1,120})\)",
    re.I,
)
JSON_KEY_WORD_RE = re.compile(r"\bkeys?\s+([A-Za-z_][\w]*)\b", re.I)
JSON_KEYS_LIST_RE = re.compile(
    r"\bkeys?\s*[:=]\s*([A-Za-z_][\w]*(?:\s*[,/]\s*[A-Za-z_][\w]*)+)",
    re.I,
)
JSON_KEY_STOP = frozenset({
    "a", "an", "and", "are", "as", "accurate", "classic", "correct", "count",
    "counts", "empty", "equal", "equals", "exact", "false", "field", "fields",
    "for", "have", "including", "integer", "is", "json", "key", "keys", "must",
    "named", "non", "nonempty", "object", "of", "required", "result", "results",
    "string", "summary", "the", "to", "true", "valid", "value", "values", "with",
    # English glue / prepositions (G4-7 ``key X`` / parenthetical split).
    # "keys on a sample" and "lines, words, characters on a sample" must
    # not invent json_field key ``on`` (or ``sample``).
    "about", "after", "against", "among", "around", "across", "at", "before",
    "between", "by", "during", "from", "how", "if", "in", "into", "it", "its",
    "like", "on", "onto", "or", "over", "per", "returning", "sample", "so",
    "such", "than", "then", "these", "this", "those", "through", "under",
    "upon", "using", "via", "what", "when", "where", "which", "while", "who",
    "why", "within", "without",
})
INFER_CODING_CHECK_CAP = 8
MERGE_CODING_CHECK_CAP = 10
DONE_PREFIX_RE = re.compile(r"^\s*DONE\s*:", re.I)
DONE_TOOL_RE = re.compile(r"^\s*DONE(?:\s*:.*)?\s*$", re.I)
_PIP_REQ_ERR = re.compile(
    r"Could not open requirements file|"
    r"No such file or directory:\s*['\"][^'\"]*requirements[^'\"]*['\"]",
    re.I,
)
_PIP_INSTALL_R = re.compile(r"\bpip(?:3)?\b(?:\s+\S+)*\s+install\s+-r\b", re.I)
_COMMAND_NOT_FOUND = re.compile(r"command not found", re.I)
_ALREADY_EXISTS = re.compile(r"already exists|FileExistsError|\bFile exists\b", re.I)
_MKDIR_LIKE = re.compile(
    r"\b(?:mkdir|md)\b|os\.mkdir|Path\([^)]*\)\.mkdir|\.mkdir\(",
    re.I,
)
_PERM_DENIED = re.compile(r"permission denied|EACCES", re.I)
_MODULE_NOT_FOUND = re.compile(r"ModuleNotFoundError|No module named", re.I)
# Optional hex/checksum utilities models invoke for inspection theater (RW-085).
_OPTIONAL_CHECKSUM_BIN = re.compile(
    r"\b(xxd|hexdump|sha256sum|sha1sum|shasum|md5sum)\b",
    re.I,
)
_OPTIONAL_BIN_NOT_FOUND = re.compile(
    r"(?:^|[\s/'\"`:])(?P<bin>xxd|hexdump|sha256sum|sha1sum|shasum|md5sum)"
    r"\s*:\s*(?:command not found|not found)\b",
    re.I,
)
_EXIT_127 = re.compile(r"\[exit[= ]127\]", re.I)
# CPython: python3: can't open file 'pkg/test_foo.py': [Errno 2] No such file …
_PYTHON_CANT_OPEN_SCRIPT = re.compile(
    r"can't open file\s+['\"][^'\"]+\.py['\"]",
    re.I,
)
# "under pkg/" (slash required so "under the …" is not a package name)
_PKG_UNDER_RE = re.compile(
    r"\bunder\s+(?:the\s+)?(?:directory\s+|dir\s+|package\s+|folder\s+)?([A-Za-z_][\w.-]*)/",
    re.I,
)
_PKG_BRACE_RE = re.compile(r"\b([A-Za-z_][\w.-]*)/\{")
# Inline one-line layout note: `pkg/ (ascii tree): f1, f2, …` / `pkg/ (tree): …`
_PKG_INLINE_TREE_RE = re.compile(
    r"\b([A-Za-z_][\w.-]*)/\s*\(\s*(?:ascii\s+)?tree\s*\)\s*:", re.I
)
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


def is_missing_python_script(output: str = "", command: str = "") -> bool:
    """True when the Python interpreter could not open a `.py` script argument.

    Running `python pkg/test_foo.py` before the agent wrote that file is
    sequencing / model error, not a missing host dependency (RW-079). The
    python binary exists; the file is agent-authored. `python: command not
    found` and `ModuleNotFoundError` stay genuine ENVIRONMENT (F-18). Nested
    `FileNotFoundError` from inside a running script (missing `input.txt`)
    is not this signal — CPython only emits `can't open file '….py'` when
    the script argument itself cannot be opened.
    """
    out = output or ""
    cmd = command or ""
    if _COMMAND_NOT_FOUND.search(out) or _MODULE_NOT_FOUND.search(out):
        return False
    if not _PYTHON_CANT_OPEN_SCRIPT.search(out):
        return False
    if cmd and not re.search(r"\bpython\d*(?:\.\d+)?\b", cmd, re.I):
        return False
    return True


def is_missing_optional_checksum_utility(output: str = "", command: str = "") -> bool:
    """True when xxd/hexdump/sha*sum is not installed (checksum theater).

    For stdlib coding the RAD host is python + write_file. A missing optional
    hex/checksum binary is model/tool-choice, not a missing environment
    prerequisite (RW-085). `python: command not found`, `pip: command not
    found`, and `cat` no-such-file stay genuine ENVIRONMENT (F-18).
    File-not-found on the *argument* (`sha256sum: input.txt: No such file
    or directory`) is not this signal — that binary exists.
    """
    out = output or ""
    cmd = command or ""
    if _OPTIONAL_BIN_NOT_FOUND.search(out):
        return True
    if not _OPTIONAL_CHECKSUM_BIN.search(cmd):
        return False
    if re.search(r"command not found", out, re.I) and _OPTIONAL_CHECKSUM_BIN.search(out):
        return True
    if _EXIT_127.search(out) and _OPTIONAL_CHECKSUM_BIN.search(cmd):
        return True
    return False


def is_mkdir_already_exists(output: str = "", command: str = "") -> bool:
    """True when mkdir/create failed because the path already exists (RW-077).

    write_file creates parent directories; a later `mkdir pkg` File-exists is
    not a failed directory contract when explicit file_exists/dir_exists checks
    can still pass. Permission denied and command-not-found stay real errors.
    """
    out = output or ""
    cmd = command or ""
    if _COMMAND_NOT_FOUND.search(out) or _PERM_DENIED.search(out):
        return False
    if not _ALREADY_EXISTS.search(out):
        return False
    return bool(_MKDIR_LIKE.search(cmd) or _MKDIR_LIKE.search(out))


def is_first_task_thrash_noise(tool: str, output: str = "", command: str = "") -> bool:
    """Approach noise that must not fail a task whose machine checks passed."""
    if is_done_protocol_tool(tool):
        return True
    if is_pip_requirements_file_missing(output, command):
        return True
    if is_missing_python_script(output, command):
        return True
    if is_missing_optional_checksum_utility(output, command):
        return True
    return is_mkdir_already_exists(output, command)


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
          "for stdlib-only coding. Do not mkdir a path write_file already created. "
          "Do not run python test_*.py before the test file exists. "
          "Do not call xxd/hexdump to inspect files for stdlib-only coding."
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

    Prefers an explicit `under pkg/` or `pkg/{…}` layout, else an inline
    `pkg/ (ascii tree): f1, f2` note (≥2 named files), else a unique
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
    m = _PKG_INLINE_TREE_RE.search(blob)
    if m and m.group(1).lower() not in _SKIP_PKG_DIRS:
        tail = blob[m.end():]
        files = re.findall(r"\b[\w-]+\.(?:py|txt|json|md)\b", tail, re.I)
        if len(files) >= 2:
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


def _check_ident(kind: str, path: str, cmd: str, field: str = "") -> tuple:
    """Dedupe key. json_field must keep one entry per (path, field)."""
    if kind == "json_field":
        return (kind, path, field)
    return (kind, path or cmd)


def _json_field_names(blob: str, json_path: str) -> List[str]:
    """Keys the goal names for a JSON artifact (parenthetical, 'key X', 'keys: a, b').

    English glue is dropped (``on`` in "keys on a sample" / parenthetical
    "characters on a sample") so a bogus json_field cannot block VERIFIED.
    """
    out: List[str] = []
    seen = set()

    def add(raw: str) -> None:
        tok = (raw or "").strip()
        if not tok or not re.match(r"^[A-Za-z_][\w]*$", tok):
            return
        low = tok.lower()
        if low in JSON_KEY_STOP or low in seen:
            return
        seen.add(low)
        out.append(tok)

    name = Path(json_path).name
    for m in JSON_PAREN_RE.finditer(blob or ""):
        mentioned = align_rel_path(m.group(1), None)
        if Path(mentioned).name.lower() != name.lower():
            continue
        for tok in re.split(r"[\s,/|;]+", m.group(2) or ""):
            add(tok)
    for m in JSON_KEY_WORD_RE.finditer(blob or ""):
        add(m.group(1))
    for m in JSON_KEYS_LIST_RE.finditer(blob or ""):
        for tok in re.split(r"[\s,/]+", m.group(1) or ""):
            add(tok)
    return out


def _named_package_files(blob: str, package_dir: Optional[str]) -> List[str]:
    """README.md / main module / other named .py|.md the goal requires (not test_*.py)."""
    out: List[str] = []
    seen = set()
    for m in NAMED_PKG_FILE_RE.finditer(blob or ""):
        path = align_rel_path(m.group(1), package_dir)
        if is_done_pollution_path(path):
            continue
        norm = path.replace("\\", "/")
        if TEST_PY_NAME_RE.search(norm):
            continue
        if norm in seen:
            continue
        seen.add(norm)
        out.append(path)
    return out


def infer_coding_checks(goal: str, criteria: Optional[List[str]] = None) -> List[Check]:
    """Structured objective checks for coding/verification goals.

    Fallback plans still emit *tasks* without checks (F-17 contract). This only
    fills *objective_checks* so invalid JSON / failing tests / missing named
    package files / empty `{}` summaries cannot become VERIFIED. Bare paths are
    joined to the goal's package directory when one is named.
    """
    blob = (goal or "") + "\n" + "\n".join(criteria or [])
    if not is_coding_or_verify_goal(blob):
        return []
    package_dir = infer_package_dir(goal, criteria)
    out: List[Check] = []
    seen = set()
    json_paths: List[str] = []
    covered_paths = set()
    for m in JSON_PATH_RE.finditer(blob):
        path = align_rel_path(m.group(1), package_dir)
        if is_done_pollution_path(path):
            continue
        key = _check_ident("json_valid", path, "")
        if key in seen:
            continue
        seen.add(key)
        json_paths.append(path)
        covered_paths.add(path.replace("\\", "/"))
        out.append(Check("json_valid", {"path": path}, f"{path} is valid JSON"))
    test_file = None
    m = TEST_FILE_RE.search(blob)
    if m:
        test_file = align_rel_path(m.group(1), package_dir)
        covered_paths.add(test_file.replace("\\", "/"))
    low = blob.lower()
    wants_tests = bool(test_file) or bool(re.search(r"\b(pytest|run the tests?|write the tests?)\b", low))
    if wants_tests:
        cmd = f"python3 {test_file}" if test_file else "python3 -m pytest -q"
        cmd = align_shell_command(cmd, package_dir)
        out.append(Check("shell_ok", {"command": cmd}, "tests exit 0"))
        seen.add(_check_ident("shell_ok", "", cmd))
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
            key = _check_ident("file_line_count", chosen, "")
            if key not in seen:
                seen.add(key)
                covered_paths.add(chosen.replace("\\", "/"))
                out.append(Check(
                    "file_line_count", {"path": chosen, "n": n},
                    f"{chosen} has exactly {n} lines",
                ))
    for path in json_paths:
        for field in _json_field_names(blob, path):
            key = _check_ident("json_field", path, "", field)
            if key in seen:
                continue
            seen.add(key)
            out.append(Check(
                "json_field",
                {"path": path, "key": field, "truthy": False},
                f"{path} has {field}",
            ))
    for path in _named_package_files(blob, package_dir):
        norm = path.replace("\\", "/")
        if norm in covered_paths:
            continue
        key = _check_ident("file_exists", path, "")
        if key in seen:
            continue
        seen.add(key)
        out.append(Check("file_exists", {"path": path}, f"{path} exists"))
    return out[:INFER_CODING_CHECK_CAP]


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
        field = str(args.get("key", "")) if c.kind == "json_field" else ""
        seen.add(_check_ident(c.kind, path, cmd, field))
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
        field = str(args.get("key", "")) if c.kind == "json_field" else ""
        key = _check_ident(c.kind, path, cmd, field)
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
    return out[:MERGE_CODING_CHECK_CAP]
