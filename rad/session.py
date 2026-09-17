"""The brain loop — DNA (who Rad is) + Memory (what it knows) + Tools (what it can do).

Working memory is the conversation itself. Every turn:
  1. recall relevant long-term memories → inject into context
  2. think (provider routing with tools, auto-fallback)
  3. execute any tools it asks for (confirm-gated)
  4. log the turn to short-term memory
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

from rad import mcp
from rad.dna import Evolver
from rad.home import RadHome
from rad.memory import Memory
from rad.router import RouterState
from rad.tools import TOOLS, TOOL_PROTOCOL_NOTE, ToolCtx, run_tool
from rad.ui import ask, col, fail, info, ok, warn

MAX_WORKING = 24          # messages kept in working memory
TOOL_LINE = re.compile(r'^\s*TOOL:\s*(\{.*\})\s*$', re.S)


class Session:
    def __init__(self, home: RadHome, auto: bool = False, voice: bool = False) -> None:
        self.home = home
        self.auto = auto
        self.voice = voice
        self.router = RouterState(home)
        self.mem = Memory(home)
        self.dna = Evolver(home)
        self.ctx = ToolCtx(home=home, router=self.router, auto=auto, confirm=ask,
                           mcp_call=lambda s, t, a: mcp.call(home, s, t, a))
        self.working: List[Dict[str, Any]] = []
        self.turns = 0
        self._last_user = ""
        self.last_provider = ""

    def _last_provider_hint(self) -> str:
        return self.last_provider or "…"

    # ------------------------------------------------------------ context
    def _all_tools(self) -> List[Dict[str, Any]]:
        return TOOLS + mcp.skills_tools_schema(self.home)

    def _system(self) -> str:
        extra_parts = [
            f"Today: {time.strftime('%Y-%m-%d %A %H:%M %Z')}".strip(),
            f"Workspace (where your hands work): {self.home.workspace()}",
            TOOL_PROTOCOL_NOTE,
        ]
        if self._last_user:
            memories = self.mem.recall(self._last_user, k=self.home.cfg.get("memory_k", 5))
            block = self.mem.format_for_prompt(memories)
            if block:
                extra_parts.append(block)
        connected = self.home.skills()
        if connected:
            names = ", ".join(f"{n} ({len(e.get('tools', []))} tools)" for n, e in connected.items())
            extra_parts.append(f"Connected skill plugins: {names}")
        return self.dna.system_prompt(extra="\n\n".join(extra_parts))

    def _trim(self) -> None:
        if len(self.working) > MAX_WORKING:
            cut = self.working[-MAX_WORKING + 1:]
            if cut and cut[0].get("role") != "user":
                cut = cut[1:]
            self.working = cut

    # ------------------------------------------------------------ think
    def think(self, user_text: str) -> str:
        self.turns += 1
        self._last_user = user_text
        self.mem.session_log("user", user_text)
        self.working.append({"role": "user", "content": user_text})
        self._trim()

        messages = [{"role": "system", "content": self._system()}] + self.working
        tools = self._all_tools()
        final_text = ""
        for _round in range(int(self.home.cfg.get("max_tool_rounds", 8))):
            res = self.router.chat(messages, tools=tools, stream_cb=print_live)
            self.last_provider = res.provider
            text = res.text
            messages = messages[:-1]  # drop the user msg we're about to re-append as assistant

            # parse text-protocol tool calls (for non-native-tool models)
            tool_reqs: List[Dict[str, Any]] = list(res.tool_calls)
            m = TOOL_LINE.search(text or "")
            if m and not tool_reqs:
                try:
                    d = json.loads(m.group(1))
                    tool_reqs.append({"id": f"tp-{self.turns}", "name": d.get("name", ""),
                                      "arguments": d.get("args", {})})
                except Exception:
                    pass

            if tool_reqs:
                assistant_msg: Dict[str, Any] = {"role": "assistant", "content": text or "",
                                                 "tool_calls": tool_reqs}
                self.working.append(assistant_msg)
                for tc in tool_reqs:
                    name, args = tc["name"], tc.get("arguments", {})
                    print(col.magenta(f"  ⚙ {name} {json.dumps(args, ensure_ascii=False)[:160]}"))
                    out = run_tool(name, args, self.ctx)
                    out = out[:20000]
                    self.working.append({"role": "tool", "tool_call_id": tc.get("id", ""),
                                         "name": name, "content": out})
                self._trim()
                messages = [{"role": "system", "content": self._system()}] + self.working
                continue
            final_text = text or final_text
            break

        final_text = final_text.strip()
        if final_text:
            self.working.append({"role": "assistant", "content": final_text})
            self._trim()
        self.mem.session_log("rad", final_text or "(tool actions only)")
        return final_text

    # ------------------------------------------------------------ session close
    def close(self) -> None:
        if self.turns >= 2:
            first_user = next((m["content"] for m in self.working if m.get("role") == "user"), "")
            summary = (f"session of {self.turns} turns. started with: {first_user[:300]}")
            self.mem.session_log("session", summary)
        if self.turns >= 3:
            last = self.working[-1].get("content", "") if self.working else ""
            self.dna.add_lesson(f"recent session ended: {str(last)[:200]}")
        info(f"  — session saved to short-term memory ({self.turns} turns) —")


def print_live(chunk: str) -> None:
    print(chunk, end="", flush=True)


# ------------------------------------------------------------ REPL

SLASH_HELP = """
  /help               this help
  /good | /bad        feedback → feeds the Evolver
  /remember <text>    pin a fact into long-term memory
  /recall <query>     search long-term memory
  /evolve <direction> tell Rad how to evolve right now
  /use <provider>     pin a provider (also: /free = free-lock on)
  /free | /free-off   free-lock on/off
  /auto | /auto-off   hands act without confirmation on/off
  /cost               paid spend so far
  /sleep              consolidate memory now
  /dna                show current DNA
  /skills             list connected plugins
  /exit               leave
""".strip()


def repl(home: RadHome, auto: bool = False, voice: bool = False) -> None:
    from rad import __version__
    from rad.ui import print_banner
    print_banner(__version__)
    s = Session(home, auto=auto, voice=voice)

    # startup status line
    chain = s.router.build_chain()
    if chain:
        names = " → ".join(f"{e.spec.name}[{e.spec.tier}]" for e in chain[:5])
        info(f"  brain chain: {names}")
    else:
        warn("no brain available yet — add a key or start a local engine; memory/voice still work")

    if voice:
        from rad import voice as V
        note = V.speak("Hey, I'm Rad. Your voice is on — talk, or type. Empty line means: listen to you.", home)
        if note:
            print(col.dim(note))

    while True:
        try:
            if voice:
                prompt = col.cyan("\nrad> ") + col.dim("(type, or Enter = mic)")
            else:
                prompt = col.cyan("\nrad> ")
            line = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            if voice:
                from rad import voice as V
                heard = V.listen(home, seconds=12)
                if heard:
                    line = heard
                    print(col.dim(f"  (heard: {heard})"))
                else:
                    continue
            else:
                continue
        if line in ("/exit", "/quit", "exit", "quit"):
            break
        if line == "/help":
            print(SLASH_HELP)
            continue
        if line in ("/good", "/bad"):
            s.dna.add_feedback("good" if line == "/good" else "bad")
            ok("noted — the Evolver will use this")
            continue
        if line.startswith("/remember "):
            e = s.mem.add("semantic", line[len("/remember "):].strip(), tags=["user-pinned"])
            ok("remembered" if e else "already in memory")
            continue
        if line.startswith("/recall "):
            found = s.mem.recall(line[len("/recall "):].strip(), k=8)
            if not found:
                info("  nothing in memory matches")
            for e in found:
                print(f"  [{e.layer}] {col.dim(f's={e.strength:.2f}')} {e.text[:140]}")
            continue
        if line.startswith("/evolve "):
            direction = line[len("/evolve "):].strip()
            try:
                def _llm(prompt: str) -> str:
                    return s.router.chat([{"role": "user", "content": prompt}]).text
                has_brain = bool(s.router.build_chain())
                dna = s.dna.evolve(direction, llm=_llm if has_brain else None)
                if not has_brain:
                    info("  (no brain online — deterministic evolution)")
                ok(f"evolved → generation {dna['generation']}")
            except Exception as e:
                fail(str(e))
            continue
        if line.startswith("/use "):
            home.update(force_provider=line[len("/use "):].strip())
            ok(f"pinned provider: {home.cfg['force_provider']} (config saved; restart rad to apply)")
            continue
        if line == "/free":
            home.update(free_lock=True)
            ok("free-lock ON — paid providers are now impossible")
            continue
        if line == "/free-off":
            home.update(free_lock=False)
            ok("free-lock OFF")
            continue
        if line == "/auto":
            s.auto = True
            home.update(auto=True)
            ok("auto mode ON — hands act without confirmation")
            continue
        if line == "/auto-off":
            s.auto = False
            home.update(auto=False)
            ok("auto mode OFF")
            continue
        if line == "/cost":
            print(s.router.cost_report())
            continue
        if line == "/sleep":
            from rad.sleep import run_sleep
            report = run_sleep(home, s.router)
            ok(f"sleep done: +{report['added']} long-term, {report['faded']} faded, {report['archived']} archived")
            continue
        if line == "/dna":
            print(s.dna.show())
            continue
        if line == "/skills":
            reg = home.skills()
            if not reg:
                info("  no skills connected — `rad connect <link>`")
            for n, e in reg.items():
                print(f"  • {n}  {col.dim(e.get('transport', ''))}  {len(e.get('tools', []))} tools")
            continue

        # normal turn
        print(col.dim(f"  rad [{s._last_provider_hint()}]"), end="", flush=True)
        try:
            reply = s.think(line)
            print()
        except Exception as e:
            fail(f"brain unavailable: {e}")
            continue
        if voice and reply:
            from rad import voice as V
            note = V.speak(reply, home)
            if note:
                print(col.dim(note))

    s.close()
