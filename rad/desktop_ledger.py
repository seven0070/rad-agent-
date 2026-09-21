"""Desktop Ledger data layer — the replication trail for the cockpit.



Pure read/fold logic (no UI): amendments applied, provenance preserved.

The Tauri side (src/pages/Ledger.tsx) consumes this via the sidecar.



CONTRACT: fold is deterministic; identical input -> identical output.

"""

import json

from pathlib import Path



def set_paths(home: Path):   # L5

    global _LEDGER; _LEDGER = Path(home) / "papers" / "_ledger.jsonl"

_LEDGER = Path.home() / ".rad" / "papers" / "_ledger.jsonl"



def _read():

    if not _LEDGER.exists(): return []

    return [json.loads(l) for l in _LEDGER.read_text(encoding="utf-8").splitlines()

            if l.strip()]



def folded() -> dict:

    """Base entries + amendments applied + provenance kept. UI-ready shape."""

    entries, amends = {}, []

    for e in _read():

        if "amendment_of" in e:

            amends.append(e)

            t = entries.get(e["amendment_of"])

            if t and e.get("field") in t:

                t.setdefault("_amendments", []).append(

                    {k: e[k] for k in ("field", "was", "now", "reason", "amended_at")})

                t[e["field"]] = e["now"]

        elif "battle_id" in e:

            entries[e["battle_id"]] = e

    return {"format": "rad-desktop-ledger", "version": 1,

            "battles": list(entries.values()),

            "amendment_count": len(amends)}



def summary() -> dict:

    f = folded()

    v = {}

    for b in f["battles"]:

        k = b.get("replication_verdict", "?")

        v[k] = v.get(k, 0) + 1

    total = len(f["battles"])

    return {"battles": total, "verdicts": v,

            "replication_rate": round(v.get("CONFIRMED", 0) / total, 3) if total else 0,

            "amendments": f["amendment_count"]}

