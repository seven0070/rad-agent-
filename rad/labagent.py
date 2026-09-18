"""Deterministic stand-in for the model, used by the benchmark lab and the regression harness.

A real LLM is not required to exercise the *control plane*: planning, task graphs, the
executor pipeline, budgets, observations, verification, recovery and checkpoints are all
deterministic code paths. `OfflineAgent` replays a script of `(tool, args)` actions through
the **real** tool runner — files really hit disk, checks really run, recovery really fires.

It also injects faults on purpose (`faults=`), which is how the recovery suite proves that
RAD retries, switches approach, or escalates honestly instead of silently failing:

    faults = {"tool": "write_file", "times": 1}     # first write_file errors
    faults = {"network": 1}                         # first web call errors
    faults = {"model": 1}                           # first think() raises
    faults = {"invalid_output": 1}                  # first reply is garbage (verification must catch)
    faults = {"permission": 1}                      # a policy-denied action is attempted

Benchmarks that need *model quality* (not runtime behaviour) use `rad.battery`
against a real provider; these banks measure the runtime.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from rad.tools import ToolCtx, run_tool

NETWORK_TOOLS = {"web_search", "fetch_page", "see_image", "verify_url", "browser"}


class OfflineAgent:
    """Session-compatible deterministic agent. One shared script per scenario."""

    script: List[Any] = []
    faults: Dict[str, Any] = {}
    prompts: List[str] = []
    _lock = threading.Lock()
    _calls: Dict[str, int] = {}
    _model_failures = 0

    def __init__(self, home, auto: bool = False, **kw: Any) -> None:
        self.home = home
        self.auto = auto
        self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
        self.tool_runner = self._runner            # direct use (no control plane)
        self.agent_tool_runner = self._runner      # used *inside* the Executor pipeline
        self.turns = 0
        self.last_provider = "offline"
        self.last_usage: Dict[str, Any] = {}
        self.requirements = None
        self.memory_scope = None

    # ------------------------------------------------------------------ tools
    def _runner(self, name: str, args: Dict[str, Any], ctx: Any = None) -> str:
        ctx = ctx or self.ctx
        fault = self._take_fault(name)
        if fault is not None:
            return fault
        try:
            return run_tool(name, args, ctx)
        except Exception as e:                       # a tool crash is an observation, not a crash
            return f"tool error: {type(e).__name__}: {e}"

    def _take_fault(self, name: str) -> Optional[str]:
        with self._lock:
            f = type(self).faults or {}
            if f.get("tool") == name and int(f.get("times", 1)) > 0:
                f["times"] = int(f.get("times", 1)) - 1
                return (f"tool error: {f.get('error', 'simulated tool failure')} "
                        f"[injected fault for {name}]")
            left = int(f.get("network", 0) or 0)
            if left > 0 and name in NETWORK_TOOLS:
                f["network"] = left - 1
                return "tool error: URLError: simulated network failure [injected fault]"
            return None

    # ------------------------------------------------------------------ thinking
    def think(self, prompt: str) -> str:
        type(self).prompts.append(prompt[:2000])
        self.turns += 1
        with self._lock:
            f = type(self).faults or {}
            if int(f.get("model", 0) or 0) > 0:
                f["model"] = int(f.get("model", 0)) - 1
                raise RuntimeError("ProviderError: simulated provider failure [injected fault]")
            if not type(self).script:
                return "DONE: script exhausted"
            step = type(self).script.pop(0)
        if isinstance(step, Exception):
            raise step
        actions, reply = step
        if isinstance(actions, str):                 # raw reply only (no tools)
            actions, reply = [], actions
        errors: List[str] = []
        with self._lock:
            invalid = int((type(self).faults or {}).get("invalid_output", 0) or 0)
            if invalid > 0:
                type(self).faults["invalid_output"] = invalid - 1
                return "I think we are basically done here."      # no DONE, no tool work
        for tool, args in actions:
            runner = self.tool_runner
            if tool == "__recall_to_file__":
                # the *memory system* produces the content — the script cannot fake it
                out = self.tool_runner("recall", {"query": args.get("query", "")}, self.ctx)
                self.tool_runner("write_file", {"path": args.get("path", "recall.txt"),
                                                "content": out}, self.ctx)
                continue
            if tool == "__sleep__":
                from rad.sleep import run_sleep
                try:
                    run_sleep(self.home, None)
                except Exception as e:
                    errors.append(f"sleep: {e}")
                continue
            out = runner(tool, args, self.ctx)
            if out.lower().startswith(("tool error", "denied", "blocked", "declined")):
                errors.append(f"{tool}: {out[:200]}")
        if errors:
            reply = (reply + "\n\nTOOL ERRORS ENCOUNTERED:\n" + "\n".join(errors)).strip()
        return reply

    def close(self) -> None:
        pass


def make_agent_class(script: List[Any], faults: Optional[Dict[str, Any]] = None) -> type:
    """Build a fresh OfflineAgent subclass with its own script/fault counters."""
    return type("OfflineAgentInstance", (OfflineAgent,), {
        "script": list(script), "faults": dict(faults or {}), "prompts": [],
    })


def plan_llm(plan: Optional[Dict[str, Any]], replan: Optional[Dict[str, Any]] = None) -> Callable[[str], str]:
    """LLM callable that returns a fixed plan (and optional replan) as JSON."""
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan or {"tasks": []})
        if "replanning part" in prompt or "Propose 1-5 NEW tasks" in prompt:
            return json.dumps(replan or {"tasks": []})
        if "strict verifier" in prompt:
            return json.dumps({"pass": True, "reason": "no objection"})
        return "YES"
    return llm


def controller_factory(script: List[Any], plan: Optional[Dict[str, Any]] = None,
                       faults: Optional[Dict[str, Any]] = None,
                       replan: Optional[Dict[str, Any]] = None):
    """A Lab-compatible controller factory: real tools, deterministic model."""
    def make(home):
        from rad.control.controller import Controller
        return Controller(home, session_factory=make_agent_class(script, faults),
                          llm=plan_llm(plan, replan), quiet=True)
    return make
