"""The world model — Rad's picture of your world.

Compresses memory + experience into entities and relations ("X works at Y",
"Z is my server", "A depends on B"), queryable and auto-injected into context
when relevant. Prediction, not just recall.

Backends (socket pattern, like the trainer/battery):
  builtin — pure-Python entity/relation store (always available, source of truth)
  kuzu    — Kuzu embedded graph DB (the same engine Graphiti runs on):
            `rad world sync` mirrors the graph into Cypher-space,
            `rad world cypher <q>` queries it — serverless, no key needed
  graphiti — full graphiti-core pipeline (LLM extraction, temporal edges):
            plug in when you have a graph server + LLM client; Rad's
            extraction is already brain-backed, so the kuzu mirror is the
            default consumption of this OSS layer
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional

from rad.home import RadHome
from rad.ui import col

# object = up to 5 lowercase words, trimmed at the first clause word below
_OBJ = r"([a-z0-9_\-]+(?:[ ][a-z0-9_\-]+){0,4})"
REL_PATTERNS = [
    (r"\b(?:is|are)\s+" + _OBJ, "is"),
    (r"\bworks?\s+at\s+" + _OBJ, "works_at"),
    (r"\buses?\s+" + _OBJ, "uses"),
    (r"\blikes?\s+" + _OBJ, "likes"),
    (r"\bdepends\s+on\s+" + _OBJ, "depends_on"),
    (r"\b(?:located|lives|based)\s+(?:in|at)\s+" + _OBJ, "located_in"),
    (r"\b(?:is called|named)\s+" + _OBJ, "named"),
]
CLAUSE_WORDS = {"and", "or", "but", "that", "which", "because", "called", "also",
                "then", "so", "if", "when", "i", "it"}
ENTITY_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")
ENTITY_STOP = {"the", "this", "that", "it", "a", "an", "i", "my", "we", "you",
               "he", "she", "rad", "today", "this"}


ENTITY_KINDS = ("person", "organization", "project", "task", "artifact", "tool", "software",
                "website", "event", "concept", "location", "thing", "entity")
RELATION_KINDS = ("owns", "works_on", "works_at", "depends_on", "created", "uses", "knows",
                  "contains", "related_to", "derived_from", "is", "likes", "located_in", "named")
# relations where one subject normally has ONE current value → a new value supersedes (temporal)
FUNCTIONAL = {"located_in", "works_at", "named", "is"}

# origin of a fact (same vocabulary as memory)
USER_PROVIDED = "USER_PROVIDED"          # the user said so — treated as fact
OBSERVED = "OBSERVED"                    # a tool/objective really observed it
INFERRED = "INFERRED"                    # derived from other facts
MODEL_GENERATED = "MODEL_GENERATED"      # a model wrote it — never a fact on its own
ASSUMPTION = "ASSUMPTION"                # explicitly held as a working assumption, to be confirmed
_CONF = {USER_PROVIDED: 0.9, OBSERVED: 0.8, INFERRED: 0.5, MODEL_GENERATED: 0.4,
         ASSUMPTION: 0.3}
ORIGINS = (USER_PROVIDED, OBSERVED, INFERRED, MODEL_GENERATED, ASSUMPTION)


def _entity_name(raw: str) -> str:
    """'The Acceptance Rig' → 'Acceptance Rig': drop leading articles and one-word noise."""
    parts = [p for p in (raw or "").split() if p]
    while parts and parts[0].lower() in ENTITY_STOP:
        parts = parts[1:]
    name = " ".join(parts)
    return name if len(name) > 2 else ""


def _origin_for(source: str) -> str:
    s = (source or "").lower()
    if s.startswith(("assum",)):
        return ASSUMPTION
    if s.startswith(("manual", "user")):
        return USER_PROVIDED
    if s.startswith(("obj_", "file:", "tool:", "artifact")):
        return OBSERVED
    if s.startswith(("llm", "sleep", "chat-close")):
        return MODEL_GENERATED
    return INFERRED


class WorldModel:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "world" / "graph.json"
        # store is always the builtin JSON graph (deterministic, offline);
        # graphiti/Kuzu is an optional mirror via sync() for temporal queries
        self.backend = "builtin"

    # ------------------------------------------------------------ storage
    def data(self) -> Dict[str, Any]:
        try:
            d = json.loads(self.path.read_text())
        except Exception:
            d = None
        if not isinstance(d, dict) or not isinstance(d.get("entities"), dict) or not isinstance(d.get("relations"), list):
            return {"entities": {}, "relations": [], "updated": 0}
        return d

    def save(self, d: Dict[str, Any]) -> None:
        d["updated"] = time.time()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(d, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------ learn
    def learn(self, text: str, source: str = "text", caller: Optional[Callable[[str], str]] = None) -> int:
        """Extract entities + relations from text. Brain-assisted when online."""
        d = self.data()
        added = 0
        if caller is not None:
            try:
                raw = caller(
                    "Extract from the text below any durable facts about the user's world: "
                    'entities (people, places, projects, tools, servers) as {"name": ..., "kind": ...} '
                    'and relations as {"from": ..., "rel": ..., "to": ...}. '
                    "Reply with ONLY JSON: {\"entities\": [...], \"relations\": [...]}. "
                    "Max 8 each. If nothing durable, return empty lists.\n\n" + text[:3000])
                m = re.search(r"\{.*\}", raw or "", re.S)
                if m:
                    got = json.loads(m.group(0))
                    lorigin = USER_PROVIDED if source == "manual" else MODEL_GENERATED
                    for e in got.get("entities", [])[:8]:
                        if isinstance(e, dict) and e.get("name"):
                            if self._add_entity(d, str(e["name"]), str(e.get("kind", "thing")).lower(), source, lorigin):
                                added += 1
                    for r in got.get("relations", [])[:8]:
                        if isinstance(r, dict) and r.get("from") and r.get("to") and r.get("rel"):
                            if self._add_relation(d, str(r["from"]), str(r["rel"]).lower().replace(" ", "_"),
                                                  str(r["to"]), source, lorigin):
                                added += 1
                    self.save(d)
                    return added
            except Exception:
                pass
        # heuristic fallback (works offline)
        names = [n for n in (_entity_name(m.group(1)) for m in ENTITY_RE.finditer(text)) if n]
        for name in names:
            if self._add_entity(d, name, "entity", source):
                added += 1
        subject = names[0] if names else None
        low = text.lower()
        for pat, rel in REL_PATTERNS:
            mm = re.search(pat, low)
            if mm and subject:
                words = mm.group(1).split()
                for k, w in enumerate(words):
                    if w in CLAUSE_WORDS:          # trim at the first clause word
                        words = words[:k]
                        break
                obj = " ".join(words)
                if 2 < len(obj) < 40 and 1 <= len(obj.split()) <= 3:
                    if self._add_relation(d, subject, rel, obj, source):
                        added += 1
        if added:
            self.save(d)
        return added

    def _add_entity(self, d: Dict[str, Any], name: str, kind: str, source: str,
                    origin: Optional[str] = None) -> bool:
        key = name.lower()
        kind = (kind or "thing").lower()[:30]
        origin = origin or _origin_for(source)
        now = time.time()
        if key not in d["entities"]:
            d["entities"][key] = {"name": name, "kind": kind, "sources": [source], "origin": origin,
                                  "confidence": _CONF[origin], "seen": now, "first_seen": now, "count": 1}
            return True
        e = d["entities"][key]
        e["count"] += 1
        e["seen"] = now
        if source not in e["sources"]:
            e["sources"].append(source)
            # independent re-observation raises confidence a little
            e["confidence"] = min(0.98, e.get("confidence", 0.5) + 0.05)
        if _CONF[origin] > _CONF.get(e.get("origin", INFERRED), 0):
            e["origin"], e["confidence"] = origin, max(e.get("confidence", 0), _CONF[origin])
        if e.get("kind") in ("entity", "thing") and kind not in ("entity", "thing"):
            e["kind"] = kind
        return False

    def _add_relation(self, d: Dict[str, Any], a: str, rel: str, b: str, source: str,
                      origin: Optional[str] = None) -> bool:
        origin = origin or _origin_for(source)
        now = time.time()
        rel = rel if rel in RELATION_KINDS else rel.replace(" ", "_")[:30]
        for r in d["relations"]:
            if r["from"].lower() == a.lower() and r["rel"] == rel and r["to"].lower() == b.lower():
                if source not in r["sources"]:
                    r["sources"].append(source)
                    r["confidence"] = min(0.98, r.get("confidence", 0.5) + 0.05)
                if _CONF[origin] > _CONF.get(r.get("origin", INFERRED), 0):
                    r["origin"], r["confidence"] = origin, max(r.get("confidence", 0), _CONF[origin])
                if r.get("until"):          # re-asserted after being superseded → current again
                    r["until"] = None
                    r["status"] = "current"
                return False
        new = {"from": a, "rel": rel, "to": b, "sources": [source], "at": now, "since": now, "until": None,
               "origin": origin, "confidence": _CONF[origin], "status": "current"}
        if rel in FUNCTIONAL:
            for r in d["relations"]:
                if r["from"].lower() == a.lower() and r["rel"] == rel and r.get("status", "current") == "current":
                    if _CONF[origin] >= r.get("confidence", 0):
                        r["until"], r["status"] = now, "superseded"
                        r["superseded_by"] = f"{b}"
                    else:
                        new["status"] = "disputed"       # weaker source disagrees with a stronger one
                        new["disputes"] = r["to"]
        d["relations"].append(new)
        return True

    # ------------------------------------------------------------ correction
    def retract(self, a: str, rel: str, b: str) -> bool:
        d = self.data()
        for r in d["relations"]:
            if r["from"].lower() == a.lower() and r["rel"] == rel and r["to"].lower() == b.lower() \
                    and r.get("status", "current") != "retracted":
                r["status"], r["until"] = "retracted", time.time()
                self.save(d)
                return True
        return False

    def confirm(self, a: str, rel: str, b: str) -> bool:
        d = self.data()
        for r in d["relations"]:
            if r["from"].lower() == a.lower() and r["rel"] == rel and r["to"].lower() == b.lower():
                r["origin"], r["confidence"], r["status"], r["until"] = USER_PROVIDED, 0.95, "current", None
                for o in d["relations"]:
                    if o is not r and o["from"].lower() == a.lower() and o["rel"] == rel and rel in FUNCTIONAL:
                        o["status"], o["until"] = "superseded", time.time()
                self.save(d)
                return True
        return False

    def disputes(self) -> List[Dict[str, Any]]:
        return [r for r in self.data()["relations"] if r.get("status") == "disputed"]

    def current_relations(self, d: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        d = d or self.data()
        return [r for r in d["relations"] if r.get("status", "current") in ("current", "disputed")]

    # ------------------------------------------------------------ query
    def query(self, term: str, include_history: bool = False) -> List[Dict[str, Any]]:
        d = self.data()
        t = term.lower()
        out: List[Dict[str, Any]] = []
        for e in d["entities"].values():
            if t in e["name"].lower():
                out.append({"type": "entity", **e})
        rels = self.current_relations(d) if not include_history else d["relations"]
        for r in rels:
            if t in (r["from"] + " " + r["to"] + " " + r["rel"]).lower():
                out.append({"type": "relation", **r})
        # neighbors: entities related to a matched entity
        matched = {e["name"].lower() for e in out if e["type"] == "entity"}
        if matched:
            for r in rels:
                if (r["from"].lower() in matched or r["to"].lower() in matched) and \
                        not any(o["type"] == "relation" and o.get("at") == r.get("at") for o in out):
                    out.append({"type": "relation", **r})
        out.sort(key=lambda x: -x.get("count", x.get("at", 0)))
        return out[:15]

    def context_block(self, text: str, max_items: int = 6) -> str:
        """Facts relevant to the current conversation, for system-prompt injection."""
        from rad.memory import tokenize
        q = set(tokenize(text))
        if not q:
            return ""
        d = self.data()
        scored = []
        for e in d["entities"].values():
            overlap = len(q & set(e["name"].lower().split()))
            if overlap:
                scored.append((overlap * 2 + min(e["count"], 3) * 0.3, f"- {e['name']} ({e['kind']})"))
        for r in self.current_relations(d):
            blob = (r["from"] + " " + r["to"]).lower()
            overlap = len(q & set(blob.split()))
            if overlap:
                tag = r.get("origin", "inferred").lower()
                if r.get("status") == "disputed":
                    tag += ",disputed"
                scored.append((overlap * 2 + 0.5 + r.get("confidence", 0.5),
                               f"- {r['from']} --{r['rel']}--> {r['to']} ({tag})"))
        if not scored:
            return ""
        scored.sort(key=lambda x: -x[0])
        return ("World model (what Rad knows about your world; model_generated/inferred are unconfirmed):\n"
                + "\n".join(s[1] for s in scored[:max_items]))

    def show(self) -> str:
        d = self.data()
        ents = sorted(d["entities"].values(), key=lambda e: -e["count"])
        gi = ("kuzu graph DB ready — `rad world sync` / `rad world cypher <q>`"
              if kuzu_available() else "kuzu not installed (graph mirror optional)")
        out = [f"  store: {self.backend}   entities: {len(ents)}   relations: {len(d['relations'])}   {col.dim(gi)}"]
        for e in ents[:8]:
            kind = col.dim(f"{e['kind']} x{e['count']}")
            out.append(f"    • {e['name']:<20} {kind}")
        for r in self.current_relations(d)[:8]:
            rel = col.dim(f"–{r['rel']}–>")
            tag = col.dim(f"{r.get('origin', 'inferred').lower()} c={r.get('confidence', 0.5):.2f}")
            flag = col.yellow(" disputed") if r.get("status") == "disputed" else ""
            out.append(f"    → {r['from']} {rel} {r['to']}  {tag}{flag}")
        hist = [r for r in d["relations"] if r.get("status") == "superseded"]
        if hist:
            out.append(col.dim(f"    ({len(hist)} superseded relation(s) kept as history — `rad world query <x> --history`)"))
        if not ents and not d["relations"]:
            out.append(col.dim("  empty — it learns from memory, chat and `rad world add`"))
        return "\n".join(out)

    def add(self, sentence: str, caller: Optional[Callable[[str], str]] = None) -> int:
        return self.learn(sentence, source="manual", caller=caller)

    def assume(self, sentence: str, caller: Optional[Callable[[str], str]] = None) -> int:
        """Record something RAD is *assuming* (origin ASSUMPTION, low confidence, status assumed).

        Assumptions are first-class so they can be listed, disputed and later `confirm`ed — a
        guess must never quietly become a fact just because it was written down.
        """
        return self.learn(sentence, source="assumption", caller=None)

    def assumptions(self) -> List[Dict[str, Any]]:
        return [r for r in self.current_relations() if r.get("origin") == ASSUMPTION]

    def learn_observation(self, objective_id: str, task_id: str, artifacts: List[Dict[str, Any]]) -> int:
        """Ground truth from the control plane: artifacts really exist → OBSERVED facts."""
        d = self.data()
        n = 0
        for a in artifacts:
            name = a["location"].rsplit("/", 1)[-1]
            n += self._add_entity(d, name, "artifact", f"{objective_id}/{task_id}", OBSERVED)
            n += self._add_relation(d, objective_id, "created", name, f"{objective_id}/{task_id}", OBSERVED)
        if artifacts:
            self._add_entity(d, objective_id, "task", objective_id, OBSERVED)
            self.save(d)
        return n


# ------------------------------------------------------------ kuzu backend (optional)

def kuzu_available() -> bool:
    try:
        import kuzu  # noqa: F401
        return True
    except ImportError:
        return False


def _kuzu_conn(home: RadHome):
    import kuzu
    db_dir = home.root / "world" / "kuzu"
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = kuzu.Connection(kuzu.Database(str(db_dir / "world")))
    for stmt in (
        "CREATE NODE TABLE IF NOT EXISTS EntityNode(uid STRING PRIMARY KEY, name STRING, kind STRING)",
        "CREATE REL TABLE IF NOT EXISTS Relation(FROM EntityNode TO EntityNode, rel STRING)",
    ):
        try:
            conn.execute(stmt)
        except Exception:
            pass  # already exists
    return conn


def kuzu_sync(home: RadHome, world: WorldModel) -> Optional[str]:
    """Mirror the builtin graph into the embedded Kuzu graph DB (idempotent)."""
    if not kuzu_available():
        return None
    try:
        conn = _kuzu_conn(home)
        d = world.data()
        for e in d["entities"].values():
            conn.execute("MERGE (n:EntityNode {uid: $uid}) SET n.name = $name, n.kind = $kind",
                         {"uid": "rad:" + e["name"].lower(), "name": e["name"],
                          "kind": str(e.get("kind", "entity"))[:60]})
        for r in d["relations"]:
            # ensure both endpoints exist so the graph stays connected
            for name, kind in ((r["from"], "ref"), (r["to"], "ref")):
                conn.execute("MERGE (n:EntityNode {uid: $uid}) SET n.name = COALESCE(n.name, $name), n.kind = COALESCE(n.kind, $kind)",
                             {"uid": "rad:" + name.lower(), "name": name, "kind": kind})
            conn.execute(
                "MATCH (a:EntityNode {uid: $a}), (b:EntityNode {uid: $b}) "
                "MERGE (a)-[x:Relation {rel: $rel}]->(b)",
                {"a": "rad:" + r["from"].lower(), "b": "rad:" + r["to"].lower(),
                 "rel": str(r["rel"])[:40]})
        nodes = conn.execute("MATCH (n:EntityNode) RETURN count(n) AS c").get_all()[0][0]
        rels = conn.execute("MATCH ()-[x:Relation]->() RETURN count(x) AS c").get_all()[0][0]
        return f"kuzu graph: {nodes} entities, {rels} relations → {home.root / 'world' / 'kuzu'}"
    except Exception as e:
        return f"kuzu sync failed: {str(e)[:160]}"


def kuzu_query(home: RadHome, cypher: str) -> str:
    """Run raw Cypher against the world graph (read the docs: Cypher dialect)."""
    try:
        conn = _kuzu_conn(home)
        rows = conn.execute(cypher).get_all()
        return "\n".join("  " + str(r) for r in rows) if rows else "  (no rows)"
    except Exception as e:
        return f"  cypher failed: {str(e)[:200]}"
