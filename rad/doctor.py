"""`rad doctor` — one command that tells you whether RAD is healthy and, with --fix, repairs
what is safe to repair. Every check returns (status, message, fix?) and nothing is changed
unless `fix=True`. Status: ok | warn | optional | fail — rendered as READY / WARNING /
OPTIONAL / ERROR. Missing optional capabilities (providers, local engines, MCP, voice)
never make the core unusable."""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.health import last_class_c, scan_provider_health
from rad.home import RadHome
from rad.storage import SCHEMA_VERSION, Storage, validate_config


@dataclass
class Finding:
    check: str
    status: str                       # ok | warn | optional | fail
    message: str
    fixed: bool = False
    detail: List[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return {"ok": "READY", "warn": "WARNING", "optional": "OPTIONAL", "fail": "ERROR"}.get(
            self.status, self.status.upper())


class Doctor:
    def __init__(self, home: RadHome, fix: bool = False, probe_network: bool = True,
                 force: bool = False) -> None:
        self.home = home
        self.fix = fix
        self.probe_network = probe_network
        self.force = force
        self.storage = Storage(home)

    def run(self) -> List[Finding]:
        checks: List[Callable[[], Finding]] = [
            self.c_python, self.c_home_tree, self.c_permissions, self.c_config, self.c_schema, self.c_integrity,
            self.c_workspace, self.c_dna, self.c_policy, self.c_memory, self.c_objectives, self.c_agents,
            self.c_skills, self.c_providers, self.c_local_runtimes, self.c_mcp, self.c_browser,
            self.c_voice, self.c_interrupted, self.c_benchmarks, self.c_sandbox, self.c_disk,
            self.c_tools_on_path,
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
        pend = self.storage.pending()          # stamps a fresh home before we read the version
        v = self.storage.version()
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
            return Finding("skills", "optional", "no MCP skills connected (optional — `rad connect <link>`)")
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
        healths = scan_provider_health(
            self.home, skip_blocked_inference=not self.force, force=self.force)
        entitled = [h for h in healths if h.inference_entitled]
        catalog_only = [h for h in healths if h.catalog_alive and not h.inference_entitled]
        free_lock = bool(self.home.cfg.get("free_lock"))
        pinned = str(self.home.cfg.get("force_provider") or "")
        detail: List[str] = []
        last = last_class_c(self.home)
        skipped = [h.name for h in healths if h.skipped_inference]
        if skipped:
            detail.append(
                "chat ping skipped for " + ", ".join(skipped)
                + " — last Class C still blocks (Retry-After / persist); "
                "`rad doctor --force` only after a believed recovery")
        if last and last.get("class_c"):
            ra = last.get("retry_after")
            until = last.get("retry_after_until")
            extra = ""
            if until:
                left = float(until) - time.time()
                if left > 0:
                    extra = f"; Retry-After {int(left)}s"
            detail.append(
                f"last Class C: {last.get('provider')} {last.get('kind')} "
                f"HTTP {last.get('status')}{extra} — {last.get('next_steps') or 'rotate-key / wait-quota / rad use'}")
        if free_lock:
            detail.append("free_lock on — paid spend is off; 403/429 pause or rotate among free brains")
        if pinned:
            detail.append(
                f"force_provider={pinned} — Class C on this pin rotates to other usable free providers")
        for h in catalog_only:
            st = h.inference_status if h.inference_status is not None else "?"
            detail.append(
                f"{h.name}: catalog-alive (HTTP {h.catalog_status}) ≠ inference-entitled "
                f"(chat HTTP {st}) — not a live brain")
        if entitled:
            names = [h.name for h in entitled][:5]
            if len(entitled) == 1:
                detail.append(
                    "single inference-entitled brain — HTTP 403/429 is Class C needs_user "
                    "(rotate key / wait for quota / `rad use` another), not a Class A patch")
            else:
                detail.append(
                    "free-first rotation: 401/403/429 skip to the next usable free provider; "
                    "exhausted Class C pauses (needs_user), not a product retry")
            return Finding("providers", "ok",
                           f"{len(entitled)} inference-entitled: {', '.join(names)}",
                           detail=detail)
        if catalog_only:
            bits = []
            for h in catalog_only[:5]:
                st = h.inference_status if h.inference_status is not None else "?"
                bits.append(f"{h.name} (chat HTTP {st})")
            return Finding(
                "providers", "warn",
                f"{len(catalog_only)} catalog-alive, 0 inference-entitled: {', '.join(bits)}",
                detail=detail or [
                    "GET /v1/models 200 is not chat/completions entitlement (RW-084)",
                    "rotate the key, wait for quota, or `rad use` another free provider",
                ])
        if healths:
            names = [h.name for h in healths][:5]
            return Finding("providers", "warn",
                           f"{len(healths)} key(s) present but catalog/inference failed: {', '.join(names)}",
                           detail=detail or ["`rad keys add` a working free key or start a local engine"])
        if pinned:
            return Finding("providers", "warn",
                           f"force_provider={pinned} but no brain is reachable",
                           detail=["`rad use` another provider, `rad keys add <provider> <key>`, "
                                   "or start a local engine (`ollama serve`)"])
        return Finding("providers", "optional",
                       "no brain configured — add a key (`rad keys add <provider> <key>`) "
                       "or start a local engine; RAD still works offline",
                       detail=["control plane, memory, doctor, lab banks and acceptance run without a key",
                               "configure a brain when you want `rad chat` / live `rad evaluate`"])


    # ---- optional subsystems (all free to be absent; RAD stays usable)
    def c_local_runtimes(self) -> Finding:
        """Local engines (Ollama, LM Studio, Edge0, vLLM) — the free-first brains."""
        from rad.providers import all_specs, probe_local
        if not self.probe_network:
            return Finding("local-engines", "ok", "probe skipped (offline mode)")
        found: List[str] = []
        for spec in all_specs(self.home):
            if not spec.local:
                continue
            reachable, models = probe_local(spec)
            if reachable:
                extra = f" ({', '.join(models[:3])})" if models else ""
                found.append(f"{spec.name}{extra}")
        if found:
            return Finding("local-engines", "ok", "running: " + ", ".join(found))
        pinned = str(self.home.cfg.get("force_provider") or "")
        if pinned in ("ollama", "lmstudio", "edge0", "vllm"):
            return Finding("local-engines", "warn",
                           f"force_provider={pinned} is a local engine but nothing is listening",
                           detail=["start it, or pin a different brain with `rad use <provider>`",
                                   "optional: `ollama serve` gives free offline brains"])
        return Finding("local-engines", "optional",
                       "no local engine detected (optional — `ollama serve` or `rad keys add`)",
                       detail=["`rad providers` shows the chain; `ollama serve` gives free offline brains"])

    def c_mcp(self) -> Finding:
        """MCP skills: manifests parse, commands exist, permissions declared."""
        d = self.home.root / "skills"
        manifests = sorted(d.glob("*/manifest.json")) if d.is_dir() else []
        if not manifests:
            return Finding("mcp", "optional", "no MCP skills connected (optional — `rad connect <link>`)")
        problems: List[str] = []
        for m in manifests:
            try:
                doc = json.loads(m.read_text())
            except Exception as e:
                problems.append(f"{m.parent.name}: manifest unreadable ({str(e)[:60]})")
                continue
            cmd = (doc.get("command") or doc.get("server", {}).get("command")
                   if isinstance(doc.get("server"), dict) else doc.get("command"))
            if isinstance(cmd, str) and cmd and shutil.which(cmd.split()[0]) is None \
                    and not Path(cmd.split()[0]).exists():
                problems.append(f"{m.parent.name}: command '{cmd.split()[0]}' not found on PATH")
            if not doc.get("permissions") and not doc.get("approval"):
                problems.append(f"{m.parent.name}: no permissions/approval declared")
        if problems:
            return Finding("mcp", "warn", f"{len(problems)} issue(s) in {len(manifests)} skill(s)",
                           detail=problems)
        return Finding("mcp", "ok", f"{len(manifests)} skill(s) healthy")

    def c_browser(self) -> Finding:
        """Browser/environment: the always-available fetcher, plus Playwright when installed."""
        try:
            import rad.browser as _b  # noqa: F401
        except Exception as e:
            return Finding("browser", "fail", f"browser module unusable: {str(e)[:80]}")
        try:
            import playwright  # noqa: F401
            have = "playwright installed (screenshots, JS pages, clicks)"
        except Exception:
            have = "urllib driver only (navigation, extraction, forms, downloads)"
        if not self.probe_network:
            return Finding("browser", "ok", have + " — network probe skipped")
        try:
            import urllib.request
            with urllib.request.urlopen("https://example.com", timeout=3) as r:
                ok_net = r.status == 200
        except Exception as e:
            return Finding("browser", "warn", f"{have}; network unreachable ({str(e)[:50]})")
        return Finding("browser", "ok", have + "; outbound network works")

    def c_voice(self) -> Finding:
        """Voice is optional: report which half of the loop is available."""
        tts = next((c for c in ("piper", "say", "espeak", "espeak-ng", "spd-say") if shutil.which(c)), None)
        stt = "whisper" if shutil.which("whisper") else None
        rec = next((c for c in ("rec", "arecord", "sox") if shutil.which(c)), None)
        bits = [f"tts={tts or 'none'}", f"stt={stt or 'none'}", f"recorder={rec or 'none'}"]
        if tts or stt:
            return Finding("voice", "ok", ", ".join(bits))
        def _on(key: str) -> bool:
            v = str(self.home.cfg.get(key, "auto") or "").strip().lower()
            return v not in ("", "auto", "none", "off", "false", "0", "disabled")

        wanted = _on("voice_enabled") or _on("tts") or _on("stt")
        message = "no local voice tooling: " + ", ".join(bits)
        if wanted:
            return Finding("voice", "warn", message,
                           detail=["voice is enabled in config but no local tooling was found: "
                                   "install piper/whisper, or set an OpenAI key for API voice"])
        return Finding("voice", "optional", message + " (optional; unused until you enable voice)",
                       detail=["`rad install voice` or set an OpenAI key; chat still works without it"])

    def c_interrupted(self) -> Finding:
        """Crash recovery: objectives whose run died mid-flight and are waiting to be resumed."""
        from rad.control.checkpoints import CheckpointManager
        cm = CheckpointManager(self.home)
        items = cm.interrupted()
        if not items:
            return Finding("recovery", "ok", "no interrupted objective state")
        detail = [f"{i['id']}: {i['status']} ({len(i['in_flight'])} task(s) mid-flight) — "
                  f"rad objective resume {i['id']}" for i in items[:8]]
        if self.fix:
            done = [cm.restore(i["id"]) for i in items]
            return Finding("recovery", "ok", f"restored {len(done)} interrupted objective(s) "
                                             f"(resume with `rad objective resume <id>`)",
                           fixed=True, detail=detail)
        return Finding("recovery", "warn", f"{len(items)} objective(s) were interrupted by a crash "
                                           f"or restart — `rad doctor --fix` prepares them for resume",
                       detail=detail)

    def c_benchmarks(self) -> Finding:
        """Evaluation evidence exists and is intact (not 'good' — just present and parseable)."""
        bits = []
        for label, path in (("lab", self.home.root / "lab"),
                            ("long-horizon", self.home.root / "benchmarks" / "longhorizon"),
                            ("evaluation", self.home.root / "evaluation" / "history.json"),
                            ("regression", self.home.root / "regression")):
            n = len(list(path.glob("*.json"))) if path.is_dir() else int(path.exists())
            bits.append(f"{label}={n}")
        return Finding("benchmarks", "ok", "runs on record: " + ", ".join(bits),
                       detail=["run one: rad benchmark bank --sample 20 | rad benchmark long | "
                               "rad regression --quick"])

    def c_sandbox(self) -> Finding:
        """Workspace jail + the non-overridable hard layer (sudo, keys, private hosts)."""
        from rad.policy import HARD_DENY, Policy
        from rad.sandbox import Sandbox
        pol = Policy(self.home)
        sudo = pol.decide("shell", "sudo id", auto=True, tool="run_shell")
        if sudo.effect != HARD_DENY:
            return Finding("sandbox", "fail",
                           f"hard layer did not refuse sudo (got {sudo.effect})",
                           detail=["hard denials are code, not config — this is a defect"])
        keys = pol.decide("fs.read", str(self.home.root / "keys"), auto=True,
                          path=self.home.root / "keys", tool="read_file")
        sb = Sandbox(self.home)
        ws = sb.workspace
        jail = "on" if sb.jail else "off"
        if keys.effect != HARD_DENY:
            return Finding("sandbox", "warn",
                           f"workspace jail {jail} at {ws}; keys path was not hard-denied ({keys.effect})",
                           detail=["`rad policy test` and `rad security` show the hard layer"])
        return Finding("sandbox", "ok",
                       f"hard layer active; workspace jail {jail} at {ws}")


STATUS_LABEL = {"ok": "READY", "warn": "WARNING", "optional": "OPTIONAL", "fail": "ERROR"}


def render(findings: List[Finding]) -> str:
    from rad.ui import col
    colour = {"ok": col.green, "warn": col.yellow, "optional": col.cyan, "fail": col.red}
    lines = []
    for f in findings:
        paint = colour.get(f.status, col.dim)
        label = STATUS_LABEL.get(f.status, f.status.upper())
        tag = col.dim(" (fixed)") if f.fixed else ""
        lines.append(f"  {paint(label):<8} {f.check:<14} {f.message}{tag}")
        for d in f.detail[:8]:
            lines.append(f"        {col.dim(d)}")
    n = {s: sum(1 for f in findings if f.status == s) for s in ("ok", "warn", "optional", "fail")}
    lines.append(f"  {n['ok']} READY · {n['warn']} WARNING · {n['optional']} OPTIONAL · {n['fail']} ERROR")
    if n["fail"]:
        lines.append(col.red("  verdict: ERROR — RAD is not ready until the ERROR lines are fixed"))
    elif n["warn"]:
        lines.append(col.yellow("  verdict: WARNING — RAD runs, but something needs attention"))
    else:
        extra = col.dim(" — optional capabilities missing; core still works") if n["optional"] else ""
        lines.append(col.green("  verdict: READY") + extra)
    return "\n".join(lines)
