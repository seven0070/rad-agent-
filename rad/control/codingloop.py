"""Verified coding loop helpers — machine checks, not model DONE: claims.

When an objective is coding/verification-shaped, RAD infers disk checks
(json_valid, pytest/test exit 0) and treats failed content/tests as a
repairable validation failure. A `DONE:` line is never an artifact path
or a substitute for the file.
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
TEST_FILE_RE = re.compile(r"\b((?:tests/)?test_\w+\.py)\b", re.I)
DONE_PREFIX_RE = re.compile(r"^\s*DONE\s*:", re.I)

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


def infer_coding_checks(goal: str, criteria: Optional[List[str]] = None) -> List[Check]:
    """Structured objective checks for coding/verification goals.

    Fallback plans still emit *tasks* without checks (F-17 contract). This only
    fills *objective_checks* so invalid JSON / failing tests cannot become VERIFIED.
    """
    blob = (goal or "") + "\n" + "\n".join(criteria or [])
    if not is_coding_or_verify_goal(blob):
        return []
    out: List[Check] = []
    seen = set()
    for m in JSON_PATH_RE.finditer(blob):
        path = m.group(1)
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
        test_file = m.group(1)
    low = blob.lower()
    wants_tests = bool(test_file) or bool(re.search(r"\b(pytest|run the tests?|write the tests?)\b", low))
    if wants_tests:
        cmd = f"python3 {test_file}" if test_file else "python3 -m pytest -q"
        out.append(Check("shell_ok", {"command": cmd}, "tests exit 0"))
    return out[:6]
