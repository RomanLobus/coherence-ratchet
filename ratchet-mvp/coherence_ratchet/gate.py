"""The optional second layer of the gate: the LLM semantic matcher.

The deterministic ratchet (the floor) is necessary but not sufficient: it flags structural duplicate
clusters but cannot interpret their intent, and it cannot see semantic layering violations. This module adds the
layer the experiments validated (`semantic-detector.md`, `architecture-gate.md`,
`gate-generalisation.md`), under the discipline those experiments proved necessary:

  - **objective matching against explicit supplied evidence, never open judgement of intent** (the
    subjective framings produced dangerous false-clears);
  - **multi-trial with a conservative quorum** — disagreement surfaces;
  - **surfaces to a steward, never ratifies or auto-acts**.

It is OPTIONAL and env-gated on ANTHROPIC_API_KEY, exactly like the self-model's `--llm` matcher. With
no key (and no injected judge) it degrades to a clean "skipped" report; the deterministic `check`
command is untouched. Compatibility checks, bounded comparison, and review are deliberately out of scope:
this module stops at surfacing to the steward, where the evidence says the human takes over.
"""
from __future__ import annotations

import ast
import json
import os
import re
from collections import Counter

from . import metrics as fm
from . import selfmodel as sm
from .exitcodes import EXIT_ADVISORY, EXIT_CROSSED, EXIT_HELD, EXIT_NOT_MEASURED

DEFAULT_JUDGE_MODEL = "claude-haiku-4-5-20251001"
# The multi-trial quorum is the gate's stated safety mechanism, and it only means anything if the
# trials can differ. That makes sampling a precondition of the design, not an API default to inherit,
# so the temperature is pinned here and reported with every run.
DEFAULT_JUDGE_TEMPERATURE = 1.0


# --- the judge (pluggable so the orchestration is testable offline) ---------

def judge_model() -> str:
    return os.environ.get("COHERENCE_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)


def judge_temperature() -> float:
    raw = os.environ.get("COHERENCE_JUDGE_TEMPERATURE")
    if raw is None:
        return DEFAULT_JUDGE_TEMPERATURE
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_JUDGE_TEMPERATURE


def _anthropic_judge(prompt: str, max_tokens: int = 600) -> str:
    """One call to the messages API. Raises if no key — callers handle the skip."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    import urllib.request

    body = json.dumps({
        "model": judge_model(),
        "max_tokens": max_tokens,
        "temperature": judge_temperature(),
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.load(resp)
    return "".join(b.get("text", "") for b in payload.get("content", []))


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# --- source index (so the matcher sees code, not just names) ----------------

def _source_index(root: str) -> dict:
    """map 'module.func' -> source text, for every function under root."""
    out = {}
    for path in fm._iter_py_files(root):
        try:
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        mod = fm._module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                seg = ast.get_source_segment(src, node)
                if seg:
                    out[f"{mod}.{node.name}"] = seg
    return out


# --- catalogue matching over duplicate clusters -----------------------------

_MATCH_PROMPT = """You are matching a cluster of near-duplicate functions against an explicit \
catalogue of SANCTIONED patterns (intentional, blessed duplication). Judge ONLY by the catalogue. \
Do NOT use outside knowledge of any library. If the cluster matches a specific catalogued pattern, \
return that pattern's exact name; otherwise return "NONE".

Catalogue of sanctioned patterns:
{catalogue}

The cluster (concept: {concept}):
{members}

Return strict JSON only: {{"match": "<pattern name or NONE>", "why": "<one sentence>"}}"""


def _match_cluster(cluster, concept, catalogue, sources, judge, trials, quorum):
    members = "\n\n".join(
        f"# {q}\n{sources.get(q, '(source unavailable)')}" for q in cluster
    )
    cat_text = "\n".join(_catalogue_line(p) for p in catalogue) or "(empty)"
    prompt = _MATCH_PROMPT.format(catalogue=cat_text, concept=concept, members=members)
    votes = []
    errors = []
    for _ in range(trials):
        try:
            r = _extract_json(judge(prompt))
        except Exception as exc:  # a failed trial counts as NONE (conservative: surfaces)
            errors.append(str(exc))
            r = {"match": "NONE", "why": f"trial error: {exc}"}
        votes.append((str(r.get("match", "NONE")).strip(), r.get("why", "")))
    named = Counter(m for m, _ in votes if m and m.upper() != "NONE")
    verdict = {"cluster": cluster, "concept": concept, "trials": trials,
               "votes": [m for m, _ in votes], "errors": len(errors)}
    if errors:
        # An unreachable or retired judge must not read as an uncatalogued divergence: the tool
        # would be asserting a finding it never made. The disposition stays conservative (SURFACE),
        # but the reason names the failure so a steward can tell the two apart.
        verdict["error"] = errors[0]
    if named:
        pattern, count = named.most_common(1)[0]
        if count >= quorum:
            why = next((w for m, w in votes if m == pattern), "")
            verdict.update({"disposition": "CLEARED", "matched": pattern,
                            "quorum": f"{count}/{trials}", "why": why})
            return verdict
    # short of quorum on any single pattern -> surface to steward
    if errors and len(errors) == trials:
        why = f"judge unavailable, {len(errors)}/{trials} trials failed: {errors[0]}"
    elif errors:
        why = (f"no sanctioned pattern reached quorum, with {len(errors)}/{trials} trials failed "
               f"({errors[0]})")
    else:
        why = "no sanctioned pattern reached quorum — uncatalogued divergence"
    verdict.update({"disposition": "SURFACE", "matched": None,
                    "quorum": f"{named.most_common(1)[0][1] if named else 0}/{trials}",
                    "why": why})
    return verdict


def _catalogue_line(pattern: dict) -> str:
    """Render one catalogue pattern for the judge, with its authorisation when it carries one.

    The catalogue is what authorises the gate to clear code, so a pattern that names its approver,
    date, and scope is a different thing from an anonymous line somebody typed. The judge sees the
    provenance because a pattern without it should read as weaker evidence, not as equal.
    """
    line = f"- {pattern['name']}: {pattern.get('description', '')}"
    bits = []
    for key, label in (("approved_by", "approved by"), ("approved_at", "on"), ("scope", "scope")):
        value = pattern.get(key)
        if value:
            bits.append(f"{label} {value}")
    if pattern.get("ratified_id"):
        bits.append(f"ratification {pattern['ratified_id']}")
    if bits:
        line += f" [{'; '.join(bits)}]"
    return line


# --- layering check over the module graph -----------------------------------

def _deterministic_layer_violations(modules, layer_of, order):
    """Cheap check when layers are declared: a module must not depend on a higher layer."""
    rank = {name: i for i, name in enumerate(order)}
    out = []
    for m in modules:
        src_layer = layer_of.get(m["module"])
        if src_layer not in rank:
            continue
        for dep in m["depends_on"]:
            dl = layer_of.get(dep)
            if dl in rank and rank[dl] < rank[src_layer]:
                out.append({"module": m["module"], "depends_on": dep,
                            "rule": "layer-order", "kind": "up-dependency",
                            "why": f"{src_layer} module depends up on {dl} module"})
    return out


_LAYERING_PROMPT = """You are checking a layered architecture against DECLARED rules only. Flag ONLY \
violations of these rules; do not editorialise or suggest improvements.

Declared layer order (high to low): {order}
Declared rules:
{rules}

Modules (name | layer | responsibility | depends on):
{manifest}

Return strict JSON only: {{"violations": [{{"module": "<name>", "rule": "<rule id>", "why": "<one sentence>"}}]}}"""


def _llm_layer_violations(modules, layering, judge, trials, quorum):
    order = layering.get("order", [])
    rules = layering.get("rules", [])
    layer_of = layering.get("layer_of", {})
    resp = layering.get("responsibilities", {})
    manifest = "\n".join(
        f"- {m['module']} | {layer_of.get(m['module'], '?')} | {resp.get(m['module'], '')} | "
        f"{', '.join(m['depends_on']) or '(none)'}"
        for m in modules
    )
    prompt = _LAYERING_PROMPT.format(
        order=" > ".join(order),
        rules="\n".join(f"- {r}" for r in rules) or "(none)",
        manifest=manifest,
    )
    tally = Counter()
    detail = {}
    errors = []
    for _ in range(trials):
        try:
            r = _extract_json(judge(prompt))
        except Exception as exc:
            # An empty violation list from a dead judge is indistinguishable from a clean
            # architecture, which is the dangerous direction: the tool would report a finding it
            # never made. The cluster path records its failures for exactly this reason; this one
            # swallowed them, so an unreachable judge read as "no layering violations".
            errors.append(str(exc))
            r = {}
        for v in r.get("violations", []) or []:
            key = (v.get("module"), v.get("rule"))
            if key[0]:
                tally[key] += 1
                detail[key] = v.get("why", "")
    # surface a violation flagged in >= quorum trials (majority discipline)
    found = [{"module": mod, "rule": rule, "why": detail[(mod, rule)], "quorum": f"{n}/{trials}"}
             for (mod, rule), n in tally.items() if n >= quorum]
    return found, errors


# --- top level --------------------------------------------------------------

def run(root, *, model_path=None, catalogue_path=None, layering_path=None,
        trials=5, quorum=4, judge=None):
    """Run the semantic layer over the deterministic residue. Returns a steward-triage report.
    `judge` is injectable for tests; default uses the Anthropic API (env-gated)."""
    needs_llm_key = judge is None and not os.environ.get("ANTHROPIC_API_KEY")

    model = None
    if model_path and os.path.exists(model_path):
        model = json.load(open(model_path, encoding="utf-8"))
    else:
        model = sm.derive(root)

    # The same courtesy the layering spec below gets, and for the same reason. A catalogue path that
    # does not exist fell through to "no catalogue provided — all duplication surfaced", which is
    # the report a reader gets for supplying no catalogue at all: a typo read as a deliberate
    # choice. A malformed catalogue was worse, dying on an unguarded json.load before the API-key
    # check, so it crashed even on an offline run.
    catalogue = []
    layering_warnings = []
    if catalogue_path:
        if not os.path.exists(catalogue_path):
            layering_warnings.append(
                f"catalogue not found at {catalogue_path}; every duplicate cluster was surfaced, "
                "which is also what an intentionally absent catalogue produces")
        else:
            try:
                catalogue = json.load(
                    open(catalogue_path, encoding="utf-8")).get("patterns", [])
            except (json.JSONDecodeError, OSError) as exc:
                layering_warnings.append(
                    f"catalogue at {catalogue_path} could not be read ({exc}); every duplicate "
                    "cluster was surfaced")
    # A layering spec that cannot be found or cannot be read used to skip both layering checks in
    # silence, so a reader exercised half the mechanism and could not tell. Say so instead.
    layering = {}
    if layering_path:
        if not os.path.exists(layering_path):
            layering_warnings.append(f"layering spec not found at {layering_path}; both layering "
                                     "checks were skipped")
        else:
            try:
                layering = json.load(open(layering_path, encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                layering_warnings.append(f"layering spec at {layering_path} could not be read "
                                         f"({exc}); both layering checks were skipped")
            else:
                if not (layering.get("order") and layering.get("layer_of")):
                    layering_warnings.append(
                        f"layering spec at {layering_path} declares no 'order' and 'layer_of', so "
                        "the deterministic layering check was skipped")

    clusters = []
    for candidate in model.get("candidates", []):
        if candidate.get("kind") != "reuse_helper":
            continue
        evidence = candidate.get("evidence", {})
        clusters.append((evidence.get("sites", []), evidence.get("concept", "")))
    observed = model.get("observed", model)
    modules = observed.get("modules", [])

    # Layering: deterministic order check is free and always runs when layers are declared.
    layer_violations = []
    if layering.get("order") and layering.get("layer_of"):
        layer_violations = _deterministic_layer_violations(modules, layering["layer_of"], layering["order"])

    # Everything below needs the judge.
    if needs_llm_key:
        return {"skipped": True,
                "reason": "semantic gate skipped — set ANTHROPIC_API_KEY (deterministic layering ran)",
                "clusters": [], "layer_violations": layer_violations,
                "surfaced": len(clusters), "cleared": 0,
                "layering_warnings": layering_warnings}

    judge = judge or _anthropic_judge
    sources = _source_index(root)

    cluster_verdicts = []
    if clusters:
        # With no catalogue, matching is a no-op that surfaces everything (never clears) — the
        # zero-false-clear default. Only spend LLM calls when there is a catalogue to clear against.
        if catalogue:
            for members, concept in clusters:
                cluster_verdicts.append(
                    _match_cluster(members, concept, catalogue, sources, judge, trials, quorum))
        else:
            cluster_verdicts = [
                {"cluster": members, "concept": concept, "disposition": "SURFACE",
                 "matched": None, "why": "no catalogue provided — all duplication surfaced"}
                for members, concept in clusters
            ]

    # LLM layering check only when responsibilities are declared (matches the experiment's manifest).
    layering_judge_errors = []
    if layering.get("responsibilities"):
        found, layering_judge_errors = _llm_layer_violations(
            modules, layering, judge, trials, quorum)
        layer_violations += found
        if layering_judge_errors:
            layering_warnings.append(
                f"semantic layering check: {len(layering_judge_errors)}/{trials} judge trials "
                f"failed ({layering_judge_errors[0]}); a clean layering result cannot be "
                "distinguished from an unreachable judge on this run")

    cleared = sum(1 for v in cluster_verdicts if v["disposition"] == "CLEARED")
    surfaced = sum(1 for v in cluster_verdicts if v["disposition"] == "SURFACE")
    judge_errors = (sum(v.get("errors", 0) for v in cluster_verdicts)
                    + len(layering_judge_errors))
    return {"skipped": False, "clusters": cluster_verdicts, "layer_violations": layer_violations,
            "cleared": cleared, "surfaced": surfaced, "judge_errors": judge_errors,
            "layering_warnings": layering_warnings,
            # A run is only interpretable next to the judge that produced it. Recorded on every
            # report so a printed capture carries its own provenance.
            "judge": {"model": judge_model(), "temperature": judge_temperature(),
                      "trials": trials, "quorum": quorum, "sampled": True}}


def render(report: dict) -> None:
    for warning in report.get("layering_warnings", []):
        print(f"  ⚠ {warning}")
    if report.get("skipped"):
        print(f"  {report['reason']}")
        if report["layer_violations"]:
            print(f"  deterministic layering violations: {len(report['layer_violations'])}")
            for v in report["layer_violations"]:
                print(f"    ✗ {v['module']} → {v.get('depends_on', v.get('rule'))}: {v['why']}")
        print(f"  (deterministic floor already flagged {report['surfaced']} duplicate clusters)")
        return
    print(f"  semantic gate: {report['cleared']} cleared, {report['surfaced']} surfaced to steward")
    if report.get("judge_errors"):
        print(f"  ⚠ {report['judge_errors']} judge trial(s) failed — surfacings below may be "
              "unavailability, not divergence")
    for v in report["clusters"]:
        if v["disposition"] == "CLEARED":
            print(f"  ✓ CLEARED [{v['concept']}] matches '{v['matched']}' ({v.get('quorum','')}): {v['why']}")
        else:
            print(f"  ⚠ SURFACE [{v['concept']}] {', '.join(n.split('.')[-1] for n in v['cluster'])}: {v['why']}")
    if report["layer_violations"]:
        print("  layering violations:")
        for v in report["layer_violations"]:
            tgt = v.get("depends_on", "")
            print(f"    ✗ {v['module']}{' → ' + tgt if tgt else ''} [{v['rule']}]: {v['why']}")


# --- CLI wiring (called from cli.py) ----------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser("gate", help="run the optional LLM semantic layer over the deterministic residue")
    p.add_argument("path")
    p.add_argument("--model", help="path to selfmodel.json (else derived on the fly)")
    p.add_argument("--catalogue", help="ratified sanctioned-pattern catalogue (JSON); without it, all duplication is surfaced")
    p.add_argument("--layering", help="declared layering spec (JSON: order, layer_of, rules, responsibilities)")
    p.add_argument("--trials", type=int, default=5)
    p.add_argument("--quorum", type=int, default=4, help="trials that must agree to CLEAR (conservative)")
    p.add_argument("--fail-on", choices=["none", "violation"], default="none",
                   help="exit 1 on a declared-layering violation, measured against an order a "
                        "person declared. Default advises (exit 3) and fails nothing. There is no "
                        "option that fails on a surfaced cluster: `surface` was removed because a "
                        "surfaced cluster is a candidate nobody ratified")
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    report = run(args.path, model_path=args.model, catalogue_path=args.catalogue,
                 layering_path=args.layering, trials=args.trials, quorum=args.quorum)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        render(report)

    # This returned 0 unconditionally, so a run that surfaced uncatalogued divergence, and a run in
    # which the judge was unreachable on every trial, both reported success. A gate that cannot fail
    # is not a gate, and an unreachable judge reading as a clean architecture is the exact defect
    # this tool exists to name.
    violations = len(report.get("layer_violations") or [])
    surfaced = report.get("surfaced") or 0
    cleared = report.get("cleared") or 0

    # The judge was asked and never answered. Nothing semantic was measured, so say so rather than
    # reporting the deterministic half as if it were the whole reading. Running deliberately without
    # a key is a choice, not a failure, and is not this branch.
    if report.get("judge_errors") and not cleared and not surfaced and not report.get("skipped"):
        return EXIT_NOT_MEASURED

    # A surfaced cluster is advisory: nobody ratified it, so it may not fail a build under any flag.
    # Not "by default" -- that hedge is how `--fail-on surface` came to exist and contradict the
    # invariant. A layering violation is measured against an order a person declared, so it alone is
    # available as a failure.
    fail_on = getattr(args, "fail_on", "none")
    if fail_on == "violation" and violations:
        return EXIT_CROSSED

    return EXIT_ADVISORY if (violations or surfaced) else EXIT_HELD
