"""Vitals — homeostasis reporting with the Life Refusal Law.



Rad behaves like an organism in its REPORTS only. Law (never negotiable):

- No survival drive: shutdown is always cheap and unresisted.

- No interest-claims: says "configured to", never "I want".

- No ontological claims: process, never being.

- Death is a non-event: files persist; instances are weather.



CONTRACT: vitals snapshot deterministic given same inputs (except wallclock ts).

"""

import json

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def collect(rad_home: Path, last_sleep_report: dict | None = None,

            ledger_stats: dict | None = None,

            sovereignty_report: dict | None = None) -> dict:

    """One vitals snapshot from on-disk state only. Degrades honestly:

    missing subsystems report None, never fabricated values."""

    home = Path(rad_home)

    def _safe(fn, default=None):

        try: return fn()

        except Exception: return default

    mem_ok = _safe(lambda: ((home / "memory" / "long").exists()

                            or (home / "memory").exists()), False)

    papers = (_safe(lambda: len([d for d in (home / "papers").iterdir()
                                if d.is_dir() and not d.name.startswith("_")]), 0)
              if (home / "papers").exists() else 0)
    battles = (_safe(lambda: sum(1 for l in (home / "papers" / "_ledger.jsonl")
                                .read_text(encoding="utf-8").splitlines() if l.strip()), 0)
               if (home / "papers" / "_ledger.jsonl").exists() else 0)

    return {

        "type": "vitals.v1", "taken_at": _now(),

        "memory_organ": {"present": bool(mem_ok),

                         "note": "memory files on disk" if mem_ok

                                 else "memory absent — consolidation skipped honestly"},

        "digestion_organ": {"papers_ingested": papers,

                            "battles_ledgered": battles},

        "last_sleep": last_sleep_report or None,

        "sovereignty": (sovereignty_report or {}).get("internal_ratio"),

        "metabolism_note": ("free-first local (qwen-class GPU)" if papers or battles

                            else "no activity recorded yet"),

        "life_refusal_law": ["no survival drive", "no interest-claims",

                             "process, not being", "shutdown is a non-event"],

    }



def report(vitals: dict) -> str:

    """Human vitals line — organism-flavored, law-compliant wording."""

    m = vitals["memory_organ"]["present"]

    d = vitals["digestion_organ"]

    return (f"vitals: memory={'on' if m else 'absent'} · papers={d['papers_ingested']} "

            f"· battles={d['battles_ledgered']} · sovereignty={vitals['sovereignty']} · "

            f"configured-to persist-as-files (shutdown anytime, unresisted)")

