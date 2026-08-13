"""A scripted change history for the checkout-pricing fixture.

Builds a throwaway git repository in a temp directory, materialises the
06-checkout-cycle state, and replays a deterministic commit sequence in which
checkout.py and revenue_report.py co-change five times with no import edge
between them — the hyperliminal pair the book describes: every campaign or
rate tweak in checkout forces a matching edit in the revenue report, because
the report re-implements the totals instead of importing them.

The sequence is authored, not mined: ten commits, eighteen module touches,
so the history lens reads contagion 18/10 = 1.8 and exactly one hyperliminal
pair. The final tree is byte-identical to playground/_states/06-checkout-cycle,
so the snapshot printed at the end is the book's chapter 5 snapshot with the
change-history block filled in.

Run from ratchet-mvp/:  python3 experiments/scripts/checkout_history_repo.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "playground"))

import checkout_states as cs
from coherence_ratchet.cli import main as ratchet_main

PKG = "checkout_pricing"


def _git(repo: str, *args: str) -> None:
    subprocess.run(
        ["git", "-C", repo, *args],
        check=True, capture_output=True, text=True,
        env={**os.environ,
             "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.com",
             "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.com",
             "GIT_AUTHOR_DATE": "2026-07-01T09:00:00+08:00",
             "GIT_COMMITTER_DATE": "2026-07-01T09:00:00+08:00"},
    )


def _write(repo: str, rel: str, text: str) -> None:
    path = os.path.join(repo, PKG, rel)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _marked(base: str, note: str) -> str:
    """An intermediate revision of a file: the canonical text plus a trailing
    calibration comment that a later commit removes. The markers only exist to
    give git a real diff per scripted commit; the final tree carries none."""
    return base + f"# calibration: {note}\n"


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="checkout-history-")
    os.makedirs(os.path.join(tmp, PKG), exist_ok=True)
    _git(tmp, "init", "-q")

    final = {rel.split("/", 1)[1]: src for rel, src in cs.CYCLE.items()}
    clean = {rel.split("/", 1)[1]: src for rel, src in cs.CLEAN.items()}

    # c1 — initial import of the seam (all four modules, pre-cycle pricing).
    for rel in ("pricing.py", "checkout.py", "receipt.py", "revenue_report.py"):
        base = clean if rel == "pricing.py" else final
        _write(tmp, rel, _marked(base[rel], "v0"))
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-q", "-m", "initial import of the checkout-pricing seam")

    # c2..c5 — four campaign/rate calibrations: checkout.py changes, and the
    # revenue report must change with it (it re-implements the totals).
    co_change = [
        "relaunch campaign rate calibrated",
        "june rate window adjusted",
        "campaign rounding reconciled with finance",
        "final pre-launch calibration",
    ]
    for n, note in enumerate(co_change, start=1):
        _write(tmp, "checkout.py", _marked(final["checkout.py"], f"v{n}"))
        _write(tmp, "revenue_report.py", _marked(final["revenue_report.py"], f"v{n}"))
        _git(tmp, "add", "-A")
        _git(tmp, "commit", "-q", "-m", f"{note} (checkout + revenue report)")

    # c6 — a rounding-policy pass touches pricing and receipt together.
    _write(tmp, "pricing.py", _marked(clean["pricing.py"], "rounding pass"))
    _write(tmp, "receipt.py", _marked(final["receipt.py"], "rounding pass"))
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-q", "-m", "rounding policy pass (pricing + receipt)")

    # c7 — the deadline change: pricing reaches back into checkout. This is the
    # commit that closes the cycle; pricing.py lands in its canonical 06 form.
    _write(tmp, "pricing.py", final["pricing.py"])
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-q", "-m", "read campaign schedule from checkout (deadline)")

    # c8..c10 — single-file tidy-ups that land each remaining module in its
    # canonical form (markers removed).
    for rel, msg in (
        ("receipt.py", "receipt tidy-up"),
        ("checkout.py", "checkout tidy-up"),
        ("revenue_report.py", "revenue report tidy-up"),
    ):
        _write(tmp, rel, final[rel])
        _git(tmp, "add", "-A")
        _git(tmp, "commit", "-q", "-m", msg)

    # The tree must now be byte-identical to the committed 06 state.
    for rel, src in final.items():
        with open(os.path.join(tmp, PKG, rel), encoding="utf-8") as f:
            assert f.read() == src, f"{rel} does not match 06-checkout-cycle"

    print(f"history repo: {tmp}  (10 commits, 18 module touches)")
    print(f"$ coherence-ratchet measure {os.path.join(tmp, PKG)} --repo {tmp}")
    return ratchet_main(["measure", os.path.join(tmp, PKG), "--repo", tmp])


if __name__ == "__main__":
    raise SystemExit(main())
