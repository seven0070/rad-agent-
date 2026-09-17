"""Scheduler — hands that act while you're away.

  rad remind <when> <task>   fire a task on a clock
  rad watch <url>            notify when a public page changes
  rad jobs                   list / cancel

Watchers are detached processes — they survive you closing the terminal.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome, new_token
from rad.ui import col, ok, warn

# ---------------------------------------------------------------- when parsing

def parse_when(when: str) -> Optional[float]:
    """Support: 'in 5m' | '5m' | '2h' | '30s' | '1d' | 'tomorrow 9am' | ISO date."""
    when = when.strip().lower()
    m = re.match(r"^(?:in\s+)?(\d+)\s*(s|sec|m|min|h|hr|d|day)s?$", when)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        mult = {"s": 1, "sec": 1, "m": 60, "min": 60, "h": 3600, "hr": 3600, "d": 86400, "day": 86400}[unit]
        return time.time() + n * mult
    m = re.match(r"^tomorrow\s+(\d{1,2})\s*(am|pm)?$", when)
    if m:
        hour = int(m.group(1))
        ap = m.group(2) or "am"
        if ap == "pm" and hour < 12:
            hour += 12
        dt = datetime.now() + timedelta(days=1)
        dt = dt.replace(hour=hour, minute=0, second=0, microsecond=0)
        return dt.timestamp()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(when, fmt)
            if fmt == "%H:%M":
                dt = dt.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
                if dt.timestamp() < time.time() - 60:
                    dt += timedelta(days=1)
            return dt.timestamp()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- jobs store

def _load(home: RadHome) -> List[Dict[str, Any]]:
    try:
        return json.loads(home.jobs_path.read_text())
    except Exception:
        return []


def _save(home: RadHome, jobs: List[Dict[str, Any]]) -> None:
    home.jobs_path.write_text(json.dumps(jobs, indent=2))


def add_job(home: RadHome, kind: str, at: float, task: str, url: str = "",
            every_min: int = 0) -> Dict[str, Any]:
    jobs = _load(home)
    job = {"id": new_token(6), "kind": kind, "at": at, "task": task, "url": url,
           "every_min": every_min, "done": False, "created": time.time(), "note": ""}
    jobs.append(job)
    _save(home, jobs)
    # detached watcher survives this process
    log = open(home.root / "logs" / f"job-{job['id']}.log", "a")
    if os.name == "nt":
        popen_kwargs = {"creationflags": 0x00000200 | 0x00000008}  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs = {"start_new_session": True}
    subprocess.Popen([sys.executable, "-m", "rad", "watcher", job["id"]],
                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                     env={**os.environ, "RAD_HOME": str(home.root)}, **popen_kwargs)
    return job


def cancel_job(home: RadHome, jid: str) -> bool:
    jobs = _load(home)
    for j in jobs:
        if j["id"] == jid and not j["done"]:
            j["done"] = True
            j["note"] = "cancelled"
            _save(home, jobs)
            return True
    return False


def list_jobs(home: RadHome) -> str:
    jobs = [j for j in _load(home) if not j["done"]]
    if not jobs:
        return "  no pending jobs"
    out = []
    for j in jobs[-20:]:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(j["at"]))
        kind = f"watch {j['url']}" if j["kind"] == "watch" else j["task"]
        out.append(f"  {col.cyan(j['id'])}  {when}  {kind[:60]}")
    return "\n".join(out)


def notify(home: RadHome, text: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(home.notifications_path, "a", encoding="utf-8") as f:
        f.write(f"\n## [{ts}] Rad\n{text.strip()}\n")
    home.log("jobs", text)
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass


# ---------------------------------------------------------------- watcher loop

def run_watcher(home: RadHome, jid: str) -> None:
    while True:
        jobs = _load(home)
        job = next((j for j in jobs if j["id"] == jid), None)
        if job is None or job.get("done"):
            return
        if job["kind"] == "note":
            if time.time() >= job["at"]:
                job["done"] = True
                _save(home, jobs)
                notify(home, f"reminder: {job['task']}")
            time.sleep(min(30, max(1, job["at"] - time.time())))
            if time.time() >= job["at"]:
                continue
        elif job["kind"] == "watch":
            from rad.tools import fetch_public_page
            every = job.get("every_min") or home.cfg.get("watch_every_min", 30)
            state = home.root / "logs" / f"watch-{jid}.hash"
            text, err = fetch_public_page(job["url"], max_chars=200_000)
            if not err and text:
                import hashlib
                h = hashlib.sha256(text.encode()).hexdigest()[:16]
                old = state.read_text().strip() if state.exists() else None
                if old and old != h:
                    notify(home, f"page changed: {job['url']}\nfirst 400 chars of new content:\n{text[:400]}")
                    # keep watching until cancelled
                elif not old:
                    state.write_text(h)
                    home.log("jobs", f"watch baseline set for {job['url']}")
            time.sleep(every * 60)
        else:
            return
        time.sleep(1)
