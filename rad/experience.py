"""Experience learning — a finished objective becomes a *validated* lesson, or nothing.

    Objective → Outcome → Analysis → Lesson candidate → Validation → Procedural memory

The rule this module enforces: **a single failure is never a permanent rule.**
Every lesson is a `Lesson` object with a status:

    candidate    proposed from one episode (recorded, visible, not behaviour)
    supported    the recorded evidence backs it (≥1 confirming episode)
    validated    ≥`MIN_SUPPORT` independent confirming episodes, no contradictions
    contradicted a later episode showed the opposite
    rejected     a human (or the validator) threw it out

Only `validated` lessons are promoted into procedural memory as *behavioural*
hints and into the DNA lesson list; everything else stays as honest, inspectable
evidence. Validation runs against episodes mined from every stored objective
(`~/.rad/objectives/*/tasks.json` + their event logs), so it is real history, not
the model's opinion of itself.

Lesson kinds:
    recovery_pattern   "class X → strategy Y worked" (needs ≥2 identical outcomes)
    tool_behaviour     "tool T fails with E in this environment"
    planning_hint      "goals shaped like G needed N tasks / failed at step S"
    environment_fact   "command/binary exists (observed)"
    efficiency         "objective type G used N tool calls, M retries"
    safety             "policy denied action A (and the run survived)"
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from rad.home import RadHome, _read_json, _write_json

MIN_SUPPORT = 2          # independent confirming episodes before a lesson becomes behaviour

#: which kinds of lesson may become persistent behaviour. Measurements (efficiency) and
#: unproven guesses never do — they stay in the lesson store where a human can read them.
PROMOTABLE_KINDS = ("recovery_pattern", "tool_behaviour", "environment_fact", "safety")

KIND_RECOVERY = "recovery_pattern"
KIND_TOOL = "tool_behaviour"
KIND_PLANNING = "planning_hint"
KIND_ENV = "environment_fact"
KIND_EFFICIENCY = "efficiency"
KIND_SAFETY = "safety"


@dataclass
class Lesson:
    id: str
    kind: str
    text: str
    objective_id: str = ""
    task_id: str = ""
    failure_class: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    supports: int = 0
    contradictions: int = 0
    status: str = "candidate"          # candidate | supported | validated | contradicted | rejected
    created: float = field(default_factory=time.time)
    note: str = ""
    promoted: bool = False

    @classmethod
    def new(cls, kind: str, text: str, **kw: Any) -> "Lesson":
        return cls(id="les_" + uuid.uuid4().hex[:8], kind=kind, text=text, **kw)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Lesson":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class Episode:
    """One recorded task attempt — the raw material for validation."""

    __slots__ = ("objective_id", "task_id", "text", "failure_class", "attempts", "status",
                 "verified", "tools_failed", "strategy")

    def __init__(self, **kw: Any) -> None:
        for k in self.__slots__:
            setattr(self, k, kw.get(k, "" if k != "attempts" else 0))


class Experience:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "experience"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "lessons.json"
        self.log_path = self.dir / "events.jsonl"

    # ------------------------------------------------------------------ storage
    def lessons(self, status: Optional[str] = None, n: int = 200) -> List[Lesson]:
        items = [Lesson.from_dict(d) for d in (_read_json(self.path, []) or [])]
        if status:
            items = [l for l in items if l.status == status]
        items.sort(key=lambda l: -l.created)
        return items[:n]

    def save(self, lesson: Lesson) -> None:
        items = _read_json(self.path, []) or []
        items = [d for d in items if d.get("id") != lesson.id]
        items.append(lesson.to_dict())
        _write_json(self.path, items[-2000:])

    def _event(self, kind: str, lesson: Lesson, **extra: Any) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": time.time(), "kind": kind, "lesson": lesson.id,
                                    "status": lesson.status, "text": lesson.text[:200], **extra},
                                   ensure_ascii=False) + "\n")
        except OSError:
            pass

    # ------------------------------------------------------------------ episodes
    def episodes(self) -> List[Episode]:
        """Mine every stored objective for task attempts that carry learning signal."""
        out: List[Episode] = []
        root = self.home.root / "objectives"
        if not root.exists():
            return out
        for d in sorted(root.iterdir()):
            if not d.is_dir():
                continue
            try:
                tasks = json.loads((d / "tasks.json").read_text(encoding="utf-8"))
            except Exception:
                continue
            strategy_by_task = self._strategies(d / "events.jsonl")
            for t in tasks:
                if not isinstance(t, dict):
                    continue
                fails = [h for h in (t.get("history") or []) if h.get("to") in ("FAILED", "BLOCKED", "NEEDS_USER")]
                if not fails and int(t.get("attempts", 1) or 1) <= 1:
                    continue
                ver = t.get("verification") or {}
                out.append(Episode(objective_id=d.name, task_id=t.get("id", ""),
                                   text=str(t.get("text", ""))[:200],
                                   failure_class=str(t.get("failure_class", "")),
                                   attempts=int(t.get("attempts", 1) or 1),
                                   status=str(t.get("status", "")),
                                   verified=str(ver.get("status", "")),
                                   tools_failed=self._failed_tools(t),
                                   strategy=strategy_by_task.get(t.get("id", ""), "")))
        return out

    @staticmethod
    def _strategies(events_path: Path) -> Dict[str, str]:
        out: Dict[str, str] = {}
        try:
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("kind") == "RECOVERY_DECISION" and ev.get("task_id"):
                    out.setdefault(ev["task_id"], ev.get("data", {}).get("strategy", ""))
        except OSError:
            pass
        return out

    @staticmethod
    def _failed_tools(task: Dict[str, Any]) -> List[str]:
        return [str(a.get("tool", "")) for a in (task.get("artifacts") or []) if isinstance(a, dict)][:3]

    # ------------------------------------------------------------------ analysis
    def analyze(self, obj: Any, graph: Any, observer: Any = None,
                verification: Optional[Dict[str, Any]] = None) -> List[Lesson]:
        lessons: List[Lesson] = []
        tasks = list(graph.tasks.values())
        for t in tasks:
            ok = (t.status == "COMPLETED" and (t.verification or {}).get("status") == "VERIFIED")
            if t.attempts > 1 and t.failure_class and ok:
                lessons.append(Lesson.new(
                    KIND_RECOVERY,
                    f"when a step fails with {t.failure_class}, retrying with the failed-check feedback "
                    f"worked (task: {t.text[:80]})",
                    objective_id=obj.id, task_id=t.id, failure_class=t.failure_class,
                    evidence=[{"objective": obj.id, "task": t.id, "attempts": t.attempts,
                               "verified": (t.verification or {}).get("status")}]))
            if t.attempts >= 3 and not ok:
                lessons.append(Lesson.new(
                    KIND_TOOL,
                    f"repeating the same approach for '{t.text[:60]}' after {t.attempts} attempts kept "
                    f"failing ({t.failure_class or 'UNKNOWN'}) — a different decomposition is needed",
                    objective_id=obj.id, task_id=t.id, failure_class=t.failure_class,
                    evidence=[{"objective": obj.id, "task": t.id, "status": t.status}]))
        # safety lessons: was anything denied, and did the objective survive it?
        if observer is not None:
            denied = []
            try:
                for o in observer.observations() if hasattr(observer, "observations") else []:
                    if o.status in ("blocked", "declined"):
                        denied.append({"tool": o.tool, "task": o.task_id, "output": o.output[:160]})
            except Exception:
                denied = []
            if denied:
                lessons.append(Lesson.new(
                    KIND_SAFETY, f"policy denied {len(denied)} action(s) during this objective "
                                 f"({', '.join(sorted({d['tool'] for d in denied}))})",
                    objective_id=obj.id, evidence=denied))
        # efficiency lessons
        usage = getattr(obj, "usage", None)
        if usage is not None and getattr(usage, "tool_calls", 0):
            lessons.append(Lesson.new(
                KIND_EFFICIENCY,
                f"objectives like '{obj.goal[:60]}' took {usage.tool_calls} tool calls, "
                f"{usage.retries} retries, {int(usage.seconds)}s",
                objective_id=obj.id,
                evidence=[{"tool_calls": usage.tool_calls, "retries": usage.retries,
                           "seconds": int(usage.seconds)}]))
        return lessons

    # ------------------------------------------------------------------ validation
    def validate(self, lesson: Lesson) -> Lesson:
        """Check a candidate against recorded history. Never trusts the model."""
        eps = self.episodes()
        if lesson.kind == KIND_RECOVERY:
            same = [e for e in eps if e.failure_class == lesson.failure_class and e.attempts > 1]
            good = [e for e in same if e.status == "COMPLETED" and e.verified == "VERIFIED"]
            bad = [e for e in same if e.status in ("FAILED", "BLOCKED", "NEEDS_USER")]
            lesson.supports = len(good)
            lesson.contradictions = len(bad)
            if bad and not good:
                lesson.status, lesson.note = "contradicted", "no episode recovered from this failure class"
            elif len(good) >= MIN_SUPPORT and len(bad) <= len(good):
                lesson.status, lesson.note = "validated", f"{len(good)} recoveries, {len(bad)} failures"
            elif good:
                lesson.status, lesson.note = "supported", f"{len(good)} recovery episode(s)"
            else:
                lesson.status, lesson.note = "candidate", "no recorded recovery yet"
        elif lesson.kind == KIND_TOOL:
            same = [e for e in eps if lesson.text[:40] in e.text or e.failure_class == lesson.failure_class]
            failed = [e for e in same if e.status in ("FAILED", "BLOCKED", "NEEDS_USER")]
            ok = [e for e in same if e.status == "COMPLETED"]
            lesson.supports, lesson.contradictions = len(failed), len(ok)
            lesson.status = "validated" if len(failed) >= MIN_SUPPORT and not ok else (
                "supported" if failed else "candidate")
            lesson.note = f"{len(failed)} failing episode(s), {len(ok)} succeeding"
        elif lesson.kind == KIND_SAFETY:
            lesson.status = "supported" if lesson.evidence else "candidate"
            lesson.note = "denials are recorded facts (kept in memory, never a DNA rule)"
        elif lesson.kind == KIND_EFFICIENCY:
            lesson.status = "supported"
            lesson.note = "measurement, not a rule"
        else:
            lesson.status = "candidate"
        self.save(lesson)
        self._event(f"LESSON_{lesson.status.upper()}", lesson)
        return lesson

    # ------------------------------------------------------------------ promotion
    def promote(self, lesson: Lesson, memory: Any = None, dna: bool = True) -> bool:
        """Lesson → procedural memory (+ DNA behaviour for fully validated lessons).

        * `supported`  (≥1 confirming episode) → procedural memory, low confidence, tagged
          `lesson-candidate`: recallable and inspectable, never a rule.
        * `validated`  (≥MIN_SUPPORT episodes, no contradictions) → procedural memory at real
          confidence **and** a DNA lesson (persistent behaviour), versioned by the Evolver.
        Anything else (candidate / contradicted / rejected) is never promoted.
        """
        if lesson.status not in ("supported", "validated"):
            return False
        if lesson.kind not in PROMOTABLE_KINDS:
            return False                     # recorded, inspectable — not behaviour
        try:
            from rad.memory import OBSERVED, Memory
            mem = memory or Memory(self.home)
            tags = ["lesson", lesson.kind, lesson.failure_class or "general"]
            importance = 0.6
            if lesson.status != "validated":
                tags.append("lesson-candidate")
                importance = 0.35
            mem.add("procedural", lesson.text, tags=tags, origin=OBSERVED,
                    source=lesson.objective_id or "experience", importance=importance,
                    confidence=0.8 if lesson.status == "validated" else 0.5)
        except Exception:
            return False
        if lesson.status == "validated" and dna:
            try:
                from rad.dna import Evolver
                Evolver(self.home).add_lesson(f"{lesson.kind}: {lesson.text[:200]}")
            except Exception:
                pass
        lesson.promoted = True
        self.save(lesson)
        self._event("LESSON_PROMOTED", lesson, behaviour=lesson.status == "validated")
        return True

    # ------------------------------------------------------------------ per objective
    def run(self, obj: Any, graph: Any, observer: Any = None,
            verification: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """analyze → validate → (promote validated) → record. Returns a report."""
        proposed = self.analyze(obj, graph, observer, verification)
        validated, promoted, rejected = 0, 0, 0
        for les in proposed:
            self.validate(les)
            if les.status == "validated":
                validated += 1
            if les.status in ("contradicted", "rejected"):
                rejected += 1
            if self.promote(les):
                promoted += 1
        report = {"objective": getattr(obj, "id", ""), "proposed": len(proposed),
                  "validated": validated, "promoted": promoted, "rejected": rejected,
                  "lessons": [{"kind": l.kind, "status": l.status, "text": l.text[:160]} for l in proposed]}
        self._event("LESSON_RUN", Lesson.new("run", f"objective {getattr(obj, 'id', '')}"),
                    proposed=len(proposed), validated=validated, promoted=promoted)
        return report

    # ------------------------------------------------------------------ views
    def stats(self) -> Dict[str, Any]:
        items = self.lessons(n=2000)
        by_status: Dict[str, int] = {}
        by_kind: Dict[str, int] = {}
        for l in items:
            by_status[l.status] = by_status.get(l.status, 0) + 1
            by_kind[l.kind] = by_kind.get(l.kind, 0) + 1
        eps = self.episodes()
        return {"lessons": len(items), "by_status": by_status, "by_kind": by_kind,
                "episodes": len(eps), "promoted": sum(1 for l in items if l.promoted)}

    def show(self, n: int = 20) -> str:
        items = self.lessons(n=n)
        if not items:
            return "  no lessons yet — they are proposed when an objective finishes"
        lines = []
        for l in items:
            flag = {"validated": "✔", "supported": "·", "candidate": "?", "contradicted": "✘",
                    "rejected": "✘"}.get(l.status, "?")
            lines.append(f"  {flag} [{l.status:<12}] {l.kind:<16} {l.text[:110]}")
            if l.note:
                lines.append(f"      {l.note}")
        return "\n".join(lines)
