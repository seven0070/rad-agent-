"""Paper ingestion: URL/arXiv-id -> sha256-pinned local text.

State: ~/.rad/papers/<slug>/{paper.md, meta.json, card.json}
"""
import hashlib, json, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

PAPERS_DIR = Path.home() / ".rad" / "papers"
ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")

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
    html = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    for k, v in {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": chr(34), "&#39;": chr(39), "&nbsp;": " "}.items():
        html = html.replace(k, v)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()

def ingest_paper(source: str) -> dict:
    """Ingest a paper. Writes paper.md + meta.json. Confirm-first by caller."""
    text, url, slug = fetch_paper_text(source)
    if not text or len(text) < 200:
        raise RuntimeError(f"Extracted text too short ({len(text)} chars) — bad source?")
    paper_dir = PAPERS_DIR / slug
    paper_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "paper.md").write_text(text, encoding="utf-8")
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else text.split("\n")[0][:120].strip()
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
