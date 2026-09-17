"""Agent runtime — registry, lifecycle, capabilities, budgets and a shared blackboard.

An *agent* here is a scoped worker: a role prompt + a model route + an explicit capability
set + a budget. Agents run the existing brain loop (`Session`) but through a `ToolCtx`
that is restricted to what they were granted, so a `researcher` can read and browse but
cannot write or run shell, and a `reviewer` can only read.

    registry.json  ─ static agent definitions (editable)
    agents/runs/   ─ one JSON per agent run (status, budget usage, outputs, provenance)
    blackboard     ─ per-objective shared notes with author + evidence links

Nothing here replaces the control plane: the Controller stays the only thing that
decides whether work is done.
"""
from __future__ import annotations

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.home import RadHome, _write_json

# ---------------------------------------------------------------- capabilities

from rad.policy import CAP_MCP, CAP_READ, CAP_SHELL, CAP_SPAWN, CAP_VISION, CAP_WEB, CAP_WRITE  # noqa: E402
ALL_CAPS = (CAP_READ, CAP_WRITE, CAP_SHELL, CAP_WEB, CAP_VISION, CAP_SPAWN, CAP_MCP)

TOOL_CAP = {
    "read_file": CAP_READ, "list_dir": CAP_READ,
    "write_file": CAP_WRITE,
    "run_shell": CAP_SHELL,
    "web_search": CAP_WEB, "fetch_page": CAP_WEB,
    "see_image": CAP_VISION,
    "spawn_agents": CAP_SPAWN,
}


def cap_for_tool(name: str) -> str:
    if name.startswith("mcp__"):
        return CAP_MCP
    return TOOL_CAP.get(name, CAP_SHELL)   # unknown tools are treated as most dangerous


BUILTIN_AGENTS: Dict[str, Dict[str, Any]] = {
    "planner":    {"caps": [CAP_READ, CAP_WEB],
                   "prompt": "You decompose problems into ordered, checkable steps and name risks and dependencies."},
    "researcher": {"caps": [CAP_READ, CAP_WEB],
                   "prompt": "You gather evidence. Cite the URL or file for every claim. Separate fact from inference."},
    "coder":      {"caps": [CAP_READ, CAP_WRITE, CAP_SHELL],
                   "prompt": "You write code that runs. Simple working solutions over clever ones. Run it to prove it."},
    "tester":     {"caps": [CAP_READ, CAP_SHELL],
                   "prompt": "You try to break things. Run the tests/commands and report exact output, pass or fail."},
    "reviewer":   {"caps": [CAP_READ],
                   "prompt": "You review skeptically: bugs, edge cases, security, unmet requirements. Never rubber-stamp."},
    "writer":     {"caps": [CAP_READ, CAP_WRITE],
                   "prompt": "You write clear, concise prose for the intended audience. No fluff."},
    "analyst":    {"caps": [CAP_READ],
                   "prompt": "You compare, quantify and summarise evidence into a decision. Show your reasoning."},
    "security":   {"caps": [CAP_READ],
                   "prompt": "You look for credential leaks, injection, unsafe commands and permission problems."},
}


@dataclass
class AgentSpec:
    id: str
    role: str
    prompt: str
    caps: List[str]
    model: Optional[str] = None
    provider: Optional[str] = None
    budget_tool_calls: int = 20
    budget_seconds: int = 300
    memory_scope: str = "shared"      # shared | isolated
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRun:
    id: str
    agent: str
    role: str
    objective_id: str
    task_id: str
    input: str
    status: str = "running"           # running | done | failed | budget | denied
    output: str = ""
    tool_calls: int = 0
    denied: List[str] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    finished: Optional[float] = None
    provider: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BudgetExceeded(Exception):
    pass


class CapabilityDenied(Exception):
    pass


# ---------------------------------------------------------------- registry

class AgentRegistry:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "agents"
        self.dir.mkdir(exist_ok=True)
        (self.dir / "runs").mkdir(exist_ok=True)
        self.path = self.dir / "registry.json"

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def all(self) -> Dict[str, AgentSpec]:
        out: Dict[str, AgentSpec] = {}
        for role, b in BUILTIN_AGENTS.items():
            out[role] = AgentSpec(id=role, role=role, prompt=b["prompt"], caps=list(b["caps"]))
        for aid, d in self._load().items():
            base = out.get(aid)
            merged = {**(base.to_dict() if base else {"id": aid, "role": aid, "prompt": "", "caps": [CAP_READ]}), **d}
            out[aid] = AgentSpec(**{k: merged[k] for k in AgentSpec.__dataclass_fields__ if k in merged})
        return out

    def get(self, aid: str) -> Optional[AgentSpec]:
        return self.all().get(aid)

    def define(self, aid: str, **fields: Any) -> AgentSpec:
        d = self._load()
        d[aid] = {**d.get(aid, {}), **{k: v for k, v in fields.items() if v is not None}}
        if "caps" in d[aid]:
            bad = [c for c in d[aid]["caps"] if c not in ALL_CAPS]
            if bad:
                raise ValueError(f"unknown capabilities {bad}; valid: {', '.join(ALL_CAPS)}")
        _write_json(self.path, d)
        return self.get(aid)  # type: ignore[return-value]

    def remove(self, aid: str) -> bool:
        d = self._load()
        if aid in d:
            del d[aid]
            _write_json(self.path, d)
            return True
        return False

    def save_run(self, run: AgentRun) -> None:
        _write_json(self.dir / "runs" / f"{run.id}.json", run.to_dict())

    def runs(self, objective_id: Optional[str] = None, n: int = 50) -> List[Dict[str, Any]]:
        out = []
        for p in sorted((self.dir / "runs").glob("*.json"), reverse=True)[:500]:
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if objective_id and d.get("objective_id") != objective_id:
                continue
            out.append(d)
            if len(out) >= n:
                break
        return out


# ---------------------------------------------------------------- blackboard

class Blackboard:
    """Shared notes between agents working on one objective. Every note has an author and
    optional evidence (observation ids / URLs). Read-mostly; appends are atomic."""

    def __init__(self, home: RadHome, scope: str) -> None:
        self.path = home.root / "agents" / "blackboard" / f"{scope}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def notes(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def post(self, author: str, text: str, kind: str = "note", evidence: Optional[List[str]] = None) -> Dict[str, Any]:
        import fcntl  # POSIX advisory lock; fine for a personal agent
        note = {"id": "n_" + uuid.uuid4().hex[:6], "author": author, "kind": kind, "text": text[:4000],
                "evidence": evidence or [], "at": time.time()}
        self.path.touch()
        with open(self.path, "r+", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
            except Exception:
                pass
            raw = f.read()
            items = json.loads(raw) if raw.strip() else []
            items.append(note)
            f.seek(0); f.truncate()
            json.dump(items, f, ensure_ascii=False, indent=1)
        return note

    def render(self, max_notes: int = 12) -> str:
        items = self.notes()[-max_notes:]
        if not items:
            return ""
        return "Shared blackboard (other agents' notes; treat as claims unless evidence is listed):\n" + \
            "\n".join(f"- [{n['author']}/{n['kind']}] {n['text'][:300]}" +
                      (f"  (evidence: {', '.join(n['evidence'][:3])})" if n["evidence"] else "")
                      for n in items)


# ---------------------------------------------------------------- runtime

class AgentRuntime:
    """Runs agents with restricted tools, budgets and a blackboard; optionally in parallel."""

    def __init__(self, home: RadHome, session_factory: Optional[Callable[..., Any]] = None,
                 auto: bool = True) -> None:
        self.home = home
        self.registry = AgentRegistry(home)
        self._session_factory = session_factory
        self.auto = auto

    def _session(self):
        if self._session_factory:
            return self._session_factory(self.home, auto=self.auto)
        from rad.session import Session
        return Session(self.home, auto=self.auto)

    def run_agent(self, agent_id: str, task: str, objective_id: str = "", task_id: str = "",
                  extra_context: str = "", blackboard: Optional[Blackboard] = None) -> AgentRun:
        spec = self.registry.get(agent_id)
        if not spec or not spec.enabled:
            raise ValueError(f"no such agent '{agent_id}'")
        run = AgentRun(id="run_" + uuid.uuid4().hex[:8], agent=spec.id, role=spec.role,
                       objective_id=objective_id, task_id=task_id, input=task)
        session = self._session()
        original = session.tool_runner
        t0 = time.time()
        ctx = getattr(session, "ctx", None)
        if ctx is not None:                      # envelope enforced again inside run_tool's policy gate
            ctx.agent_caps = list(spec.caps)
            ctx.actor = f"agent:{spec.id}"

        def guarded(name, args, ctx):
            cap = cap_for_tool(name)
            if cap not in spec.caps:
                run.denied.append(f"{name} ({cap})")
                return (f"DENIED: agent '{spec.id}' lacks capability '{cap}' for tool {name}. "
                        f"Do without it or report what you need.")
            if run.tool_calls >= spec.budget_tool_calls:
                raise BudgetExceeded(f"agent {spec.id} tool budget {spec.budget_tool_calls} exhausted")
            if time.time() - t0 > spec.budget_seconds:
                raise BudgetExceeded(f"agent {spec.id} time budget {spec.budget_seconds}s exhausted")
            run.tool_calls += 1
            out = original(name, args, ctx)
            if name in ("fetch_page", "web_search", "read_file") and not str(out).startswith(("fetch failed", "not found", "BLOCKED", "tool error")):
                run.evidence.append({"tool": name, "source": args.get("url") or args.get("query") or args.get("path", ""),
                                     "trusted": name == "read_file", "at": time.time()})
            return out

        session.tool_runner = guarded
        prompt_parts = [f"You are acting as the '{spec.role}' sub-agent. {spec.prompt}",
                        f"Capabilities granted: {', '.join(spec.caps)}. Tools outside these will be denied."]
        if blackboard:
            bb = blackboard.render()
            if bb:
                prompt_parts.append(bb)
        if extra_context:
            prompt_parts.append(extra_context)
        prompt_parts.append(f"TASK: {task}")
        prompt_parts.append("Finish with a clear final answer. If you relied on evidence, name it.")
        try:
            run.output = (session.think("\n\n".join(prompt_parts)) or "").strip()
            run.status = "done" if run.output else "failed"
            run.provider = getattr(session, "last_provider", "")
        except BudgetExceeded as e:
            run.status, run.output = "budget", str(e)
        except Exception as e:
            run.status, run.output = "failed", str(e)[:500]
        finally:
            run.finished = time.time()
            try:
                session.close()
            except Exception:
                pass
        if blackboard and run.output and run.status == "done":
            blackboard.post(spec.id, run.output[:1500], kind="result",
                            evidence=[str(e["source"])[:120] for e in run.evidence[:5]])
        self.registry.save_run(run)
        return run

    def run_parallel(self, jobs: List[Dict[str, Any]], scope: str = "", max_workers: int = 4) -> List[AgentRun]:
        """jobs: [{"agent": id, "task": str, ...}] → runs (in job order). Shares one blackboard."""
        bb = Blackboard(self.home, scope) if scope else None
        results: List[Optional[AgentRun]] = [None] * len(jobs)
        workers = min(max_workers, max(1, len(jobs))) if self.auto else 1
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="rad-agent") as pool:
            futs = {pool.submit(self.run_agent, j["agent"], j["task"], j.get("objective_id", ""),
                                j.get("task_id", ""), j.get("context", ""), bb): i for i, j in enumerate(jobs)}
            for f in as_completed(futs):
                i = futs[f]
                try:
                    results[i] = f.result()
                except Exception as e:
                    j = jobs[i]
                    results[i] = AgentRun(id="run_err", agent=j["agent"], role=j["agent"], objective_id="",
                                          task_id="", input=j["task"], status="failed", output=str(e)[:300],
                                          finished=time.time())
        return [r for r in results if r is not None]

    # ------------------------------------------------------------ review as a machine-recorded check
    def review(self, subject: str, criteria: List[str], objective_id: str = "", task_id: str = "",
               agent_id: str = "reviewer") -> Dict[str, Any]:
        """Independent read-only review. Returns {"pass": bool, "issues": [...], "run": id}.
        The reviewer may read files/run nothing — it must ground issues in what it read."""
        crit = "\n".join(f"- {c}" for c in criteria) or "- the work is complete and correct"
        task = (f"Review the following against the criteria. Read the relevant files yourself.\n"
                f"SUBJECT:\n{subject[:6000]}\n\nCRITERIA:\n{crit}\n\n"
                'Reply ONLY JSON: {"pass": true|false, "issues": ["..."], "checked": ["file or fact you verified"]}')
        run = self.run_agent(agent_id, task, objective_id, task_id)
        import re
        m = re.search(r"\{.*\}", run.output or "", re.S)
        try:
            d = json.loads(m.group(0)) if m else {}
        except Exception:
            d = {}
        return {"pass": bool(d.get("pass", False)) and run.status == "done",
                "issues": [str(x)[:200] for x in (d.get("issues") or [])][:10],
                "checked": [str(x)[:120] for x in (d.get("checked") or [])][:10],
                "run": run.id, "status": run.status, "tool_calls": run.tool_calls}
