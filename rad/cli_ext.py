"""rad cli_ext — contribution command surface, dispatcher-agnostic.

Wire into ANY dispatcher with one call:  register_on(dispatcher)
Or run standalone:                       python -m rad.cli_ext <verb> [...]

L5: every store path injectable — CLI never hardcodes home in tests.
"""
import argparse, json, sys
from pathlib import Path

COMMANDS = {}          # L1: registry dict, not name-scan

def command(name, help_=""):
    def deco(fn):
        COMMANDS[name] = {"fn": fn, "help": help_}
        return fn
    return deco

def register_on(dispatcher) -> dict:
    """One-line hook: your dispatcher gets every verb in COMMANDS."""
    for name, spec in COMMANDS.items():
        dispatcher[name] = spec["fn"]
    return COMMANDS

# ---------------- paper verbs ----------------

@command("paper-add", "ingest a paper: paper-add <arxiv-id|url>")
def paper_add(args, papers_dir: Path | None = None):
    from rad.papers.ingest import ingest_paper, PAPERS_DIR
    if papers_dir:
        import rad.papers.ingest as ing
        ing.PAPERS_DIR = Path(papers_dir)
    meta = ingest_paper(args[0])
    print(f"[ok] ingested: {meta['title']}\n  slug={meta['slug']} sha256={meta['sha256'][:16]} chars={meta['char_count']}")
    print(f"  next: python -m rad.cli_ext paper-card {meta['slug']}")
    return meta

@command("paper-list", "list ingested papers")
def paper_list(args, papers_dir: Path | None = None):
    from rad.papers import ingest as ing, cards as cds
    if papers_dir:
        ing.PAPERS_DIR = Path(papers_dir); cds.PAPERS_DIR = ing.PAPERS_DIR
    papers = ing.list_papers()
    if not papers:
        print("no papers — try: paper-add 2501.12948"); return []
    for p in papers:
        card = cds.get_card(p["slug"])
        status = card["status"] if card else "ingested"
        print(f"  [{status:>10}] {p['slug']:<24} {p['title'][:56]}")
    return papers

@command("paper-card", "show/create technique card: paper-card <slug> [--create]")
def paper_card(args, papers_dir: Path | None = None, brain_fn=None):
    from rad.papers import ingest as ing, cards as cds
    if papers_dir:
        ing.PAPERS_DIR = Path(papers_dir); cds.PAPERS_DIR = ing.PAPERS_DIR
    slug = args[0]
    if "--create" in args:
        if brain_fn is None:
            from rad.home import RadHome
            from rad.router import BrainRouter
            from rad.integrate.hooks import make_brain_fn
            brain_fn = make_brain_fn(BrainRouter(home=RadHome()))
        from rad.papers.extract import extract_card_brain
        card = extract_card_brain(slug, brain_fn)
        print(f"[ok] card {card['card_id']} ({card['status']}) — quotes verified: "
              f"{sum(1 for c in card['claims'] if c['quote_verified'])}/{len(card['claims'])}")
        return card
    card = cds.get_card(slug)
    print(json.dumps(card, indent=2) if card else f"no card for {slug!r}")
    return card

@command("paper-ledger", "replication ledger: paper-ledger [--export PATH]")
def paper_ledger(args, papers_dir: Path | None = None):
    from rad.papers import ledger as ldg
    if papers_dir:
        ldg.PAPERS_DIR = Path(papers_dir)
        ldg.LEDGER_FILE = ldg.PAPERS_DIR / "_ledger.jsonl"
    entries = ldg.read_ledger()
    if not entries:
        print("ledger empty — completed battles land here"); return []
    for e in entries:
        icon = {"CONFIRMED": "[+]", "NOT_REPLICATED": "[!]", "NO_CLAIM_TO_TEST": "[-]", "INCONCLUSIVE": "[?]"}.get(e["replication_verdict"], "[?]")
        note = f" (amended: {e['amendments'][-1]['was']}->{e['replication_verdict']})" if e.get("amendments") else ""
        print(f"  {icon} {e['paper_title'][:48]:<48} -> {e['replication_verdict']}{note}")
    if "--export" in args:
        out = args[args.index("--export") + 1]
        ldg.export_ledger(out); print(f"  exported -> {out}")
    return entries

# ---------------- relay / sovereignty / federation ----------------

@command("relay-test", "classify + route a prompt through Relay: relay-test \"text\" [--open]")
def relay_test(args):
    from rad.routing.relay import classify_request, route
    text = args[0] if args else "fix this python bug in my api"
    pref = "open" if "--open" in args else "default"
    cls = classify_request(text)
    dec = route(cls, policy_pref=pref)
    print(f"  class={cls['task_class']} decided_in={cls['decision_ms']}ms")
    print(f"  route: {dec['route_selected']}  chain={dec['fallback_chain']}")
    return dec

@command("sovereignty", "HEARTH report: sovereignty [objective-dir]")
def sovereignty(args):
    from rad.sovereignty.audit import audit_objective
    rep = audit_objective(Path(args[0]) if args else None)
    print(f"  objectives={rep['objectives']} fully_internal={rep['fully_sovereign']} "
          f"internal_ratio={rep['internal_ratio']}")
    print(f"  port_calls={rep['port_calls']}")
    print(f"  law: {rep['law']}")
    return rep

@command("federation-status", "federation bundles/verdicts summary")
def federation_status(args):
    from rad.home import RadHome
    base = RadHome().root / "federation" if Path.home().joinpath(".rad").exists() else None
    print("  federation state: wire cross_audit runs into your task loop; "
          "verdicts land in the cross-ledger (RFC-005 P4)")
    return {"note": "P4 pending"}

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print("rad cli_ext — contribution verbs:\n")
        for name, spec in COMMANDS.items():
            print(f"  {name:<20} {spec['help']}")
        return 0
    verb, rest = argv[0], argv[1:]
    if verb not in COMMANDS:
        print(f"unknown verb {verb!r}; try --help"); return 1
    COMMANDS[verb]["fn"](rest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
