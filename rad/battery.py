"""The Capability Battery — is Rad smarter? Now it's a number, not a vibe.

A built-in, deterministic, zero-dependency task bank with exact graders.
Works offline, on any machine, against ANY brain through the provider socket
(local engine, free tier, paid, or a staged weight adapter).

Categories: math · logic · code-reasoning · tool-use · json · summarize · style · retrieval · router
Scores: 0-100, saved to history, compared run over run.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from rad.home import RadHome

# ------------------------------------------------------------- graders

def _first_number(text: str) -> Optional[float]:
    m = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m[-1])
    except Exception:
        return None


def g_number(expected: float, tol: float = 1e-6):
    def check(text: str) -> Tuple[float, str]:
        got = _first_number(text)
        if got is None:
            return 0.0, "no number found"
        return (1.0 if abs(got - expected) <= tol else 0.0, f"got {got}, want {expected}")
    return check


def g_contains(*needles: str, all_of: bool = False):
    def check(text: str) -> Tuple[float, str]:
        low = text.lower()
        hits = [n for n in needles if n.lower() in low]
        if not hits:
            return 0.0, "missing: " + "/".join(needles)
        if all_of:
            return (1.0 if len(hits) == len(needles) else 0.0, f"hits {hits}")
        return 1.0, f"hit: {hits[0]}"
    return check


def g_words_max(n: int, must_contain: Optional[str] = None):
    def check(text: str) -> Tuple[float, str]:
        words = [w for w in re.findall(r"[A-Za-z']+", text)]
        if not words:
            return 0.0, "empty"
        score = 1.0 if len(words) <= n else max(0.0, 1.0 - (len(words) - n) / n)
        note = f"{len(words)} words (max {n})"
        if must_contain and must_contain.lower() not in text.lower():
            score *= 0.5
            note += f"; missing '{must_contain}'"
        return score, note
    return check


def g_words_exact(n: int):
    def check(text: str) -> Tuple[float, str]:
        words = [w for w in re.findall(r"[A-Za-z0-9']+", text)]
        return (1.0 if len(words) == n else 0.0, f"{len(words)} words, want exactly {n}")
    return check


def g_json_keys(*keys: str):
    def check(text: str) -> Tuple[float, str]:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return 0.0, "no JSON object"
        try:
            d = json.loads(m.group(0))
        except Exception:
            return 0.0, "invalid JSON"
        missing = [k for k in keys if k not in d]
        return (0.0 if missing else 1.0, f"missing {missing}" if missing else "keys ok")
    return check


def g_json_array_sum(n: int, total: float):
    def check(text: str) -> Tuple[float, str]:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return 0.0, "no JSON array"
        try:
            a = json.loads(m.group(0))
        except Exception:
            return 0.0, "invalid JSON"
        if not isinstance(a, list) or len(a) != n:
            return 0.0, f"length {len(a) if isinstance(a, list) else '?'}, want {n}"
        s = sum(x for x in a if isinstance(x, (int, float)))
        return (1.0 if abs(s - total) < 1e-6 else 0.0, f"sum {s}, want {total}")
    return check


def g_tool_call(tool: str, arg_key: Optional[str] = None, arg_contains: Optional[str] = None):
    def check(text: str) -> Tuple[float, str]:
        low = text.lower()
        if tool.lower() not in low:
            return 0.0, f"no call to {tool}"
        score = 1.0
        note = f"calls {tool}"
        if arg_key or arg_contains:
            m = re.search(r"\{.*\}", text, re.S)
            if not m:
                return 0.5, f"{tool} called but no JSON args"
            try:
                args = json.loads(m.group(0))
            except Exception:
                args = {}
            # args may be nested under "args"
            if "args" in args and isinstance(args["args"], dict):
                args = args["args"]
            flat = json.dumps(args).lower()
            if arg_key and arg_key.lower() not in flat:
                score = 0.5
                note += f"; missing arg '{arg_key}'"
            if arg_contains and arg_contains.lower() not in flat:
                score = 0.5
                note += f"; arg missing '{arg_contains}'"
        return score, note
    return check


# ------------------------------------------------------------- task bank

def _tasks() -> List[Dict[str, Any]]:
    T = []

    def add(tid, cat, prompt, checker, system="Answer with only the final answer. No explanations."):
        T.append({"id": tid, "category": cat, "prompt": prompt, "system": system, "check": checker})

    # math
    add("m1", "math", "What is 17 × 23?", g_number(391))
    add("m2", "math", "What is 15% of 240?", g_number(36))
    add("m3", "math", "A train travels 60 km/h for 2.5 hours. How many kilometers does it cover?", g_number(150))
    add("m4", "math", "Solve 3x + 7 = 22. What is x?", g_number(5))
    add("m5", "math", "What is the sum of the first 10 positive integers?", g_number(55))

    # logic
    add("l1", "logic", "What number comes next in the sequence: 2, 6, 12, 20, 30, ?", g_number(42))
    add("l2", "logic", "All Bloops are Razzies. All Razzies are Lazzies. Are all Bloops necessarily Lazzies? Answer yes or no.",
        g_contains("yes"))
    add("l3", "logic", "Five letters are ordered D A B C E, where A is left of B, C is right of B, D is left of A, E is right of C. "
        "Confirm the full left-to-right order.", g_contains("d a b c e", "dabc e", "d a b c e"))

    # code-reasoning (exact output, no execution needed)
    add("c1", "code", "Sum all prime numbers less than 20. Give the number only.", g_number(58))
    add("c2", "code", "How many integers from 1 to 100 (inclusive) are divisible by 7? Number only.", g_number(14))

    # tool use (text protocol — works for native-tool and plain models)
    TOOL_SYS = ("You have these tools: get_weather(city), search_web(query), run_shell(command). "
                "To use a tool, output exactly one line: TOOL: {\"name\": \"<tool>\", \"args\": {…}} "
                "Use the appropriate tool for the request.")
    add("t1", "tool", "What is the weather in Tokyo?", g_tool_call("get_weather", "city", "tokyo"), system=TOOL_SYS)
    add("t2", "tool", "Search the web for the latest news about Mars.", g_tool_call("search_web", "query", "mars"), system=TOOL_SYS)
    add("t3", "tool", "List the files in /tmp using the shell.", g_tool_call("run_shell", "command", "ls"), system=TOOL_SYS)

    # json discipline
    add("j1", "json", 'Reply with ONLY this JSON object: {"name":"rad","age":1}',
        g_json_keys("name", "age"), system="Output raw JSON only.")
    add("j2", "json", "Reply with ONLY a JSON array of exactly 3 numbers that sum to 6.",
        g_json_array_sum(3, 6), system="Output raw JSON only.")

    # summarize
    add("s1", "summarize",
        "Summarize in at most 12 words: The solar eclipse of this year attracted millions of observers across four continents. "
        "Researchers used the total phase to study the sun's outer atmosphere, and communities celebrated with local festivals. "
        "Safety glasses were sold out in many towns days before the event.",
        g_words_max(12, must_contain="solar"),
        system="You are a careful editor. Follow word limits strictly.")
    add("s2", "summarize", "In one sentence of at most 15 words, explain why the sky is blue.",
        g_words_max(15, must_contain="scatter"), system="You are a careful editor. Follow word limits strictly.")

    # style
    add("y1", "style", "Introduce yourself in exactly 5 words.", g_words_exact(5),
        system="Be extremely concise.")

    # retrieval (P0 bank 1 — hybrid retriever contract: FTS5 + vector stub observability)
    add("r1", "retrieval", "Given the memory 'Alice works at Acme' and query 'Where does Alice work?', answer with Acme.",
        g_contains("acme"), system="Answer with only the final answer. No explanations.")
    add("r2", "retrieval", "Given FTS5 lexical match on 'lives in Berlin' vs 'Berlin', confirm the location is Berlin.",
        g_contains("berlin"), system="Answer with only the final answer. No explanations.")

    # router (P0 bank 2 — Router Gateway observability: health + cost + latency)
    add("p1", "router", 'Reply with ONLY JSON {"health":"healthy","latency_ms":12,"cost_per_1k":0.0003} (choose plausible healthy values).',
        g_json_keys("health", "latency_ms", "cost_per_1k"), system="Output raw JSON only.")
    add("p2", "router", "Which provider tier is cheapest: local, free, or paid? Answer in one word.",
        g_contains("local"), system="Answer with only the final answer. No explanations.")

    return T


# ------------------------------------------------------------- runner

class Benchmark:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.history_path = home.root / "benchmarks" / "history.json"

    def tasks(self, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        all_t = _tasks()
        if not categories:
            return all_t
        return [t for t in all_t if t["category"] in categories]

    def run(self, caller: Callable[[str, str], str], label: str, provider: str = "?",
            model: str = "?", categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """caller(system_prompt, user_prompt) -> text."""
        results = []
        for t in self.tasks(categories):
            try:
                text = caller(t["system"], t["prompt"])
                score, note = t["check"](text or "")
            except Exception as e:
                score, note = 0.0, f"error: {str(e)[:80]}"
            results.append({"id": t["id"], "category": t["category"], "score": round(score, 3), "note": note})
        by_cat: Dict[str, List[float]] = {}
        for r in results:
            by_cat.setdefault(r["category"], []).append(r["score"])
        cats = {c: round(100.0 * sum(v) / len(v), 1) for c, v in by_cat.items()}
        total = round(100.0 * sum(r["score"] for r in results) / len(results), 1) if results else 0.0
        report = {"label": label, "provider": provider, "model": model,
                  "score": total, "categories": cats, "at": time.time(), "tasks": results}
        self._save(report)
        return report

    def _save(self, report: Dict[str, Any]) -> None:
        hist = self.history()
        hist.append(report)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(json.dumps(hist[-200:], indent=2, ensure_ascii=False))

    def history(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.history_path.read_text())
        except Exception:
            return []

    def compare(self, n: int = 5) -> str:
        from rad.ui import col
        hist = self.history()[-n:]
        if not hist:
            return "  no benchmark runs yet — `rad benchmark`"
        out = []
        for h in hist:
            cats = "  ".join(f"{c} {v}" for c, v in sorted(h.get("categories", {}).items()))
            when = time.strftime("%m-%d %H:%M", time.localtime(h["at"]))
            score = col.cyan(f"{h['score']:>5}")
            out.append(f"  {score}  {h['label']:<24} {when}  {col.dim(cats)}")
        if len(hist) >= 2:
            delta = round(hist[-1]["score"] - hist[-2]["score"], 1)
            arrow = col.green("▲") if delta > 0 else (col.red("▼") if delta < 0 else "·")
            out.append(f"  {arrow} last change: {delta:+} pts")
        return "\n".join(out)


def build_caller(home: RadHome, provider: Optional[str] = None, model: Optional[str] = None,
                 temperature: float = 0.2):
    """A (system, user) -> text caller routed through Rad's provider socket,
    pinned to a specific provider/model for EVERY call (used for A/B brain battles).

    The pin is applied per call and restored afterwards, so callers built for
    different brains can be interleaved without leaking config."""
    from rad.router import RouterState
    r = RouterState(home)

    def caller(system: str, user: str) -> str:
        old_force = home.cfg.get("force_provider")
        old_model = home.cfg.get("model")
        if provider:
            home.cfg["force_provider"] = provider
        if model:
            home.cfg["model"] = model
        try:
            msgs = ([{"role": "system", "content": system}] if system else [])
            msgs.append({"role": "user", "content": user})
            return r.chat(msgs, stream_cb=None, temperature=temperature).text
        finally:
            home.cfg["force_provider"] = old_force
            home.cfg["model"] = old_model

    return caller


class CapabilityBattery(Benchmark):
    def run(self, provider: str = "?", model: str = "?", categories: Optional[List[str]] = None,
            caller: Optional[Callable[[str, str], str]] = None, label: str = "run",
            temperature: float = 0.2, **kwargs) -> Dict[str, Any]:
        if caller is None:
            caller = build_caller(self.home, provider=None if provider == "?" else provider,
                                  model=None if model == "?" else model,
                                  temperature=temperature)
        return super().run(caller=caller, label=label, provider=provider, model=model, categories=categories)
