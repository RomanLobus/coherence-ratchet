"""Command line for the coherence ratchet.

    coherence-ratchet measure  <path> [--repo DIR] [--json]
    coherence-ratchet init     <path> [--repo DIR] [--budgets FILE]
    coherence-ratchet check    <path> [--repo DIR] [--budgets FILE] [--tighten]
                               [--accept --owner NAME --trigger TEXT [--note TEXT] [--ledger FILE]]
    coherence-ratchet history  <path> --repo DIR [--samples 24] [--json [OUT]]
    coherence-ratchet compare  <original> <replacement> [--strategy FILE] [--json]
    coherence-ratchet apidiff  <old-tree> <new-tree> [--json]
    coherence-ratchet ground   <path> [--target FILE] [--check] [--dry-run]
    coherence-ratchet advise   <path> [--staged | --diff RANGE | --patch FILE | --stdin]
                               [--fail-on ratified|any|none] [--format text|json]
    coherence-ratchet serve    <path>   # the same standing, to a coding agent over MCP

`check` exits non-zero when a watched signal has worsened past its ceiling — the same contract as a
coverage ratchet failing CI. `--accept` turns a trip into an owned, dated coherence-debt ledger entry
instead of a failure (exit 0), so accepting decay is a deliberate, recorded act.

`ground` writes ratified intent into the files coding agents read and `ground --check` fails when it
no longer describes the tree. `advise` measures a change against what already exists and hands the
finding back. Together they close the loop: derive, ratify, ground, author, detect, hold.

Exit codes are uniform and defined in `exitcodes.py`: 0 held, 1 crossed, 2 refused, 3 advisory,
4 not measured. Two rules give them meaning — a candidate never exits non-zero, and a failure never
reads as a clean result.
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import json
import sys

from .exitcodes import (  # noqa: F401  (the contract; re-exported for consumers)
    EXIT_ADVISORY, EXIT_CROSSED, EXIT_HELD, EXIT_NOT_MEASURED, EXIT_REFUSED,
)
from .paths import SourceTreeError
from .ratchet import (
    Budget, BudgetExists, BudgetMalformed, BudgetMissing, append_ledger, check,
    decompose, init_budget, tighten,
)
from .signals import measure_all

DEFAULT_BUDGETS = "coherence/budgets.json"
DEFAULT_LEDGER = "coherence/coherence-ledger.jsonl"


def _decorate(metric: str, d: dict) -> str:
    """' (num x / den y)' decomposition suffix for a ratio metric, '' when not applicable.
    Every ratio is printed with its raw counts — density alone misleads under volume inflation."""
    dec = decompose(metric, d)
    return f" ({dec[2]})" if dec else ""


def _print_snapshot(snap) -> None:
    d = snap.to_dict()
    print("  duplication (function-level)")
    print(f"    functions ............ {d['total_functions']}")
    print(f"    redundant clusters ... {d['redundant_clusters']}")
    print(f"    redundant functions .. {d['redundant_functions']}")
    print(f"    duplication ratio .... {d['duplication_ratio']}{_decorate('duplication_ratio', d)}")
    if "cycle_ratio" in d:
        print("  architecture")
        print(f"    modules .............. {d['n_modules']}")
        print(f"    cycle ratio .......... {d['cycle_ratio']}{_decorate('cycle_ratio', d)}  (ratcheted)")
        print(f"    coupling density ..... {d['coupling_density']}{_decorate('coupling_density', d)}  (diagnostic)")
        print(f"    max fan-in ratio ..... {d['max_fan_in_ratio']}{_decorate('max_fan_in_ratio', d)}  (diagnostic)")
        print("  connascence")
        print(f"    shared literals ...... {d['connascence_shared']}  (ratcheted)")
        if "third_party_imports" in d:
            print("  dependencies")
            print(f"    third-party imports .. {d['third_party_imports']}  (informational)")
            print(f"    single-use ........... {d['single_use_third_party']}  (informational)")
        if d.get("hyperliminal_pairs"):
            print("  change history")
            print(f"    hyperliminal pairs ... {d['hyperliminal_pairs']}  (diagnostic)")
            print(f"    contagion (mean) ..... {d['contagion_mean']}  (diagnostic)")
        elif getattr(snap, "history_error", None):
            # Without this the block simply disappears, which is what a genuinely clean history
            # looks like too.
            print("  change history")
            print(f"    ⚠ not measured: {snap.history_error}")


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("coherence-ratchet")
    except Exception:
        return "unknown (not installed as a distribution)"


def main(argv: list[str] | None = None) -> int:
    """Dispatch, turning a refusal into an exit code rather than a traceback.

    A reader is told to put `check` in CI. That instruction is only safe if every way the tool can
    fail to measure produces a named error and a non-zero exit, never a clean-looking zero reading.
    """
    try:
        return _main(argv)
    except SourceTreeError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except BudgetMissing as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    except BudgetMalformed as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED


def _print_measurement(snap) -> None:
    """An imported reading prints its producer first. These counts are another tool's claim."""
    produced = (snap.meta.get("produced_by") or {})
    print(f"  imported from {produced.get('tool', 'unknown')} {produced.get('version', '')} "
          f"({produced.get('producer_schema', 'schema unknown')})")
    for name, value in sorted(snap.to_dict().items()):
        print(f"    {name} ... {value:g}")
    print("  every line above is a candidate; this tool did not read that code")


def _init_from_measurement(args) -> int:
    import os

    from .interchange import ImportRefused, budget_from_measurement, load_measurement

    try:
        measurement = load_measurement(args.from_measurement)
    except ImportRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED

    prior = None
    if os.path.exists(args.budgets):
        if not args.force:
            print(f"\n{args.budgets} already exists. Re-baselining replaces the enforced ceilings, "
                  "so it needs --force together with --by and --reason.", file=sys.stderr)
            return EXIT_REFUSED
        try:
            prior = Budget.load(args.budgets).ceilings
        except (OSError, ValueError, KeyError, BudgetMalformed, BudgetMissing):
            prior = None

    budget = budget_from_measurement(
        measurement, author=args.by, reason=args.reason,
        set_at=datetime.date.today().isoformat(), prior=prior,
    )
    budget.save(args.budgets)
    print(f"baseline budget written to {args.budgets} from {args.from_measurement}")
    for name, value in sorted(budget.ceilings.items()):
        print(f"  {name} <= {value:g}")
    print("\nThese ceilings hold another tool's counts. They are raw counts, so no denominator can "
          "dilute them, and nothing here has been ratified.")
    return EXIT_HELD


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="coherence-ratchet")
    p.add_argument("--version", action="version", version=f"coherence-ratchet {_version()}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pm = sub.add_parser("measure", help="measure a tree and print the signal portfolio")
    pm.add_argument("path")
    pm.add_argument("--repo", help="git repo for hyperliminal/contagion signals")
    pm.add_argument("--similarity", type=float,
                    help="near-duplicate threshold; the shipped default is calibrated against the "
                         "playground fixture, and `calibrate` measures one for your own code")
    pm.add_argument("--json", action="store_true")

    pi = sub.add_parser("init", help="write the baseline budget from the portfolio")
    pi.add_argument("path", nargs="?",
                    help="the package directory to measure; omit only with --from-measurement")
    pi.add_argument("--from-measurement", dest="from_measurement",
                    help="baseline from another tool's imported counts instead of measuring here")
    pi.add_argument("--repo")
    pi.add_argument("--budgets", default=DEFAULT_BUDGETS)
    pi.add_argument("--by", help="who set these ceilings (required)")
    pi.add_argument("--reason", help="why this baseline was taken")
    pi.add_argument("--force", action="store_true",
                    help="replace an existing budgets file, retaining the prior ceilings")

    pc = sub.add_parser("check", help="fail if coherence worsened past the budget")
    pc.add_argument("path", nargs="?",
                    help="the package directory to measure; omit only with --from-measurement")
    pc.add_argument("--from-measurement", dest="from_measurement",
                    help="compare another tool's imported counts instead of measuring here")
    pc.add_argument("--repo")
    pc.add_argument("--budgets", default=DEFAULT_BUDGETS)
    pc.add_argument("--tighten", action="store_true", help="ratchet ceilings down on improvement")
    pc.add_argument("--by", help="who lowered the ceilings, recorded in the budgets file (--tighten)")
    pc.add_argument("--accept", action="store_true", help="record the breach as owned coherence debt instead of failing")
    pc.add_argument("--owner", help="owner of the accepted debt (required with --accept)")
    pc.add_argument("--trigger", help="dated/condition repayment trigger (required with --accept)")
    pc.add_argument("--region", default="", help="region label for the ledger entry")
    pc.add_argument("--note", default="", help="free-text note for the ledger entry")
    pc.add_argument("--ledger", default=DEFAULT_LEDGER)
    for dimension in ("volatility", "coordination-span", "criticality", "discoverability", "blast-radius"):
        pc.add_argument(f"--{dimension}", choices=["low", "medium", "high"])
    pc.add_argument("--evidence", action="append", default=[], help="evidence for the exposure assessment")
    pc.add_argument("--confidence", choices=["low", "medium", "high"])
    pc.add_argument("--review-date", help="ISO date for the next review")
    pc.add_argument("--status", default="accepted", choices=["accepted", "repaying", "closed"])
    pc.add_argument("--repayment-feasibility", choices=["low", "medium", "high"])
    pc.add_argument("--needs-assessment", action="store_true",
                    help="record the entry with a dimension left unassessed (reports NEEDS_ASSESSMENT)")

    # Every module below lives in this package; none is an optional third-party import. Swallowing
    # the exception here used to delete a whole verb from the CLI on any import error, silently and
    # with every test still passing, so the command table printed in the book was unenforced. A
    # failure to register is now a failure to run.
    for _name in ("selfmodel", "gate", "comparison", "report", "history", "apidiff", "ground", "advise", "mcp", "calibrate", "interchange"):
        importlib.import_module("." + _name, __package__).register_cli(sub)

    args = p.parse_args(argv)

    if args.cmd == "measure":
        snap = measure_all(args.path, repo=getattr(args, "repo", None),
                           sim_threshold=getattr(args, "similarity", None))
        if args.json:
            print(json.dumps(snap.to_dict(), indent=2, sort_keys=True))
        else:
            _print_snapshot(snap)
        return 0

    if args.cmd == "init":
        if not args.by:
            print("\ninit requires --by NAME: the budgets file is the only artefact CI enforces, "
                  "so it records who set the ceilings.", file=sys.stderr)
            return 2
        # Re-baselining is the one path that lets worsening in without a signed decision, so the
        # reason is not decoration. It was unenforced while this message, the appendix, and the
        # honest-metric argument all said it was required.
        if args.force and not args.reason:
            print("\nre-baselining requires --reason TEXT: --force replaces the enforced ceilings, "
                  "and the reason is what distinguishes a considered re-baseline from a silent one.",
                  file=sys.stderr)
            return 2
        if args.from_measurement:
            return _init_from_measurement(args)
        if not args.path:
            print("\ninit needs a path to measure, or --from-measurement FILE to baseline from "
                  "another tool's imported counts.", file=sys.stderr)
            return EXIT_REFUSED
        try:
            budget = init_budget(
                args.path, args.budgets, repo=getattr(args, "repo", None),
                author=args.by, reason=args.reason,
                set_at=datetime.date.today().isoformat(), force=args.force,
            )
        except BudgetExists as exc:
            print(f"\n{exc} already exists. Re-baselining replaces the enforced ceilings, so it "
                  "needs --force together with --by and --reason; the prior ceilings are kept in "
                  "the file.", file=sys.stderr)
            return 2
        print(f"baseline budget written to {args.budgets}")
        for m, v in sorted(budget.ceilings.items()):
            num = budget.numerators.get(m)
            detail = f"  (from {num:g})" if num is not None else ""
            print(f"  {m} <= {v}{detail}")
        if budget.provenance.get("prior"):
            print(f"  re-baselined by {args.by}; prior ceilings retained in the file")
        return 0

    if args.cmd == "check":
        if args.from_measurement:
            from .interchange import ImportRefused, load_measurement
            try:
                snap = load_measurement(args.from_measurement)
            except ImportRefused as exc:
                print(f"refused: {exc}", file=sys.stderr)
                return EXIT_REFUSED
            budget = Budget.load(args.budgets)
            breaches, improvements = budget.breaches(snap), budget.improvements(snap)
            _print_measurement(snap)
        elif not args.path:
            print("\ncheck needs a path to measure, or --from-measurement FILE to compare "
                  "another tool's imported counts.", file=sys.stderr)
            return EXIT_REFUSED
        else:
            snap, breaches, improvements = check(args.path, args.budgets,
                                                 repo=getattr(args, "repo", None))
            _print_snapshot(snap)
        if breaches:
            print("\nRATCHET TRIPPED — coherence worsened past budget:")
            for b in breaches:
                detail = f" ({b.detail})" if b.detail else ""
                print(f"  ✗ {b.metric}: {b.observed}{detail} > ceiling {b.ceiling} (+{b.delta})")
            if args.accept:
                dimensions = {
                    "volatility": args.volatility,
                    "coordination_span": args.coordination_span,
                    "criticality": args.criticality,
                    "discoverability": args.discoverability,
                    "blast_radius": args.blast_radius,
                }
                mandatory = (args.owner and args.trigger and args.review_date and args.confidence
                             and args.repayment_feasibility and args.evidence)
                complete = all(dimensions.values())
                # A dimension with no evidence yet is a real state, and the ledger can represent it:
                # the entry reports NEEDS_ASSESSMENT until the evidence arrives. It stays an explicit
                # act, so the accountable fields are still mandatory and the reader must ask for it.
                if not mandatory or not (complete or args.needs_assessment):
                    print(
                        "\n--accept requires owner, trigger, review date, all five exposure dimensions, "
                        "evidence, confidence, and repayment feasibility. To record an entry whose "
                        "evidence is still missing for a dimension, pass --needs-assessment and leave "
                        "that dimension out; the entry reports NEEDS_ASSESSMENT until it is assessed.",
                        file=sys.stderr,
                    )
                    return 2
                append_ledger(
                    args.ledger,
                    when=datetime.date.today().isoformat(),
                    region=args.region or args.path,
                    breaches=breaches,
                    owner=args.owner,
                    repayment_trigger=args.trigger,
                    note=args.note,
                    exposure=dimensions,
                    evidence=args.evidence,
                    confidence=args.confidence,
                    review_date=args.review_date,
                    status=args.status,
                    repayment_feasibility=args.repayment_feasibility,
                )
                print(f"\nAccepted as coherence debt → {args.ledger}")
                print(f"  owner: {args.owner}   repayment trigger: {args.trigger}")
                return 0
            print("\nReuse the existing pattern, or accept the debt: --accept --owner NAME --trigger TEXT")
            return 1
        if improvements:
            print("\nCoherence improved:")
            d = snap.to_dict()
            for m, (old, new) in sorted(improvements.items()):
                dec = decompose(m, d)
                detail = f" ({dec[2]})" if dec else ""
                print(f"  ✓ {m}: {old} -> {new}{detail}")
            if args.tighten:
                tightened, declined = tighten(
                    Budget.load(args.budgets), snap,
                    by=getattr(args, "by", None), at=datetime.date.today().isoformat())
                tightened.save(args.budgets)
                lowered = [m for m in improvements if m not in declined]
                if lowered:
                    print(f"ratchet tightened: {', '.join(sorted(lowered))} lowered to the new floor.")
                for m, why in sorted(declined.items()):
                    print(f"  ⚠ {m} not tightened: {why}")
                if declined and not lowered:
                    print("ratchet held: no ceiling was lowered.")
        print("\nOK — coherence held.")
        return 0

    if args.cmd and args.cmd.startswith("selfmodel"):
        from . import selfmodel as _sm

        return _sm.run_cli(args)

    if args.cmd == "gate":
        from . import gate as _gate

        return _gate.run_cli(args)

    if args.cmd == "compare":
        from . import comparison as _comparison

        return _comparison.run_cli(args)

    if args.cmd == "report":
        from . import report as _report

        return _report.run_cli(args)

    if args.cmd == "close":
        from . import report as _report

        return _report.run_close_cli(args)

    if args.cmd == "history":
        from . import history as _history

        return _history.run_cli(args)

    if args.cmd == "apidiff":
        from . import apidiff as _apidiff

        return _apidiff.run_cli(args)

    if args.cmd == "ground":
        from . import ground as _ground

        return _ground.run_cli(args)

    if args.cmd == "advise":
        from . import advise as _advise

        return _advise.run_cli(args)

    if args.cmd == "serve":
        from . import mcp as _mcp

        return _mcp.run_cli(args)

    if args.cmd == "calibrate":
        from . import calibrate as _calibrate

        return _calibrate.run_cli(args)

    if args.cmd == "import":
        from . import interchange as _interchange

        return _interchange.run_cli(args)

    # A verb that registered and was never wired here used to fall out silently on exit 2, which
    # reads as a usage error the caller made rather than a gap in this table.
    print(f"'{args.cmd}' registered a parser and has no dispatch; this is a defect in the CLI table.",
          file=sys.stderr)
    return EXIT_NOT_MEASURED


if __name__ == "__main__":
    sys.exit(main())
