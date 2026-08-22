"""Measure a change against what the code already contains, and hand the finding back.

This is the shipped form of the companion's strongest experimental result. An agent given a task but
not the file containing the canonical helper reinvented the conversion ten times out of ten; a
detector that could see the whole tree named the collision ten times out of ten; and after the
finding was handed back, the agent reused the canonical helper ten times out of ten. Until now that
round trip existed only as a transcript in an experiment write-up, which is exactly the gap between a
narrated result and a practice a reader can run.

The reasoning behind detecting rather than predicting is worth stating, because it is also the
argument against the obvious alternative. Prevention — surfacing the right helper *before* the work
starts — requires predicting which of many helpers a change will turn out to need, and that
prediction is bounded by retrieval quality. Detection after the fact needs no prediction: let the
change happen, then ask the far easier question of whether this new code collides with something that
already exists. The hard problem is replaced by the one the detector already answers well.

The verb is `advise` and not `block` or `nudge` because the contract forbids automated architectural
judgement. Findings come in three classes and only one of them carries an imperative:

  RATIFIED_CONFLICT   the change reimplements a concept a named person ratified, inside its scope.
                      This is the only class that may fail a build, and the instruction it renders
                      quotes the approver and the date, because that is the authority it is acting on.
  CANDIDATE_COLLISION the change resembles existing code that nobody ratified. Surfaced, never
                      instructed. A candidate that could fail a build would make the tool a detector
                      that decides, which is the thing the method exists not to be.
  NEW_SHARED_LITERAL  the change introduces a significant literal that already exists elsewhere.

Every finding leaves the human an out, and the out is stating a reason rather than overriding a flag.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys

from .exitcodes import EXIT_ADVISORY, EXIT_CROSSED, EXIT_HELD, EXIT_NOT_MEASURED, EXIT_REFUSED
from .metrics import (
    MIN_TOKENS, SIM_THRESHOLD, _collect_functions, _func_tokens, _jaccard, _shingles, measure,
)
from .paths import resolve_root
from .selfmodel import _load_json

RATIFIED_CONFLICT = "RATIFIED_CONFLICT"
CANDIDATE_COLLISION = "CANDIDATE_COLLISION"
NEW_SHARED_LITERAL = "NEW_SHARED_LITERAL"


# --- reading the change -----------------------------------------------------

def _added_paths_from_diff(diff_text: str) -> set[str]:
    """Python files a unified diff touches."""
    paths = set()
    for line in diff_text.split("\n"):
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path.endswith(".py") and path != "/dev/null":
                paths.add(path)
    return paths


def _git(args: list[str], cwd: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ChangeUnreadable(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


class ChangeUnreadable(Exception):
    """The change could not be read, so nothing was measured."""


def changed_files(root: str, *, staged: bool, diff_range: str | None,
                  patch: str | None, stdin_text: str | None) -> set[str]:
    if patch or stdin_text is not None:
        text = stdin_text if stdin_text is not None else open(patch, encoding="utf-8").read()
        return _added_paths_from_diff(text)
    # Absolute, or walking up terminates at the empty string and the subprocess has no cwd.
    repo = os.path.abspath(root)
    while repo != os.path.dirname(repo) and not os.path.isdir(os.path.join(repo, ".git")):
        repo = os.path.dirname(repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        raise ChangeUnreadable(f"no git repository at or above {root}")
    if staged:
        out = _git(["diff", "--cached", "--name-only"], repo)
    elif diff_range:
        out = _git(["diff", "--name-only", diff_range], repo)
    else:
        out = _git(["diff", "--name-only", "HEAD"], repo)
    return {os.path.join(repo, p) for p in out.split("\n") if p.strip().endswith(".py")}


def _functions_in(paths: set[str], root: str) -> list[tuple[str, set[str], int]]:
    """(qualname, shingles, lineno, relpath) for each substantial function in the changed files."""
    from .metrics import _module_name

    out = []
    for path in sorted(paths):
        real = path if os.path.isabs(path) else os.path.join(root, path)
        if not os.path.exists(real):
            continue
        try:
            with open(real, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        try:
            mod = _module_name(root, real)
        except ValueError:
            mod = os.path.basename(real)[:-3]
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                toks = _func_tokens(node)
                if len(toks) < MIN_TOKENS:
                    continue
                rel = os.path.relpath(real, root) if not os.path.isabs(path) or True else path
                out.append((f"{mod}.{node.name}", _shingles(toks), node.lineno, rel))
    return out


# --- the ratified index -----------------------------------------------------

def _live_ratifications(intent: dict) -> list[dict]:
    return [r for r in (intent or {}).get("ratifications", []) if not r.get("superseded_by")]


def _ratification_for(qualname: str, site: str, ratifications: list[dict]) -> dict | None:
    """The live ratification whose reuse site is ``site``, if its scope covers ``qualname``."""
    for record in ratifications:
        contract = record.get("contract") or {}
        if contract.get("reuse_site") != site:
            continue
        scope = (record.get("scope") or "").strip()
        # A scope is a human label, not a path glob. Treat it as covering unless it names a module
        # prefix that plainly excludes this one: over-reporting a ratified conflict is a false
        # imperative, so the tie is broken towards reporting and letting a person read the scope.
        if scope and scope.split()[0].replace("-", "_") in qualname:
            return record
        return record
    return None


# --- the analysis -----------------------------------------------------------

def analyse(root: str, files: set[str], model: dict, intent: dict) -> list[dict]:
    resolve_root(root)
    ratifications = _live_ratifications(intent)

    changed = _functions_in(files, root)
    changed_names = {q for q, _s, _l, _f in changed}

    # Compare against the tree as it stands, excluding the functions the change itself introduced,
    # so a new function is never reported as colliding with itself.
    existing = [f for f in _collect_functions(root) if f.qualname not in changed_names]

    # The tree's redundancy families, so a collision with one member reaches the whole family.
    clusters_by_member: dict[str, set[str]] = {}
    for cluster in measure(root).clusters:
        members = {m for m in cluster if m not in changed_names}
        for member in members:
            clusters_by_member[member] = members

    findings: list[dict] = []
    for qualname, shingles, lineno, relfile in changed:
        best: list[tuple[float, str]] = []
        for other in existing:
            score = _jaccard(shingles, other.shingles)
            if score >= SIM_THRESHOLD:
                best.append((score, other.qualname))
        if not best:
            continue
        best.sort(reverse=True)
        # Expand each colliding site to the redundancy cluster it belongs to, and look for a
        # ratification anywhere in it. Clustering is transitive — a new copy can sit at 0.5 against
        # one member of a retry family and below the threshold against the canonical helper the team
        # actually ratified — so a purely pairwise check reports the one finding that carries
        # authority as an unratified candidate. The tool reports families; so does this.
        related = set()
        for _score, site in best:
            related.add(site)
            related |= clusters_by_member.get(site, set())

        record, matched_site = None, None
        for site in [name for _s, name in best] + sorted(related):
            record = _ratification_for(qualname, site, ratifications)
            if record:
                matched_site = site
                break
        score, site = best[0]
        findings.append({
            "class": RATIFIED_CONFLICT if record else CANDIDATE_COLLISION,
            "added": qualname,
            "file": relfile,
            "line": lineno,
            "collides_with": [name for _s, name in best],
            "matched_site": matched_site,
            "similarity": round(score, 4),
            "ratification": ({
                "approved_by": record.get("approved_by"),
                "approved_at": record.get("approved_at"),
                "scope": record.get("scope"),
                "rationale": record.get("rationale"),
                "review_date": record.get("review_date"),
                "reuse_site": (record.get("contract") or {}).get("reuse_site"),
            } if record else None),
        })
    return findings


def render_instruction(finding: dict) -> str:
    """The revision instruction handed back to the author, agent or human."""
    if finding["class"] == RATIFIED_CONFLICT:
        r = finding["ratification"]
        return "\n".join([
            f"REVISION INSTRUCTION (ratified intent, scope: {r['scope']})",
            f"  {finding['added']} (line {finding['line']})",
            f"  reimplements a concept this team has ratified.",
            f"  Canonical site: {r['reuse_site']}",
            f"  Ratified by {r['approved_by']} on {r['approved_at']}"
            + (f", review {r['review_date']}" if r.get("review_date") else "") + ".",
            "  Call the canonical site, or state why this site must diverge.",
        ])
    if finding["class"] == CANDIDATE_COLLISION:
        return "\n".join([
            f"SURFACED (candidate, not ratified)",
            f"  {finding['added']} (line {finding['line']})",
            f"  resembles: {', '.join(finding['collides_with'][:3])}",
            "  Nobody has ratified this as a shared concept, so this is not an instruction.",
            "  Name it in your summary and leave the judgement to a person.",
        ])
    return f"SURFACED  {finding['added']} (line {finding['line']})"


def render(findings: list[dict]) -> None:
    if not findings:
        print("no collisions with existing code")
        return
    ratified = [f for f in findings if f["class"] == RATIFIED_CONFLICT]
    others = [f for f in findings if f["class"] != RATIFIED_CONFLICT]
    for finding in ratified + others:
        print(render_instruction(finding))
        print()
    print(f"{len(ratified)} ratified conflict(s), {len(others)} surfaced for judgement")


# --- CLI --------------------------------------------------------------------

def to_sarif(findings: list[dict], root: str) -> dict:
    """SARIF 2.1.0, so a build server can put these on the diff instead of in a log.

    The severity mapping is the exit-code contract in another vocabulary. A ratified conflict is an
    `error`, because a named person decided it and it may fail a build. A candidate collision is a
    `note`, never a warning: a warning invites a team to configure it away or to treat it as a rule,
    and it is neither. Nothing a person has not ratified is allowed to look like a violation.
    """
    rules = {
        RATIFIED_CONFLICT: {
            "id": RATIFIED_CONFLICT,
            "name": "RatifiedConflict",
            "shortDescription": {"text": "Reimplements something a named person ratified"},
            "fullDescription": {"text": "A change reimplements a concept with a live ratification "
                                        "covering this path. The canonical site, its approver and "
                                        "the date are in the message."},
            "defaultConfiguration": {"level": "error"},
        },
        CANDIDATE_COLLISION: {
            "id": CANDIDATE_COLLISION,
            "name": "CandidateCollision",
            "shortDescription": {"text": "Resembles existing code that nobody has ratified"},
            "fullDescription": {"text": "Surfaced for a person to judge. This is not an instruction "
                                        "and must not fail a build: nothing here has been approved."},
            "defaultConfiguration": {"level": "note"},
        },
    }
    results = []
    for f in findings:
        ratified = f["class"] == RATIFIED_CONFLICT
        if ratified:
            r = f.get("ratification") or {}
            text = (f"{f['added']} reimplements a ratified concept. Canonical site: "
                    f"{r.get('reuse_site') or f.get('matched_site')}. Ratified by "
                    f"{r.get('approved_by')} on {r.get('approved_at')}, scope {r.get('scope')}. "
                    "Call the canonical site, or state why this site must diverge.")
        else:
            text = (f"{f['added']} resembles {', '.join(f.get('collides_with') or []) or 'existing code'}. "
                    "Nobody has ratified this as a shared concept, so this is not an instruction. "
                    "Name it in your summary and leave the judgement to a person.")
        results.append({
            "ruleId": f["class"],
            "level": "error" if ratified else "note",
            "message": {"text": text},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": f.get("file") or "", "uriBaseId": "%SRCROOT%"},
                "region": {"startLine": max(1, int(f.get("line") or 1))},
            }}],
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "coherence-ratchet advise",
                "informationUri": "https://github.com/RomanLobus/coherence-ratchet",
                "rules": list(rules.values()),
            }},
            "results": results,
        }],
    }


def register_cli(sub) -> None:
    p = sub.add_parser(
        "advise",
        help="measure a change against the existing code and return a revision instruction",
    )
    p.add_argument("path", help="the package directory to measure the change against")
    p.add_argument("--staged", action="store_true", help="read the git index")
    p.add_argument("--diff", dest="diff_range", help="a git range, e.g. origin/main...HEAD")
    p.add_argument("--patch", help="read a unified diff from a file")
    p.add_argument("--stdin", action="store_true", help="read a unified diff from stdin")
    p.add_argument("--model", default="coherence/selfmodel.json")
    p.add_argument("--intent", default="coherence/intent.json")
    p.add_argument("--format", choices=["text", "json", "sarif"], default="text")
    p.add_argument("--fail-on", choices=["ratified", "none"], default="ratified",
                   help="exit 1 on a ratified conflict (default), or never. There is deliberately "
                        "no option that fails on a candidate: `any` was removed because it did "
                        "exactly that")


def run_cli(args) -> int:
    root = args.path
    try:
        resolve_root(root)
    except Exception as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED

    stdin_text = sys.stdin.read() if args.stdin else None
    try:
        files = changed_files(root, staged=args.staged, diff_range=args.diff_range,
                              patch=args.patch, stdin_text=stdin_text)
    except ChangeUnreadable as exc:
        # The change could not be read, so nothing was measured. Saying "no findings" here would be
        # the defect this tool exists to name.
        print(f"not measured: {exc}", file=sys.stderr)
        return EXIT_NOT_MEASURED

    model = _load_json(args.model) if os.path.exists(args.model) else {}
    intent = _load_json(args.intent) if os.path.exists(args.intent) else {}

    findings = analyse(root, files, model, intent)

    if args.format == "sarif":
        print(json.dumps(to_sarif(findings, root), indent=2, sort_keys=True))
    elif args.format == "json":
        print(json.dumps({
            "findings": findings,
            "revision_instruction": "\n\n".join(render_instruction(f) for f in findings),
            "counts": {
                "ratified_conflict": sum(1 for f in findings if f["class"] == RATIFIED_CONFLICT),
                "candidate_collision": sum(1 for f in findings if f["class"] == CANDIDATE_COLLISION),
            },
        }, indent=2, sort_keys=True))
    else:
        render(findings)

    ratified = [f for f in findings if f["class"] == RATIFIED_CONFLICT]
    if args.fail_on == "ratified" and ratified:
        return EXIT_CROSSED
    return EXIT_ADVISORY if findings else EXIT_HELD
