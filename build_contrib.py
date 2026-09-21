#!/usr/bin/env python3
"""
build_contrib.py — self-extracting builder for the Rad Agent contribution pack.

WHAT IT DOES
  1. Creates contrib_staging/ with the complete file tree (never touches your repo)
  2. Writes every module, byte-for-byte, in place
  3. Optionally self-verifies everything offline (python build_contrib.py --verify)

RUN
  python build_contrib.py            # build only
  python build_contrib.py --verify   # build + run all offline checks

THEN (your side of the deal)
  copy contrib_staging/rad/papers   -> <repo>/rad/papers
  copy contrib_staging/rad/memory   -> merge strength.py into <repo>/rad/memory/
  copy contrib_staging/scripts/verify_contrib.py -> <repo>/scripts/
  run: python scripts/verify_contrib.py   (from repo root)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "contrib_staging"

FILES = {

# ============================================================
# rad/papers/__init__.py
# ============================================================
"rad/papers/__init__.py": '''
"""Research Frontier — papers as a second evolution input.

Law: nothing goes live without winning a benchmark battle —
     including ideas that arrive with a citation.
"""
''',

# ============================================================
# rad/papers/ingest.py
# ============================================================
"rad/papers/ingest.py": '''
"""Paper ingestion: URL/arXiv-id -> sha256-pinned local text.

State: ~/.rad/papers/<slug>/{paper.md, meta.json, card.json}
"""
import hashlib, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

PAPERS_DIR = Path.home() / ".rad" / "papers"
ARXIV_RE = re.compile(r"(\\d{4}\\.\\d{4,5})(v\\d+)?")

def _now(): return datetime.now(timezone.utc).isoformat()
def _sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def _slug_from_url(url: str) -> str:
    m = ARXIV_RE.search(url)
    if m: return m.group(1)
    slug = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:64]
    return slug or "unknown"

def fetch_paper_text(source: str):
    """Returns (text, resolved_url, slug). arXiv HTML preferred (no PDF parsing)."""
    source = source.strip()
    if ARXIV_RE.fullmatch(source):
        arxiv_id = ARXIV_RE.fullmatch(source).group(1)
        url = f"https://arxiv.org/abs/{arxiv_id}"
        text = _fetch_url_text(f"https://arxiv.org/html/{arxiv_id}") or _fetch_url_text(url)
        return text, url, arxiv_id
    if source.startswith("http"):
        return _fetch_url_text(source), source, _slug_from_url(source)
    raise ValueError(f"Cannot resolve source: {source!r}. Use an arXiv id or URL.")

def _fetch_url_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "rad-agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
    except Exception as e:
        raise RuntimeError(f"Fetch failed for {url}: {e}") from e
    if "html" in ctype or raw[:200].lower().lstrip().startswith(b"<!doctype"):
        return _html_to_text(raw.decode("utf-8", errors="replace"))
    return raw.decode("utf-8", errors="replace")

def _html_to_text(html: str) -> str:
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<br\\s*/?>", "\\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\\n\\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    for k, v in {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": chr(34), "&#39;": chr(39), "&nbsp;": " "}.items():
        html = html.replace(k, v)
    html = re.sub(r"[ \\t]+", " ", html)
    html = re.sub(r"\\n{3,}", "\\n\\n", html)
    return html.strip()

def ingest_paper(source: str) -> dict:
    """Ingest a paper. Writes paper.md + meta.json. Confirm-first by caller."""
    text, url, slug = fetch_paper_text(source)
    if not text or len(text) < 200:
        raise RuntimeError(f"Extracted text too short ({len(text)} chars) — bad source?")
    paper_dir = PAPERS_DIR / slug
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "paper.md").write_text(text, encoding="utf-8")
    m = re.search(r"^#\\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else text.split("\\n")[0][:120].strip()
    meta = {"slug": slug, "source_url": url, "title": title,
            "sha256": _sha256(text.encode("utf-8")), "ingested_at": _now(),
            "char_count": len(text), "status": "ingested"}
    (paper_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

def list_papers() -> list:
    if not PAPERS_DIR.exists(): return []
    return [json.loads((d / "meta.json").read_text(encoding="utf-8"))
            for d in sorted(PAPERS_DIR.iterdir())
            if (d / "meta.json").exists()]

def get_paper(slug: str):
    f = PAPERS_DIR / slug / "meta.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

def get_paper_text(slug: str):
    f = PAPERS_DIR / slug / "paper.md"
    return f.read_text(encoding="utf-8") if f.exists() else None
''',

# ============================================================
# rad/papers/cards.py
# ============================================================
"rad/papers/cards.py": '''
"""Technique Cards — the bridge between a paper and a testable candidate.

Law: no claim without an exact quote on disk.
"""
import json
from datetime import datetime, timezone
from .ingest import PAPERS_DIR, get_paper, get_paper_text

CARD_VERSION = 1
VALID_TYPES = {"technique", "benchmark", "dataset", "theory", "survey"}
VALID_STATUS = {"extracted", "candidate", "battling", "promoted", "rejected", "retracted"}

def _now(): return datetime.now(timezone.utc).isoformat()

def create_card(slug, card_type, claims, mechanism, implementation_surface,
                battle_plan=None, coi_flags=None) -> dict:
    """Every claim MUST carry evidence_quote; verified against paper text (flag, not block)."""
    if card_type not in VALID_TYPES:
        raise ValueError(f"card_type must be one of {VALID_TYPES}")
    meta = get_paper(slug)
    if not meta:
        raise ValueError(f"Paper {slug!r} not ingested. Run ingest first.")
    paper_text = get_paper_text(slug) or ""
    norm_paper = " ".join(paper_text.split()).lower()

    verified = []
    for c in claims:
        quote = str(c.get("evidence_quote", "")).strip()
        if not quote:
            raise ValueError(f"Claim without evidence_quote: {str(c.get('claim'))[:60]!r}")
        verified.append({"claim": str(c.get("claim", "")).strip(),
                         "evidence_quote": quote,
                         "claimed_gain": c.get("claimed_gain", ""),
                         "quote_verified": " ".join(quote.split()).lower() in norm_paper})

    card = {"card_version": CARD_VERSION, "card_id": f"TC-{slug[:20]}",
            "source": {"slug": slug, "title": meta["title"],
                       "url": meta["source_url"], "sha256": meta["sha256"]},
            "type": card_type, "claims": verified, "mechanism": mechanism,
            "implementation_surface": implementation_surface,
            "battle_plan": battle_plan or {"baseline": "current", "suite": "realworld",
                "metrics": ["verified_rate", "false_done", "cost"],
                "note": "default — customize before battle"},
            "coi_flags": coi_flags or [], "status": "extracted",
            "created_at": _now(), "updated_at": _now()}
    (PAPERS_DIR / slug / "card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card

def get_card(slug: str):
    f = PAPERS_DIR / slug / "card.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

def list_cards(status=None) -> list:
    if not PAPERS_DIR.exists(): return []
    out = []
    for d in sorted(PAPERS_DIR.iterdir()):
        c = get_card(d.name) if (d / "card.json").exists() else None
        if c and (status is None or c.get("status") == status):
            out.append(c)
    return out

_LEGAL = {"extracted": {"candidate", "rejected"}, "candidate": {"battling", "rejected"},
          "battling": {"promoted", "rejected"}, "promoted": {"retracted"},
          "rejected": set(), "retracted": set()}

def set_card_status(slug, new_status) -> dict:
    if new_status not in VALID_STATUS:
        raise ValueError(f"Invalid status: {new_status!r}")
    card = get_card(slug)
    if not card:
        raise ValueError(f"No card for {slug!r}")
    cur = card["status"]
    if new_status not in _LEGAL.get(cur, set()):
        raise ValueError(f"Illegal transition: {cur!r} -> {new_status!r}")
    card["status"] = new_status
    card["updated_at"] = _now()
    (PAPERS_DIR / slug / "card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card

def check_coi(card, benchmark_names) -> list:
    """COI firewall: a paper proposing benchmark X is never validated on X."""
    flags = []
    title_l = card["source"]["title"].lower()
    from .ingest import get_paper_text
    snippet = (get_paper_text(card["source"]["slug"]) or "")[:3000].lower()
    for b in benchmark_names:
        bl = b.lower()
        if bl in title_l or bl in snippet:
            flags.append(f"COI: paper mentions benchmark {b!r} — cannot validate on it")
    if flags:
        card["coi_flags"] = sorted(set(card.get("coi_flags", [])) | set(flags))
        (PAPERS_DIR / card["source"]["slug"] / "card.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8")
    return flags
''',

# ============================================================
# rad/papers/battle.py
# ============================================================
"rad/papers/battle.py": '''
"""Paired battle harness: baseline vs candidate on identical seeded tasks.

Results graded from grader_result dicts (disk-only law). Every battle is a
pinned, auditable record. Integration: pass your executor as execute_fn.
"""
import hashlib, json, time
from datetime import datetime, timezone
from .cards import get_card, set_card_status
from .ingest import PAPERS_DIR

BATTLE_DIR = PAPERS_DIR / "_battles"

def _now(): return datetime.now(timezone.utc).isoformat()
def _sha(s) -> str:
    if isinstance(s, str): s = s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()

def design_battle(slug, task_suite, baseline_config, candidate_config, seed=0) -> dict:
    """task_suite: [{"task_id","prompt","grader"}] — grader schema same as scenario pack."""
    card = get_card(slug)
    if not card: raise ValueError(f"No card for {slug!r}")
    if card["status"] != "candidate":
        raise ValueError(f"Card status must be 'candidate' to battle, got {card['status']!r}")
    spec = {"battle_id": f"battle-{slug}-{seed}-{_sha(json.dumps(baseline_config)+json.dumps(candidate_config))[:12]}",
            "slug": slug, "card_id": card["card_id"], "seed": seed,
            "task_count": len(task_suite),
            "task_hashes": [_sha(json.dumps(t, sort_keys=True)) for t in task_suite],
            "baseline_config": baseline_config, "candidate_config": candidate_config,
            "metrics": card["battle_plan"].get("metrics", ["verified_rate", "false_done", "cost"]),
            "designed_at": _now(), "status": "designed"}
    bdir = BATTLE_DIR / spec["battle_id"]
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "tasks.json").write_text(json.dumps(task_suite, indent=2), encoding="utf-8")
    (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return spec

def run_battle(battle_id, execute_fn, dry_run=True) -> dict:
    """execute_fn(config, task, seed) -> {"grader_result": {...}, "events": [...]}"""
    bdir = BATTLE_DIR / battle_id
    if not bdir.exists(): raise ValueError(f"Battle {battle_id!r} not found")
    spec = json.loads((bdir / "spec.json").read_text(encoding="utf-8"))
    tasks = json.loads((bdir / "tasks.json").read_text(encoding="utf-8"))
    if spec["status"] != "designed":
        raise ValueError(f"Battle status must be 'designed', got {spec['status']!r}")
    if dry_run:
        spec["status"] = "dry_run_complete"
        spec["note"] = "dry run passed — dry_run=False to execute for real (costs tokens)"
        (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
        return spec

    base, cand = [], []
    for task in tasks:
        seed_int = int(hashlib.sha256(f"{spec['seed']}:{task['task_id']}".encode()).hexdigest()[:8], 16)
        t0 = time.monotonic(); b = execute_fn(spec["baseline_config"], task, seed_int); bd = time.monotonic() - t0
        t0 = time.monotonic(); c = execute_fn(spec["candidate_config"], task, seed_int); cd = time.monotonic() - t0
        base.append({"task_id": task["task_id"], "grader_result": b.get("grader_result", {}),
                     "duration_s": round(bd, 3), "events_count": len(b.get("events", []))})
        cand.append({"task_id": task["task_id"], "grader_result": c.get("grader_result", {}),
                     "duration_s": round(cd, 3), "events_count": len(c.get("events", []))})

    scores = _score(spec["metrics"], base, cand)
    verdict = _verdict(scores, spec["metrics"])
    result = {"battle_id": battle_id, "slug": spec["slug"], "seed": spec["seed"],
              "ran_at": _now(), "baseline_results": base, "candidate_results": cand,
              "scores": scores, "verdict": verdict, "status": "complete"}
    (bdir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    spec["status"] = "complete"
    (bdir / "spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    if verdict == "candidate_wins":
        set_card_status(spec["slug"], "battling")  # promotion is separate + confirmed
    return result

def _score(metrics, base, cand) -> dict:
    scores = {}
    for m in metrics:
        bv = [x["grader_result"][m] for x in base if m in x["grader_result"]]
        cv = [x["grader_result"][m] for x in cand if m in x["grader_result"]]
        bm = sum(bv)/len(bv) if bv else 0
        cm = sum(cv)/len(cv) if cv else 0
        scores[m] = {"baseline_mean": round(bm, 4), "candidate_mean": round(cm, 4),
                     "delta": round(cm - bm, 4), "n": min(len(bv), len(cv))}
    return scores

def _verdict(scores, metrics) -> str:
    wins = losses = ties = 0
    for m in metrics:
        if m not in scores: continue
        d = scores[m]["delta"]
        if d > 0.01: wins += 1
        elif d < -0.01: losses += 1
        else: ties += 1
    if wins and not losses: return "candidate_wins"
    if losses and not wins: return "baseline_wins"
    if wins and losses: return "mixed"
    return "tie"

def promote_technique(slug, battle_id, confirmation=False) -> dict:
    """Human-confirmed promotion. Requires a completed winning battle on disk."""
    if not confirmation:
        raise PermissionError("Promotion requires explicit confirmation=True.")
    card = get_card(slug)
    if not card: raise ValueError(f"No card for {slug!r}")
    rf = BATTLE_DIR / battle_id / "result.json"
    if not rf.exists(): raise ValueError(f"No completed result for battle {battle_id!r}")
    result = json.loads(rf.read_text(encoding="utf-8"))
    if result["verdict"] != "candidate_wins":
        raise ValueError(f"Cannot promote: verdict is {result['verdict']!r}")
    set_card_status(slug, "promoted")
    promo = {"slug": slug, "battle_id": battle_id, "promoted_at": _now(),
             "verdict": result["verdict"], "scores": result["scores"],
             "seed": result["seed"], "card_id": card["card_id"],
             "paper_sha256": card["source"]["sha256"]}
    (BATTLE_DIR / battle_id / "promotion.json").write_text(
        json.dumps(promo, indent=2), encoding="utf-8")
    return promo
''',

# ============================================================
# rad/papers/ledger.py
# ============================================================
"rad/papers/ledger.py": '''
"""Replication Ledger — claimed vs measured, append-only, open.

Losses are data. `export_ledger()` emits the open replication dataset.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from .ingest import PAPERS_DIR
from .battle import BATTLE_DIR

LEDGER_FILE = PAPERS_DIR / "_ledger.jsonl"

def record_battle_outcome(battle_id: str) -> dict:
    bdir = BATTLE_DIR / battle_id
    if not (bdir / "result.json").exists():
        raise ValueError(f"No result for battle {battle_id!r}")
    result = json.loads((bdir / "result.json").read_text(encoding="utf-8"))
    spec = json.loads((bdir / "spec.json").read_text(encoding="utf-8"))
    cf = PAPERS_DIR / spec["slug"] / "card.json"
    card = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    claimed = [{"claim": c["claim"], "claimed_gain": c["claimed_gain"]}
               for c in card.get("claims", []) if c.get("claimed_gain")]
    measured = {m: {"baseline": d["baseline_mean"], "candidate": d["candidate_mean"],
                    "delta": d["delta"], "n": d["n"]}
                for m, d in result.get("scores", {}).items()}
    claimed_positive = any(("+" in g["claimed_gain"]) or
                           ("improve" in g["claimed_gain"].lower()) for g in claimed)
    measured_positive = result.get("verdict") == "candidate_wins"
    verdict = ("CONFIRMED" if claimed_positive and measured_positive else
               "NOT_REPLICATED" if claimed_positive else "NO_CLAIM_TO_TEST")
    entry = {"ledger_ts": datetime.now(timezone.utc).isoformat(),
             "battle_id": battle_id, "slug": spec["slug"],
             "paper_title": card.get("source", {}).get("title", ""),
             "paper_url": card.get("source", {}).get("url", ""),
             "paper_sha256": card.get("source", {}).get("sha256", ""),
             "seed": spec["seed"], "task_count": spec.get("task_count", 0),
             "claimed": claimed, "measured": measured,
             "battle_verdict": result.get("verdict", ""),
             "replication_verdict": verdict,
             "coi_flags": card.get("coi_flags", [])}
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\\n")
    return entry

def read_ledger() -> list:
    if not LEDGER_FILE.exists(): return []
    return [json.loads(l) for l in LEDGER_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

def export_ledger(output_path=None) -> str:
    entries = read_ledger()
    verdicts = {}
    for e in entries:
        v = e.get("replication_verdict", "UNKNOWN")
        verdicts[v] = verdicts.get(v, 0) + 1
    data = {"format": "rad-replication-ledger", "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(entries),
            "summary": {"total_battles": len(entries), "verdicts": verdicts,
                        "replication_rate": round(verdicts.get("CONFIRMED", 0)/len(entries), 3) if entries else 0,
                        "papers_tested": len({e.get("slug") for e in entries})},
            "entries": entries}
    text = json.dumps(data, indent=2)
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
    return text
''',

# ============================================================
# rad/papers/extract.py
# ============================================================
"rad/papers/extract.py": '''
"""Brain-assisted card extraction with quote verification + retry-on-fail.

The extractor is held to the same law as the agent: no claim without an
exact quote on disk. Bad quotes -> feedback -> retry. Integration: brain_fn
= callable(prompt) -> str (your chat/LLM loop).
"""
import json, re
from .cards import create_card, get_card
from .ingest import PAPERS_DIR, get_paper, get_paper_text

EXTRACTION_PROMPT = """You are extracting a Technique Card from a research paper.
Output ONLY valid JSON matching this schema — no prose, no markdown fences:

{{
  "card_type": "technique|benchmark|dataset|theory|survey",
  "claims": [
    {{"claim": "<one falsifiable sentence>",
      "evidence_quote": "<EXACT verbatim text copied from the paper below>",
      "claimed_gain": "<number/percent claimed, or 'none'>"}}
  ],
  "mechanism": "<2-3 sentences: HOW it works>",
  "implementation_surface": ["<rad subsystem touched>"],
  "coi_flags": ["<e.g. paper evaluates on its own benchmark>"]
}}

RULES:
1. evidence_quote MUST be copied character-for-character from the paper text.
2. 1-5 claims max — strongest falsifiable claims only.
3. If the paper proposes/evaluates a named benchmark, add a coi_flag.
4. "technique" only if it proposes a METHOD changing runtime behavior.

PAPER TEXT:
{paper_text}
"""

class ExtractionError(RuntimeError):
    pass

def extract_card_brain(slug: str, brain_fn, max_retries: int = 2) -> dict:
    meta = get_paper(slug)
    if not meta: raise ValueError(f"Paper {slug!r} not ingested")
    if get_card(slug): raise ValueError(f"Card already exists for {slug!r}")
    paper_text = (get_paper_text(slug) or "")[:60_000]

    feedback, last_errors = "", []
    for attempt in range(1 + max_retries):
        prompt = EXTRACTION_PROMPT.format(paper_text=paper_text)
        if feedback:
            prompt += f"\\n\\nPREVIOUS ATTEMPT FAILED. Fix these:\\n{feedback}"
        parsed = _parse_json_loose(brain_fn(prompt))
        if parsed is None:
            last_errors = ["output was not valid JSON"]
            feedback = "Output ONLY the JSON object."
            continue
        errors = _validate(parsed, paper_text)
        if errors:
            last_errors = errors
            feedback = "These evidence_quotes were NOT found verbatim:\\n" + \\
                       "\\n".join(f"- {e}" for e in errors) + \\
                       "\\nCopy quotes EXACTLY, character-for-character."
            continue
        card = create_card(slug, parsed["card_type"], parsed["claims"],
                           parsed["mechanism"], parsed["implementation_surface"],
                           coi_flags=parsed.get("coi_flags", []))
        card["extraction"] = {"method": "brain_assisted", "attempts": attempt + 1,
                              "errors_before_pass": len(last_errors) if attempt else 0}
        (PAPERS_DIR / slug / "card.json").write_text(
            json.dumps(card, indent=2), encoding="utf-8")
        return card
    raise ExtractionError(f"Extraction failed after {1+max_retries} attempts: {last_errors}")

def _parse_json_loose(raw: str):
    raw = re.sub(r"^```(json)?\\s*|\\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if 0 <= s < e:
            try: return json.loads(raw[s:e+1])
            except json.JSONDecodeError: return None
        return None

def _validate(parsed: dict, paper_text: str) -> list:
    errors = []
    norm = " ".join(paper_text.split()).lower()
    if parsed.get("card_type") not in {"technique","benchmark","dataset","theory","survey"}:
        errors.append(f"bad card_type: {parsed.get('card_type')!r}")
    claims = parsed.get("claims", [])
    if not claims:
        errors.append("no claims extracted")
    for i, c in enumerate(claims):
        q = " ".join(str(c.get("evidence_quote", "")).split()).lower()
        if len(q) < 20:
            errors.append(f"claim[{i}] quote too short to verify")
        elif q not in norm:
            errors.append(f"claim[{i}] quote not found verbatim: {q[:80]!r}")
    return errors
''',

# ============================================================
# rad/memory/strength.py
# ============================================================
"rad/memory/strength.py": '''
"""Memory strength, decay, sleep consolidation — deterministic + testable.

strength = origin_w * verification_m * freq_boost * exp(-lambda_layer * days_idle)
Formula is PINNED (versioned). Changing it is a generation, not an edit.
"""
import json, math
from datetime import datetime, timezone
from pathlib import Path

ORIGIN_WEIGHT = {"user": 1.0, "observed": 0.8, "inferred": 0.6, "model_generated": 0.4}
VERIFICATION_MULT = {"verified": 1.0, "unverified": 0.85, "contradicted": 0.5}
LAYER_LAMBDA = {"episodic": 0.10, "semantic": 0.02, "procedural": 0.005}
ARCHIVE_THRESHOLD = 0.15
FORMULA_VERSION = 1

def strength(mem: dict, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    last_used = _parse_ts(mem.get("last_used_at", mem.get("created_at", now.isoformat())))
    days_idle = max(0.0, (now - last_used).total_seconds() / 86400)
    base = ORIGIN_WEIGHT.get(mem.get("origin", "model_generated"), 0.4) * \\
           VERIFICATION_MULT.get(mem.get("verification", "unverified"), 0.85)
    freq = 1 + 0.1 * math.log1p(int(mem.get("recall_count", 0)))
    return round(base * freq * math.exp(-LAYER_LAMBDA.get(mem.get("layer", "semantic"), 0.05) * days_idle), 4)

def reinforce(mem: dict, verified: bool | None = None) -> dict:
    mem["recall_count"] = int(mem.get("recall_count", 0)) + 1
    mem["last_used_at"] = datetime.now(timezone.utc).isoformat()
    if verified is True:
        mem["verification"] = "verified"
    return mem

def sleep(memory_root: Path, now: datetime | None = None, drive_sync_fn=None) -> dict:
    """Consolidation pass. Layout: memory_root/long/{layer}/*.json, archive/.
    Deterministic given same files + timestamp. Archive NEVER deletes."""
    now = now or datetime.now(timezone.utc)
    report = {"formula_version": FORMULA_VERSION, "ran_at": now.isoformat(),
              "scanned": 0, "reinforced": 0, "decayed": 0, "archived": 0,
              "strongest": None, "weakest_surviving": None}
    archive_dir = memory_root / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for layer_dir in (memory_root / "long").glob("*"):
        if not layer_dir.is_dir(): continue
        for mf in sorted(layer_dir.glob("*.json")):
            report["scanned"] += 1
            mem = json.loads(mf.read_text(encoding="utf-8"))
            s = strength(mem, now)
            if mem.get("_pending_reinforce"):
                mem = reinforce(mem, verified=mem.pop("_verified_flag", None))
                report["reinforced"] += 1
            elif s < ARCHIVE_THRESHOLD:
                mem["archived_at"] = now.isoformat()
                mem["strength_at_archive"] = s
                (archive_dir / mf.name).write_text(json.dumps(mem, indent=2), encoding="utf-8")
                mf.unlink()
                report["archived"] += 1
                continue
            else:
                report["decayed"] += 1
            mem["strength_at_last_sleep"] = s
            mf.write_text(json.dumps(mem, indent=2), encoding="utf-8")
            if report["strongest"] is None or s > report["strongest"][1]:
                report["strongest"] = [mf.name, s]
            if s >= ARCHIVE_THRESHOLD and (report["weakest_surviving"] is None
                                           or s < report["weakest_surviving"][1]):
                report["weakest_surviving"] = [mf.name, s]

    if drive_sync_fn:
        report["drive_sync"] = drive_sync_fn(memory_root)  # integration hook
    (memory_root / "last_sleep_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report

def _parse_ts(s: str) -> datetime:
    try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return datetime.now(timezone.utc)
''',
}

# ============================================================
# scripts/verify_contrib.py — written by the builder
# ============================================================
VERIFY = r'''#!/usr/bin/env python3
"""Offline verification of the contribution pack. No network, no keys.
    python scripts/verify_contrib.py    (exit 1 on any FAIL)"""
import json, math, sys, tempfile, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = []
def check(name):
    def deco(fn):
        def run():
            try:
                fn(); RESULTS.append((name, "PASS", ""))
            except Exception as e:
                RESULTS.append((name, "FAIL", str(e))); traceback.print_exc()
        run._is_check = True; return run
    return deco

@check("papers.ingest: html->text, arxiv regex, slug")
def _():
    from rad.papers import ingest as ing
    assert ing._html_to_text("<p>hello &amp; bye</p>").strip() == "hello & bye"
    assert ing.ARXIV_RE.search("https://arxiv.org/abs/2501.12948v2").group(1) == "2501.12948"
    assert ing._slug_from_url("https://arxiv.org/abs/2501.12948") == "2501.12948"

def _mk_paper(tmp, slug="t1", text="quote here"):
    from rad.papers import ingest as ing
    ing.PAPERS_DIR = tmp
    d = tmp / slug; d.mkdir(parents=True, exist_ok=True)
    (d / "paper.md").write_text(text, encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(
        {"slug": slug, "title": "T", "source_url": "u", "sha256": "deadbeef"}), encoding="utf-8")

@check("papers.cards: quote verify (true/bogus), illegal transition")
def _():
    from rad.papers import ingest as ing, cards as cds
    tmp = Path(tempfile.mkdtemp()); ing.PAPERS_DIR = tmp; cds.PAPERS_DIR = tmp
    _mk_paper(tmp, text="Reflexion improves task success by 22 percent via verbal feedback.")
    cds.create_card("t1", "technique",
        claims=[{"claim": "improves", "evidence_quote": "improves task success by 22 percent",
                 "claimed_gain": "+22%"}], mechanism="m", implementation_surface=["x"])
    c2 = cds.create_card("t1", "technique",
        claims=[{"claim": "bogus", "evidence_quote": "this quote is not in the paper at all xyz",
                 "claimed_gain": ""}], mechanism="m", implementation_surface=["x"])
    assert c2["claims"][0]["quote_verified"] is False
    try:
        cds.set_card_status("t1", "promoted"); raise AssertionError("should raise")
    except ValueError: pass

@check("papers.battle+ledger: paired run, verdict, CONFIRMED, export")
def _():
    from rad.papers import ingest as ing, cards as cds, battle as btl, ledger as ldg
    tmp = Path(tempfile.mkdtemp())
    for m in (ing, cds): m.PAPERS_DIR = tmp
    btl.PAPERS_DIR = tmp; btl.BATTLE_DIR = tmp / "_battles"
    ldg.PAPERS_DIR = tmp; ldg.LEDGER_FILE = tmp / "_ledger.jsonl"
    _mk_paper(tmp)
    cds.create_card("t1", "technique",
        claims=[{"claim": "c", "evidence_quote": "quote here", "claimed_gain": "+10%"}],
        mechanism="m", implementation_surface=["x"])
    cds.set_card_status("t1", "candidate")
    spec = btl.design_battle("t1", [{"task_id": "a", "prompt": "p", "grader": {}}],
                             {"k": 1}, {"k": 2}, seed=42)
    res = btl.run_battle(spec["battle_id"],
        lambda cfg, task, seed: {"grader_result": {
            "verified_rate": 0.9 if cfg["k"] == 2 else 0.7,
            "false_done": 0.0 if cfg["k"] == 2 else 0.2}, "events": ["e"]},
        dry_run=False)
    assert res["verdict"] == "candidate_wins", res["verdict"]
    entry = ldg.record_battle_outcome(spec["battle_id"])
    assert entry["replication_verdict"] == "CONFIRMED", entry["replication_verdict"]
    assert "rad-replication-ledger" in ldg.export_ledger()

@check("papers.extract: brain extraction with verified quotes")
def _():
    from rad.papers import ingest as ing, cards as cds, extract as ext
    tmp = Path(tempfile.mkdtemp())
    for m in (ing, cds, ext): m.PAPERS_DIR = tmp
    _mk_paper(tmp, slug="t2", text="Verbal reflection boosts agent accuracy substantially.")
    good = json.dumps({"card_type": "technique",
        "claims": [{"claim": "reflection helps", "claimed_gain": "+10%",
                    "evidence_quote": "Verbal reflection boosts agent accuracy substantially."}],
        "mechanism": "self-critique then retry",
        "implementation_surface": ["executor:retry-policy"], "coi_flags": []})
    card = ext.extract_card_brain("t2", brain_fn=lambda p: good)
    assert card["claims"][0]["quote_verified"] is True
    bad_fn = lambda p: json.dumps({"card_type": "technique", "claims": [
        {"claim": "x", "claimed_gain": "", "evidence_quote": "short"}],
        "mechanism": "m", "implementation_surface": [], "coi_flags": []})
    try:
        ext.extract_card_brain("t2", brain_fn=bad_fn); raise AssertionError("should raise")
    except ext.ExtractionError: pass

@check("memory.strength: formula, decay order, sleep archives-never-deletes")
def _():
    from rad.memory import strength as st
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    fresh = {"origin": "user", "verification": "verified", "layer": "semantic",
             "recall_count": 2, "last_used_at": now.isoformat()}
    assert abs(st.strength(fresh, now) - (1.0 * (1 + 0.1 * math.log1p(2)))) < 1e-6
    old = dict(fresh, last_used_at="2026-06-20T00:00:00+00:00")
    assert st.strength(old, now) < st.strength(fresh, now)
    e = dict(old, layer="episodic")
    assert st.strength(e, now) < st.strength(old, now)
    mroot = Path(tempfile.mkdtemp()); (mroot / "long" / "semantic").mkdir(parents=True)
    weak = {"origin": "model_generated", "verification": "contradicted", "layer": "semantic",
            "recall_count": 0, "created_at": "2025-01-01T00:00:00+00:00"}
    (mroot / "long" / "semantic" / "w.json").write_text(json.dumps(weak))
    (mroot / "long" / "semantic" / "s.json").write_text(json.dumps(fresh))
    rep = st.sleep(mroot, now=now)
    assert rep["archived"] == 1 and (mroot / "archive" / "w.json").exists()
    assert not (mroot / "long" / "semantic" / "w.json").exists()
    assert (mroot / "long" / "semantic" / "s.json").exists()

def main():
    print("\n=== VERIFICATION (offline, no keys) ===")
    for name, obj in list(globals().items()):
        if callable(obj) and getattr(obj, "_is_check", False):
            obj()
    fails = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    for name, s, err in RESULTS:
        print(f"  {'PASS' if s == 'PASS' else 'FAIL'}  {name}" + (f"  -- {err[:90]}" if err else ""))
    print(f"\n{len(RESULTS)-fails}/{len(RESULTS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
'''

def main():
    do_verify = "--verify" in sys.argv
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    vp = STAGE / "scripts" / "verify_contrib.py"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(VERIFY.lstrip("\n"), encoding="utf-8")
    print(f"[build] {len(written) + 1} files written to {STAGE}")
    for w in written:
        print(f"  + {w}")
    print(f"  + scripts/verify_contrib.py")

    if not do_verify:
        print("\nNext: python build_contrib.py --verify")
        return
    print("\n=== VERIFICATION (offline, no keys) ===")
    # Add staging to path so we can import from it
    sys.path.insert(0, str(STAGE))
    # Run the verify script
    exec(compile(VERIFY, str(vp), "exec"), {"__name__": "__main__"})

if __name__ == "__main__":
    main()
