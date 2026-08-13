"""Leading-indicator report — the honest, measurable outcomes (not ROI).

The report presents exposure and ownership state, not a return-on-investment claim. This
command reads the coherence-debt ledger (and, if given, the budgets and a git repo) and reports the
process metrics a team CAN stand behind:

  - ledger coverage: how much accepted debt is actually owned AND dated (the discipline working)
  - open debt items, by region
  - overdue items: a repayment trigger whose date has passed
  - held-since: how long the ratchet has held (days since the last accepted breach; commits if a repo)

These are deterministic reads of artefacts the team already produces. They are process indicators, not
savings — the honesty guard the whole method rests on.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys

_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _load_ledger(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    # The ledger is JSON Lines: one object per line. A pretty-printed entry pasted in by hand yields
    # lines that parse as fragments — a bare string parses cleanly and then fails on .get, which used
    # to surface as a traceback. Name the line instead, so the reader can fix the file.
    out = []
    malformed = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                malformed.append(lineno)
                continue
            if not isinstance(entry, dict):
                malformed.append(lineno)
                continue
            out.append(entry)
    if malformed:
        shown = ", ".join(str(n) for n in malformed[:5])
        more = "" if len(malformed) <= 5 else f" (and {len(malformed) - 5} more)"
        print(f"  ⚠ {path}: {len(malformed)} line(s) are not one JSON object per line and were "
              f"skipped — line {shown}{more}", file=sys.stderr)
    return out


def _first_date(text: str):
    m = _ISO.search(text or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _open_entries(records: list[dict]) -> list[dict]:
    """The open register: entries not themselves closed, and not superseded by a closing record.

    The ledger is append-only, so a closure arrives as a later record carrying `closes` (the original
    entry's `when`). Filtering only on an entry's own status would leave the original standing open
    for ever beside its own closure.
    """
    closed_keys = {
        (record.get("region"), record.get("closes"))
        for record in records
        if record.get("status") == "closed" and record.get("closes")
    }
    return [
        record for record in records
        if record.get("status", "accepted") != "closed"
        and (record.get("region"), record.get("when")) not in closed_keys
    ]


def report(ledger_path: str, *, today: datetime.date, repo: str | None = None) -> dict:
    entries = _open_entries(_load_ledger(ledger_path))
    total = len(entries)
    owned = sum(1 for e in entries if (e.get("owner") or "").strip())
    dated = sum(1 for e in entries if (e.get("repayment_trigger") or "").strip())
    owned_and_dated = sum(
        1 for e in entries
        if (e.get("owner") or "").strip() and (e.get("repayment_trigger") or "").strip()
    )
    by_region: dict[str, int] = {}
    by_exposure: dict[str, int] = {}
    for e in entries:
        by_region[e.get("region", "?")] = by_region.get(e.get("region", "?"), 0) + 1
        tier = e.get("exposure_tier", "NEEDS_ASSESSMENT")
        by_exposure[tier] = by_exposure.get(tier, 0) + 1

    # The review date is the entry's own commitment to re-examine, and it is mandatory on accept.
    # The repayment trigger is often an event ("before contract v2 becomes the default") that carries
    # no date at all, so reading the trigger text alone left every event-triggered entry permanently
    # unchaseable. Read the review date first and fall back to a date parsed from the trigger.
    overdue = []
    for e in entries:
        d = _first_date(e.get("review_date", "")) or _first_date(e.get("repayment_trigger", ""))
        if d is not None and d < today:
            overdue.append({"region": e.get("region"), "owner": e.get("owner"), "due": d.isoformat()})

    whens = [d for d in (_first_date(e.get("when", "")) for e in entries) if d]
    last_accepted = max(whens) if whens else None
    held_days = (today - last_accepted).days if last_accepted else None
    held_commits = None
    if repo and last_accepted:
        try:
            out = subprocess.run(
                ["git", "-C", repo, "rev-list", "--count", f"--since={last_accepted.isoformat()}", "HEAD"],
                capture_output=True, text=True, timeout=15).stdout.strip()
            held_commits = int(out) if out.isdigit() else None
        except Exception:
            held_commits = None

    return {
        "total": total,
        "owned": owned,
        "dated": dated,
        "coverage": round(owned_and_dated / total, 3) if total else 1.0,
        "by_region": by_region,
        "by_exposure": by_exposure,
        "overdue": overdue,
        "last_accepted": last_accepted.isoformat() if last_accepted else None,
        "held_days": held_days,
        "held_commits": held_commits,
    }


def render(r: dict) -> None:
    if r["total"] == 0:
        print("  coherence-debt ledger is empty — no accepted debt on the books.")
        print("  (an empty ledger with the ratchet in CI is the clean state, not a missing one.)")
        return
    print("  coherence-debt ledger — exposure and ownership")
    print(f"    open debt items ....... {r['total']}")
    print(f"    coverage (owned+dated)  {int(r['coverage'] * 100)}%  ({r['owned']} owned, {r['dated']} dated)")
    if r["by_region"]:
        print("    by region:")
        for region, n in sorted(r["by_region"].items(), key=lambda kv: -kv[1]):
            print(f"      {region}: {n}")
    if r["by_exposure"]:
        print("    exposure:")
        for tier in ("HIGH", "MODERATE", "LOW", "NEEDS_ASSESSMENT"):
            if tier in r["by_exposure"]:
                print(f"      {tier}: {r['by_exposure'][tier]}")
    if r["overdue"]:
        # The date tested is the review date, falling back to a date parsed out of the trigger
        # text; labelling it "repayment trigger" named the fallback and misreported the usual case.
        print(f"    OVERDUE ({len(r['overdue'])} — review date passed):")
        for o in r["overdue"]:
            print(f"      ✗ {o['region']} (owner {o['owner']}) due {o['due']}")
    else:
        print("    overdue ............... none")
    if r["held_commits"] is not None:
        print(f"    ratchet held .......... {r['held_commits']} commits since last accepted breach ({r['last_accepted']})")
    elif r["held_days"] is not None:
        print(f"    ratchet held .......... {r['held_days']} days since last accepted breach ({r['last_accepted']})")


# --- CLI wiring (called from cli.py) ----------------------------------------

from .exitcodes import EXIT_CROSSED, EXIT_HELD, EXIT_REFUSED  # noqa: F401

DEFAULT_LEDGER = "coherence/coherence-ledger.jsonl"


def register_cli(sub) -> None:
    p = sub.add_parser("report", help="exposure and ownership report over the coherence-debt ledger")
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    p.add_argument("--repo", help="git repo, to report ratchet-held-since in commits")
    p.add_argument("--as-of", dest="as_of",
                   help="report as at this date (YYYY-MM-DD) instead of today, for a reproducible run")
    p.add_argument("--json", action="store_true")

    c = sub.add_parser("close", help="close open ledger entries for a region (appends, never edits)")
    c.add_argument("region")
    c.add_argument("--ledger", default=DEFAULT_LEDGER)
    c.add_argument("--by", required=True, help="who closed it")
    c.add_argument("--reason", required=True, help="why it is closed (repaid, superseded, withdrawn)")


def run_cli(args) -> int:
    today = datetime.date.today()
    if getattr(args, "as_of", None):
        try:
            today = datetime.date.fromisoformat(args.as_of)
        except ValueError:
            print(f"--as-of must be YYYY-MM-DD, got {args.as_of!r}", file=sys.stderr)
            return 2
    r = report(args.ledger, today=today, repo=getattr(args, "repo", None))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        render(r)
    return 0


def run_close_cli(args) -> int:
    from .ratchet import close_ledger_entry

    closed = close_ledger_entry(
        args.ledger, region=args.region, when=datetime.date.today().isoformat(),
        by=args.by, reason=args.reason,
    )
    if not closed:
        # Nothing matched, which is a usage error and not a line being crossed. Exit 1 is reserved
        # for a ceiling an owner set or a rule a person ratified; using it here would make a typo in
        # --region indistinguishable from real structural worsening in a pipeline.
        print(f"no open ledger entry for region {args.region!r} in {args.ledger}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"closed {closed} entr{'y' if closed == 1 else 'ies'} for {args.region} → {args.ledger}")
    return 0
