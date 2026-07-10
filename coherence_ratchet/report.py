"""Leading-indicator report — the honest, measurable outcomes (not ROI).

The book promises leading indicators and insurance, not a return-on-investment claim (Claim 48). This
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

_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _load_ledger(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _first_date(text: str):
    m = _ISO.search(text or "")
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def report(ledger_path: str, *, today: datetime.date, repo: str | None = None) -> dict:
    entries = _load_ledger(ledger_path)
    total = len(entries)
    owned = sum(1 for e in entries if (e.get("owner") or "").strip())
    dated = sum(1 for e in entries if (e.get("repayment_trigger") or "").strip())
    owned_and_dated = sum(
        1 for e in entries
        if (e.get("owner") or "").strip() and (e.get("repayment_trigger") or "").strip()
    )
    by_region: dict[str, int] = {}
    for e in entries:
        by_region[e.get("region", "?")] = by_region.get(e.get("region", "?"), 0) + 1

    overdue = []
    for e in entries:
        d = _first_date(e.get("repayment_trigger", ""))
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
    print("  coherence-debt ledger — leading indicators")
    print(f"    open debt items ....... {r['total']}")
    print(f"    coverage (owned+dated)  {int(r['coverage'] * 100)}%  ({r['owned']} owned, {r['dated']} dated)")
    if r["by_region"]:
        print("    by region:")
        for region, n in sorted(r["by_region"].items(), key=lambda kv: -kv[1]):
            print(f"      {region}: {n}")
    if r["overdue"]:
        print(f"    OVERDUE ({len(r['overdue'])} — repayment trigger date passed):")
        for o in r["overdue"]:
            print(f"      ✗ {o['region']} (owner {o['owner']}) due {o['due']}")
    else:
        print("    overdue ............... none")
    if r["held_commits"] is not None:
        print(f"    ratchet held .......... {r['held_commits']} commits since last accepted breach ({r['last_accepted']})")
    elif r["held_days"] is not None:
        print(f"    ratchet held .......... {r['held_days']} days since last accepted breach ({r['last_accepted']})")


# --- CLI wiring (called from cli.py) ----------------------------------------

DEFAULT_LEDGER = "coherence/coherence-ledger.jsonl"


def register_cli(sub) -> None:
    p = sub.add_parser("report", help="leading-indicator report over the coherence-debt ledger")
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    p.add_argument("--repo", help="git repo, to report ratchet-held-since in commits")
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    r = report(args.ledger, today=datetime.date.today(), repo=getattr(args, "repo", None))
    if args.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        render(r)
    return 0
