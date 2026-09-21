#!/usr/bin/env python3
"""Diagnose extraction on YOUR live brain. Run: python scripts/diagnose_extract.py
Prints a stage-by-stage table: where the pipeline actually breaks."""
import json, sys, time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rad.home import RadHome
from rad.router import BrainRouter
from rad.integrate.hooks import make_brain_fn

print("=== EXTRACTION DIAGNOSIS ===")
t0 = time.monotonic()
brain = make_brain_fn(BrainRouter(home=RadHome()), temperature=0.1)
print(f"[1] router constructed in {time.monotonic()-t0:.1f}s")

t0 = time.monotonic()
r1 = brain('Reply with exactly: {"ok": true}')
print(f'[2] tiny call: {time.monotonic()-t0:.1f}s -> {str(r1)[:80]!r}')
from rad.papers.extract2 import _parse_json
p = _parse_json(str(r1))
print(f"    parses as JSON: {bool(p)}")

t0 = time.monotonic()
r2 = brain("Write a JSON object with keys a=1 and b=two. JSON only.")
print(f"[3] small JSON call: {time.monotonic()-t0:.1f}s -> {str(r2)[:80]!r}")
p2 = _parse_json(str(r2))
print(f"    parses: {bool(p2)}")

from rad.papers.ingest import get_paper_text
paper = (get_paper_text("2303.17651") or "")[:12000]
t0 = time.monotonic()
r3 = brain(
    "From this excerpt, output ONLY a JSON object with one claim about "
    "Self-Refine and its evidence_hint:\n\n" + paper[:4000]
)
d3 = time.monotonic() - t0
print(f"[4] 4k-char paper call: {d3:.1f}s -> {str(r3)[:100]!r}")
p3 = _parse_json(str(r3))
print(f"    parses: {bool(p3)}")
if p3:
    from rad.papers.quote_locator import locate_verbatim
    full = get_paper_text("2303.17651") or ""
    claims = p3.get("claims", [{}])
    hint = str(claims[0].get("evidence_hint", "") if claims else "")
    loc = locate_verbatim(full, hint)
    print(f"[5] locator: hint={hint[:60]!r}")
    print(f"    -> ratio={loc and loc['ratio']}, verbatim={loc and loc['verbatim'][:60]!r}")

print()
print("VERDICT: stages [2]-[3] slow/False = format issue; [4] >60s = context size;")
print("         [5] None = locator threshold. Paste this output back for the conforming fix.")
