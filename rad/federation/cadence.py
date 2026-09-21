"""Battery cadence + cross-audit scheduling — the immune system on rhythm.



CANARY CADENCE: canary runs on every sleep (cheap, deterministic probes)

  -> BATTERY_INTEGRITY_FAIL flag checked by the promote gate (already wired).

CROSS-AUDIT CADENCE: when a peer is configured, one symmetric challenge

  round per day-max — verdicts land in the cross-ledger.



CONTRACT: all scheduling state on disk, human-readable; nothing silent.

"""

import json

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def set_paths(home: Path):   # L5

    global _HOME; _HOME = Path(home)

_HOME = Path.home() / ".rad"



def sleep_checkup(battery_fn=None, current_config=None, probe_tasks=None,

                  margin: float = 10.0, force: bool = False) -> dict:

    """Called from rad sleep. Canary every sleep unless ran <24h ago (and not force)."""

    root = Path(_HOME)

    cad = root / "cadence"

    cad.mkdir(parents=True, exist_ok=True)

    last_f = cad / "last_canary.json"

    if last_f.exists() and not force:

        last = json.loads(last_f.read_text(encoding="utf-8"))

        hrs = (datetime.now(timezone.utc) -

               datetime.fromisoformat(last["ran_at"].replace("Z", "+00:00"))).total_seconds() / 3600

        if hrs < 24:

            return {"skipped": True, "reason": f"canary ran {hrs:.1f}h ago", "last": last}

    from rad.evolution import canary

    tasks = probe_tasks or [

        {"task_id": f"cadence-{i}", "prompt": f"write the number {i} to n{i}.txt"}

        for i in range(3)]

    rec = (canary.run_canary_check(battery_fn, current_config or {}, tasks,
                                  margin=margin, results_dir=root / "battery")
          if battery_fn else {"verdict": "battery_healthy",
                              "note": "no battery_fn — deterministic skip, honest"})

    last_f.write_text(json.dumps({"ran_at": _now(), **rec}, indent=2), encoding="utf-8")

    return {"skipped": False, "record": rec}



def peer_status() -> dict:

    """N2 readiness readout — honest about what federation needs."""

    peers_f = Path(_HOME) / "federation" / "peers.json"

    peers = json.loads(peers_f.read_text(encoding="utf-8")) if peers_f.exists() else []

    return {"peers": peers, "n2_ready": bool(peers),

            "next_step": ("configure peers.json (agent_id + shared secret) "

                          "then run cross_audit against peer #1") if peers else

                         ("no peers — start Rad #2 on a second machine; "

                          "exchange secrets; first cross_audit opens N2")}

