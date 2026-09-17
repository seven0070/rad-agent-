"""Multi-agent cognition — Rad thinks in parallel.

Rad spawns specialist sub-agents (same brain socket, distinct roles grown
from the DNA), runs them on a problem, then synthesizes. Two modes:
  solo    — each agent answers independently, Rad synthesizes
  debate  — agents critique each other's answers, a judge picks the best

Backend socket: `builtin` (pure Python, any provider through the socket —
always available) and `autogen` (AutoGen agent graphs, when installed).
The brain can also delegate mid-chat via the `spawn_agents` tool.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

from rad.home import RadHome
from rad.ui import col

DEFAULT_ROLES = {
    "coder": "You are Rad's coding specialist: precise, practical, writes code that runs. "
             "You favor simple working solutions over clever ones.",
    "reviewer": "You are Rad's reviewer: skeptical, finds edge cases, bugs, and security holes. "
                "You are constructive but never rubber-stamp.",
    "planner": "You are Rad's planner: decomposes problems into ordered, checkable steps, "
               "names risks and dependencies explicitly.",
    "researcher": "You are Rad's researcher: thorough, cites sources when known, separates "
                  "fact from inference, notes uncertainty clearly.",
    "writer": "You are Rad's writer: clear, concise, audience-aware prose. No fluff.",
}

ROLE_FALLBACK = ("You are a specialist sub-agent of Rad working on one aspect of a problem. "
                 "Be precise and concrete. {role_hint}")


class Team:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "team"
        self.dir.mkdir(exist_ok=True)

    def caller_for(self, role: str, extra: str = "") -> Callable[[str], str]:
        """A sub-agent = brain socket + DNA persona + role identity."""
        from rad.battery import build_caller
        from rad.dna import Evolver
        dna = Evolver(self.home).load()
        persona = dna.get("persona", "You are Rad.")
        role_desc = DEFAULT_ROLES.get(role, ROLE_FALLBACK.format(role_hint=f"Focus: {role}"))
        system = f"{persona}\n\nYour role in this task: {role_desc}\n{extra}".strip()

        def call(user: str) -> str:
            caller = build_caller(self.home)
            return caller(system, user)
        return call

    # ------------------------------------------------------------ orchestration
    def run(self, problem: str, roles: Optional[List[str]] = None, mode: str = "solo",
            n: int = 0, tools: bool = False, objective_id: str = "") -> Dict[str, Any]:
        """tools=False → prompt-only specialists (fast, cheap, original behaviour).
        tools=True  → real scoped agents through AgentRuntime (capabilities, budgets, blackboard,
        parallel), recorded under ~/.rad/agents/runs."""
        if not roles:
            roles = ([r for r in DEFAULT_ROLES][:max(1, n)] if n > 0
                     else ["coder", "reviewer", "planner"])
        answers: List[Dict[str, Any]] = []
        if tools:
            from rad.agents import AgentRuntime
            rt = AgentRuntime(self.home, auto=bool(self.home.cfg.get("auto")))
            runs = rt.run_parallel([{"agent": r, "task": problem, "objective_id": objective_id} for r in roles],
                                   scope=objective_id or f"team-{int(time.time())}")
            for r in runs:
                answers.append({"role": r.role, "answer": (r.output or "")[:4000], "run": r.id,
                                "status": r.status, "tool_calls": r.tool_calls, "denied": r.denied})
        else:
            for role in roles:
                try:
                    text = self.caller_for(role)(problem)
                except Exception as e:
                    text = f"[agent {role} failed: {str(e)[:120]}]"
                answers.append({"role": role, "answer": text.strip()[:4000]})

        if mode == "debate":
            critique = self._debate(problem, answers)
            answers.append({"role": "debate", "answer": critique})
        synthesis = self._synthesize(problem, answers)
        result = {"problem": problem, "mode": mode, "roles": roles,
                  "answers": answers, "final": synthesis, "at": time.time()}
        self._save(result)
        return result

    def _debate(self, problem: str, answers: List[Dict[str, Any]]) -> str:
        joined = "\n\n".join(f"--- {a['role']} ---\n{a['answer']}" for a in answers)
        try:
            return self.caller_for("reviewer")(
                f"Problem: {problem}\n\n{len(answers)} specialists answered:\n\n{joined}\n\n"
                "Critique: where do they disagree, who is most likely right and why, "
                "and what is missing? Be concise.").strip()
        except Exception as e:
            return f"[debate unavailable: {str(e)[:120]}]"

    def _synthesize(self, problem: str, answers: List[Dict[str, Any]]) -> str:
        joined = "\n\n".join(f"--- {a['role']} ---\n{a['answer']}" for a in answers)
        try:
            return self.caller_for("writer")(
                f"Problem: {problem}\n\nSpecialist answers:\n\n{joined}\n\n"
                "Write the final answer: synthesize the strongest parts, drop the rest, "
                "state disagreements honestly. Do not just concatenate.").strip()
        except Exception as e:
            # no brain for synthesis → honest fallback
            return "(synthesis unavailable — raw answers above)"

    def _save(self, result: Dict[str, Any]) -> None:
        p = self.dir / f"run-{int(result['at'])}.json"
        p.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    def history(self, n: int = 10) -> List[str]:
        files = sorted(self.dir.glob("run-*.json"), reverse=True)[:n]
        out = []
        for f in files:
            try:
                d = json.loads(f.read_text())
                out.append(f"  {time.strftime('%m-%d %H:%M', time.localtime(d['at']))}  "
                           f"{d['mode']:<6} [{', '.join(d['roles'])}]  {d['problem'][:50]}")
            except Exception:
                continue
        return out or ["  no team runs yet — `rad team run <problem>`"]


# ------------------------------------------------------------ autogen backend (optional)

def autogen_available() -> bool:
    try:
        import autogen_agentchat  # noqa: F401
        return True
    except ImportError:
        return False


def run_autogen(home: RadHome, problem: str, roles: List[str]) -> Optional[str]:
    """Optional backend: real AutoGen agent graph. Returns final text or None."""
    if not autogen_available():
        return None
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.teams import RoundRobinGroupChat
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        from rad import providers as P
        from rad.router import RouterState
        r = RouterState(home)
        chain = r.build_chain()
        if not chain:
            return None
        e = chain[0]
        model_client = OpenAIChatCompletionClient(
            model=e.model or "gpt-4o-mini",
            base_url=e.spec.base_url,
            api_key=e.key or "none",
            temperature=0.4)
        agents = [AssistantAgent(
            name=role, model_client=model_client,
            system_message=DEFAULT_ROLES.get(role, ROLE_FALLBACK.format(role_hint=role)))
            for role in roles]
        team = RoundRobinGroupChat(agents, max_messages=2 * len(agents) + 1)
        res = team.run(task=problem)
        return str(getattr(res, "messages", ""))[-4000:]
    except Exception:
        return None
