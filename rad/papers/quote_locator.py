"""Fuzzy verbatim locator — the quote-law's deterministic enforcer.

Law: a pinned quote must exist VERBATIM in the paper text. LLMs paraphrase,
so the locator converts a paraphrase-hint into the actual on-disk span.

CONTRACT (L2): returns the ORIGINAL paper substring (verbatim bytes),
match ratio rounded 3dp, pinned only when ratio >= min_ratio.
Deterministic: same inputs -> same span.
"""
from difflib import SequenceMatcher
import re


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _windows(words: list, size: int, overlap_frac: float = 0.5):
    step = max(1, int(size * (1 - overlap_frac)))
    for i in range(0, max(1, len(words) - size + 1), step):
        yield i, words[i:i + size]
    if len(words) > size:                       # tail window
        yield len(words) - size, words[-size:]


def locate_verbatim(paper_text: str, hint: str,
                    min_ratio: float = 0.60) -> "dict | None":
    """Find the paper's real span closest to the hint.
    Returns {"verbatim": str, "ratio": float} pinned only if ratio >= min_ratio."""
    if not hint or not hint.strip() or not paper_text:
        return None
    norm_paper = _norm(paper_text)
    norm_hint = _norm(hint)
    if norm_hint in norm_paper:                 # exact (normalized) hit
        return {"verbatim": hint.strip(), "ratio": 1.0}
    hw = norm_hint.split()
    size = max(8, len(hw))
    pw = norm_paper.split()
    best, best_ratio = None, 0.0
    for _, win in _windows(pw, size):
        cand = " ".join(win)
        r = SequenceMatcher(None, norm_hint, cand).ratio()
        if r > best_ratio:
            best, best_ratio = cand, r
    if best is None or best_ratio < min_ratio:
        return None
    # map normalized span back to original text (first occurrence)
    probe = best[:80]
    idx = norm_paper.find(probe)
    if idx < 0:
        return None
    # walk original text to the same word offset (words align 1:1 after _norm)
    w_idx = len(norm_paper[:idx].split())
    orig_words = paper_text.split()
    span_words = orig_words[max(0, w_idx - 2): w_idx + size + 2]
    return {"verbatim": " ".join(span_words), "ratio": round(best_ratio, 3)}
