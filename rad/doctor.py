"""`rad doctor` — one command that tells you whether RAD is healthy and, with --fix, repairs
what is safe to repair. Every check returns (status, message, fix?) and nothing is changed
unless `fix=True`. Status: ok | warn | fail."""
from __future__ import annotations

import os
import platform
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.home import RadHome
from rad.storage import SCHEMA_VERSION, Storage, validate_config


@dataclass
class Finding:
    check: str
    status: str                       # ok | warn | fail
    message: str
    fixed: bool = False
    detail: List[str] = field(default_factory=list)


class Doctor:
    def __init__(self, home: RadHome, fix: bool = False, probe_network: bool = True) -> None:
        self.home = home
        self.fix = fix
        self.probe_network = probe_network
        self.storage = Storage(home)

    def run(self) -> List[Finding]:
        checks: List[Callable[[], Finding]] = [
            self.c_python, self.c_home_tree, self.c_permissions, self.c_config, self.c_schema, self.c_integrity,
            self.c_workspace, self.c_dna, self.c_policy, self.c_memory, self.c_objectives, self.c_agents,
            self.c_skills, self.c_providers, self.c_disk, self.c_tools_on_path,
        ]
        out = []
        for c in checks:
            try:
                out.append(c())
            except Exception as e:                       # a broken check must not hide the others
                out.append(Finding(c.__name__[2:], "fail", f"check crashed: {type(e).__name__}: {str(e)[:120]}"))
        return out

    # ---- environment
    def c_python(self) -> Finding:
        v = sys.version_info
        st = "ok" if v >= (3, 9) else "fail"
        return Finding("python", st, f"Python {v.major}.{v.minor}.{v.micro} on {platform.system()} {platform.machine()}")

    def c_tools_on_path(self) -> Finding:
        want = {"git": "used by rad connect / evolution provenance", "sh": "shell tool", "python3": "lab graders, skills"}
        missing = [k for k in want if shutil.which(k) is None]
        return Finding("tools", "warn" if missing else "ok",
                       "all helper binaries present" if not missing else f"missing: {', '.join(missing)}",
                       detail=[f"{m}: {want[m]}" for m in missing])

    def c_disk(self) -> Finding:
        u = shutil.disk_usage(self.home.root)
        free_gb = u.free / 1e9
        size = sum(v["bytes"] for v in self.storage.usage().values())
        st = "ok" if free_gb > 1 else ("warn" if free_gb > 0.2 else "fail")
        return Finding("disk", st, f"{free_gb:.1f} GB free; ~/.rad uses {size / 1e6:.1f} MB")

    # ---- home
    def c_home_tree(self) -> Finding:
        need = ["memory/short", "memory/long/episodic", "memory/long/semantic", "memory/long/procedural",
                "dna", "skills", "keys", "logs"]
        missing = [d for d in need if not (self.home.root / d).is_dir()]
        if missing and self.fix:
            self.home._make_tree(); missing = [d for d in need if not (self.home.root / d).is_dir()]
            return Finding("home", "ok", f"recreated missing dirs under {self.home.root}", fixed=True)
        return Finding("home", "fail" if missing else "ok",
                       f"{self.home.root}" + (f" — missing {missing}" if missing else " complete"))

    def c_permissions(self) -> Finding:
        probs, fixed = [], False
        for rel, want in (("keys", 0o700), (".vault.key", 0o600), ("keys/keys.env", 0o600), ("keys/vault.enc", 0o600)):
            p = self.home.root / rel
            if not p.exists():
                continue
            mode = p.stat().st_mode & 0o777
            if mode & 0o077:
                if self.fix:
                    os.chmod(p, want); fixed = True
                else:
                    probs.append(f"{rel} is {oct(mode)} (want {oct(want)})")
        if fixed and not probs:
            return Finding("permissions", "ok", "tightened secret file permissions", fixed=True)
        return Finding("permissions", "warn" if probs else "ok", "; ".join(probs) or "secret files are private", detail=probs)

    def c_config(self) -> Finding:
        issues = validate_config(self.home.cfg)
        if not issues:
            return Finding("config", "ok", f"{self.home.config_path.name} valid ({len(self.home.cfg)} keys)")
        if self.fix:
            for i in issues:
                if i.fix == "__remove__":
                    self.home.cfg.pop(i.key, None)
                elif i.fix is not None:
                    self.home.cfg[i.key] = i.fix
            self.home.save_config()
            left = validate_config(self.home.cfg)
            return Finding("config", "warn" if left else "ok",
                           f"fixed {len(issues) - len(left)} issue(s)" + (f", {len(left)} need you" if left else ""),
                           fixed=True, detail=[f"{i.key}: {i.problem} (value {i.value!r})" for i in left])
        return Finding("config", "warn", f"{len(issues)} issue(s)",
                       detail=[f"{i.key}: {i.problem} (value {i.value!r})" + (f" → --fix sets {i.fix!r}" if i.fix is not None and i.fix != "__remove__" else "") for i in issues])

    def c_schema(self) -> Finding:
        v = self.storage.version()
        pend = self.storage.pending()
        if not pend:
            return Finding("schema", "ok", f"storage schema v{v} (current)")
        if self.fix:
            done = self.storage.migrate()
            return Finding("schema", "ok", f"migrated v{v} → v{self.storage.version()}", fixed=True,
                           detail=[f"v{d['version']}: {d['name']} {d.get('summary', '')}" for d in done])
        return Finding("schema", "warn", f"storage schema v{v}, {len(pend)} migration(s) pending (rad doctor --fix)",
                       detail=[f"v{m.version}: {m.name}" for m in pend])

    def c_integrity(self) -> Finding:
        f = self.storage.integrity(repair=self.fix)
        if not f:
            return Finding("integrity", "ok", "no corrupt or leftover files")
        rep = sum(1 for x in f if x["repaired"])
        unfix = [x for x in f if not x["fixable"]]
        st = "fail" if unfix and not self.fix else ("warn" if unfix else ("ok" if rep == len(f) else "warn"))
        return Finding("integrity", st, f"{len(f)} finding(s)" + (f", {rep} quarantined" if rep else ""), fixed=bool(rep),
                       detail=[f"{x['path']}: {x['problem']}" + (f" → {x['quarantined_as']}" if x.get('quarantined_as') else "") for x in f])

    def c_workspace(self) -> Finding:
        ws = self.home.workspace()
        if not ws.exists():
            return Finding("workspace", "fail", f"{ws} does not exist (rad workspace <dir>)")
        if not os.access(ws, os.W_OK):
            return Finding("workspace", "fail", f"{ws} is not writable")
        note = " (allow_outside_workspace is ON — file tools may leave it)" if self.home.cfg.get("allow_outside_workspace") else ""
        return Finding("workspace", "warn" if note else "ok", f"{ws}{note}")

    # ---- subsystems
    def c_dna(self) -> Finding:
        from rad.dna import Evolver
        ev = Evolver(self.home)
        dna = ev.load()
        gens = ev.generations()
        if dna.get("generation") not in gens:
            if self.fix:
                ev._write_gen(dna)
                return Finding("dna", "ok", f"re-materialised generation {dna.get('generation')}", fixed=True)
            return Finding("dna", "warn", f"current generation {dna.get('generation')} has no gen file")
        return Finding("dna", "ok", f"generation {dna.get('generation')} of {len(gens)}, {len(dna.get('lessons', []))} lessons")

    def c_policy(self) -> Finding:
        from rad.policy import Policy
        pol = Policy(self.home)
        rules = pol.rules
        loose = [f"default {k}=ALLOW" for k in ("shell", "fs.write", "mcp") if pol.default_for(k) == "ALLOW"]
        loose += [f"rule#{i} {r.capability} ALLOW {r.match!r}" for i, r in enumerate(rules) if r.effect == "ALLOW" and r.capability in ("shell", "fs.write") and r.match == "*"]
        st = "warn" if loose else "ok"
        return Finding("policy", st, f"{len(rules)} rule(s); hard layer active" + ("; permissive: " + ", ".join(loose) if loose else ""))

    def c_memory(self) -> Finding:
        from rad.memory import Memory
        m = Memory(self.home)
        entries = m.scan()
        contra = len(m.contradictions())
        unslept = len(m.unslept_short_text())
        st = "warn" if (contra > 5 or unslept > 20000) else "ok"
        return Finding("memory", st, f"{len(entries)} long-term, {contra} contradiction(s), {unslept} chars unconsolidated"
                       + (" (rad sleep)" if unslept > 20000 else ""))

    def c_objectives(self) -> Finding:
        from rad.control.objectives import ObjectiveStore
        store = ObjectiveStore(self.home)
        objs = store.list()
        stuck = [o for o in objs if o.status == "running" and (time.time() - (o.updated or o.created)) > 6 * 3600]
        needs = [o for o in objs if o.status == "needs_user"]
        st = "warn" if stuck or needs else "ok"
        return Finding("objectives", st, f"{len(objs)} total, {len(needs)} need you, {len(stuck)} stale-running",
                       detail=[f"{o.id} {o.status} {o.goal[:50]}" for o in (needs + stuck)[:8]])

    def c_agents(self) -> Finding:
        from rad.agents import AgentRegistry, ALL_CAPS
        reg = AgentRegistry(self.home)
        bad = []
        for aid, sp in reg.all().items():
            if any(c not in ALL_CAPS for c in sp.caps):
                bad.append(aid)
        return Finding("agents", "warn" if bad else "ok", f"{len(reg.all())} agents" + (f"; invalid caps in {bad}" if bad else ""))

    def c_skills(self) -> Finding:
        reg = self.home.skills()
        if not reg:
            return Finding("skills", "ok", "no MCP skills connected")
        probs = []
        for name, e in reg.items():
            if e.get("transport", "stdio") == "stdio":
                cmd = (e.get("command") or [None])[0]
                if cmd and not (shutil.which(cmd) or Path(cmd).exists()):
                    probs.append(f"{name}: command {cmd!r} not found")
            if not e.get("tools"):
                probs.append(f"{name}: no tools recorded (reconnect)")
        return Finding("skills", "warn" if probs else "ok", f"{len(reg)} skill(s)" + ("; " + "; ".join(probs) if probs else ""), detail=probs)

    def c_providers(self) -> Finding:
        if not self.probe_network:
            return Finding("providers", "ok", "skipped (offline mode)")
        from rad.router import RouterState
        r = RouterState(self.home)
        chain = r.build_chain()
        if not chain:
            return Finding("providers", "fail", "no brain available: add a key (rad keys add …) or start a local engine")
        names = [getattr(getattr(e, "spec", e), "name", str(e)) for e in chain][:5]
        return Finding("providers", "ok", f"{len(chain)} usable: {', '.join(names)}")


def render(findings: List[Finding]) -> str:
    from rad.ui import col
    sym = {"ok": col.green("✓"), "warn": col.yellow("!"), "fail": col.red("✗")}
    lines = []
    for f in findings:
        tag = col.dim(" (fixed)") if f.fixed else ""
        lines.append(f"  {sym[f.status]} {f.check:<12} {f.message}{tag}")
        for d in f.detail[:8]:
            lines.append(f"        {col.dim(d)}")
    n = {s: sum(1 for f in findings if f.status == s) for s in ("ok", "warn", "fail")}
    lines.append(f"  {n['ok']} ok · {n['warn']} warn · {n['fail']} fail")
    return "\n".join(lines)
