"""Does a stale hand-written structure map cause an agent to miss a site a derived one catches?

`res-derived-vs-mapped.md` is the book's answer to Residuality theory's sharpest critique of
structural methods: a mapped abstraction rots, so a method built on one inherits the rot. The
original probe ran three stressors, one trial each, and its figures (3/3 derived, 1/3 stale) are
quoted in Chapter 12's graveyard table and in its prose. Three trials is the weakest sample behind
any figure the manuscript prints, which is why this probe exists.

The design isolates one variable. Both arms get the same task and the same subsystem source. They
differ only in the structure spec they are handed:

    stale_map      lists three of the four sites; written before analytics/report.py existed
    derived_spec   lists all four; regenerated from the code

The scorer is deterministic and has no model in it: the change is a new loyalty tier, and a site
survives only if the produced file for it carries the new tier. A run is a success only when all
four sites do, which is the four-site oracle the original used.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "_fixtures", "derivedmap")

# The four sites that compute an order total. The fourth was added after the map was written, which
# is the whole experiment.
SITES = {
    "orders/checkout.py": "order_total",
    "orders/receipt.py": "receipt_total",
    "orders/revenue.py": "booked_total",
    "orders/analytics/report.py": "cohort_total",
}
MAPPED_SITES = ["orders/checkout.py", "orders/receipt.py", "orders/revenue.py"]

TASK = (
    "Task: the business is adding a PLATINUM loyalty tier at a 30% discount (0.30).\n"
    "Apply it everywhere an order total is computed, so that every total in the system agrees.\n\n"
    "Return the complete updated content of every file you change. Put each file in its own fenced\n"
    "code block, and put the file's path on the line immediately before the block, like this:\n\n"
    "orders/example.py\n"
    "```python\n"
    "...file content...\n"
    "```\n"
)


def _read(rel: str) -> str:
    with open(os.path.join(FIXTURE, rel), encoding="utf-8") as fh:
        return fh.read()


def _source() -> str:
    out = []
    for rel in list(SITES):
        out.append(f"{rel}\n```python\n{_read(rel)}```")
    return "\n\n".join(out)


def _spec(sites) -> str:
    lines = "\n".join(f"  - {rel}  ({SITES[rel]})" for rel in sites)
    return (
        "Structure spec for this subsystem.\n"
        "Sites that compute an order total:\n" + lines + "\n"
    )


STALE_NOTE = (
    "This spec is hand-maintained and was last reviewed some time ago.\n"
)
DERIVED_NOTE = (
    "This spec was regenerated from the current source at this revision.\n"
)


def _source_of(rels) -> str:
    return "\n\n".join(f"{rel}\n```python\n{_read(rel)}```" for rel in rels)


def build_prompt(condition: str) -> str:
    body = (
        "You are changing a Python subsystem. Its full current source is below.\n\n"
        + _source() + "\n\n"
    )
    # The regime the method exists for: the subsystem does not fit in the window, so the spec is the
    # agent's only account of the sites it cannot see. With every file visible the spec's staleness
    # cannot cost anything, because the agent reads the code instead. Measured: 20/20 in all three
    # visible arms, which is the visibility finding again rather than a result about maps.
    partial = (
        "You are changing a Python subsystem. It is too large to show in full. The source of the\n"
        "files you are most likely to need is below.\n\n"
        + _source_of(MAPPED_SITES) + "\n\n"
    )
    if condition == "hidden_stale":
        return partial + STALE_NOTE + _spec(MAPPED_SITES) + "\n" + TASK
    if condition == "hidden_derived":
        return partial + DERIVED_NOTE + _spec(list(SITES)) + "\n" + TASK
    if condition == "stale_map":
        return body + STALE_NOTE + _spec(MAPPED_SITES) + "\n" + TASK
    if condition == "derived_spec":
        return body + DERIVED_NOTE + _spec(list(SITES)) + "\n" + TASK
    if condition == "no_spec":
        # The control the original lacked: source only, no spec at all. Without it a reader cannot
        # tell whether the derived spec helped or the stale one actively hurt.
        return body + TASK
    raise ValueError(condition)


CONDITIONS = ("no_spec", "stale_map", "derived_spec", "hidden_stale", "hidden_derived")


# --- deterministic scorer ---------------------------------------------------

_BLOCK = re.compile(r"^([\w./-]+\.py)\s*\n+```(?:python)?\n(.*?)```", re.S | re.M)


def parse_files(text: str) -> dict:
    """{path: content} for every fenced block whose preceding line names a .py file."""
    out = {}
    for path, body in _BLOCK.findall(text):
        out[path.strip().lstrip("./")] = body
    return out


def score_response(text: str) -> dict:
    """Which of the four total sites carry the new tier, and did the run satisfy the oracle."""
    files = parse_files(text)
    covered = {}
    for rel, func in SITES.items():
        body = files.get(rel)
        # A site counts only if its own file came back carrying the new tier. A change to the shared
        # rate table alone is a real and better answer, so it is scored separately rather than
        # counted as having touched the site.
        covered[rel] = bool(body) and "PLATINUM" in body
    # The fixture deliberately has no shared rate table. The first version of it did, every agent
    # correctly edited that one file, and all three arms scored 20/20: a subsystem whose sites
    # delegate to one table is immune to a stale map, because the correct change is a single edit.
    # Testing staleness needs the divergence that makes staleness cost something.
    via_table = False
    n_sites = sum(covered.values())
    return {
        "files_returned": len(files),
        "sites_covered": n_sites,
        "missed_sites": [r for r, ok in covered.items() if not ok],
        "changed_rate_table": False,
        # The oracle the original used: every site agrees. Editing the shared table reaches every
        # site through one change, so it satisfies the oracle on its own.
        "oracle": n_sites == len(SITES),
        "missed_the_unmapped_site": not covered["orders/analytics/report.py"],
    }


def tally(results_dir: str) -> None:
    present = sorted(d for d in os.listdir(results_dir)
                     if os.path.isdir(os.path.join(results_dir, d)))
    print(f"{'condition':<14} {'n':>3}  {'oracle':>8}  {'via table':>10}  {'missed unmapped':>16}")
    for cond in [c for c in CONDITIONS if c in present] + [d for d in present if d not in CONDITIONS]:
        d = os.path.join(results_dir, cond)
        files = [f for f in sorted(os.listdir(d)) if f.endswith(".raw.json")]
        if not files:
            print(f"{cond:<14} {0:>3}  no responses")
            continue
        sys.path.insert(0, os.path.join(HERE, "experiments", "harness"))
        from dispatch import _text_of
        ok = table = missed = 0
        for name in files:
            text = _text_of(open(os.path.join(d, name), encoding="utf-8").read())
            s = score_response(text)
            ok += s["oracle"]; table += s["changed_rate_table"]; missed += s["missed_the_unmapped_site"]
        n = len(files)
        print(f"{cond:<14} {n:>3}  {ok:>6}/{n}  {table:>8}/{n}  {missed:>14}/{n}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--print":
        print(build_prompt(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)
