"""The optional second layer of the gate: the LLM semantic matcher.

The deterministic ratchet (the floor) is necessary but not sufficient — it flags structural duplicate
clusters but cannot tell a *sanctioned* pattern (intentional symmetry the team blesses) from
*uncatalogued* fragmentation, and it cannot see semantic layering violations. This module adds the
layer the experiments validated (`semantic-detector.md`, `architecture-gate.md`,
`gate-generalisation.md`), under the discipline those experiments proved necessary:

  - **objective matching against an explicit catalogue, never open judgement of intent** (the
    subjective framings produced dangerous false-clears);
  - **multi-trial with a conservative quorum to CLEAR** — anything short of quorum surfaces;
  - **surfaces to a steward, never auto-acts** — it can clear only what matches a ratified pattern.

It is OPTIONAL and env-gated on ANTHROPIC_API_KEY, exactly like the self-model's `--llm` matcher. With
no key (and no injected judge) it degrades to a clean "skipped" report; the deterministic `check`
command is untouched. The behaviour-complete proof — the *third* layer — is deliberately out of scope:
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

DEFAULT_JUDGE_MODEL = "claude-haiku-4-5-20251001"


# --- the judge (pluggable so the orchestration is testable offline) ---------

def _anthropic_judge(prompt: str, max_tokens: int = 600) -> str:
    """One call to the messages API. Raises if no key — callers handle the skip."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    import urllib.request

    body = json.dumps({
        "model": os.environ.get("COHERENCE_JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
        "max_tokens": max_tokens,
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
    cat_text = "\n".join(f"- {p['name']}: {p.get('description', '')}" for p in catalogue) or "(empty)"
    prompt = _MATCH_PROMPT.format(catalogue=cat_text, concept=concept, members=members)
    votes = []
    for _ in range(trials):
        try:
            r = _extract_json(judge(prompt))
        except Exception as exc:  # a failed trial counts as NONE (conservative: surfaces)
            r = {"match": "NONE", "why": f"trial error: {exc}"}
        votes.append((str(r.get("match", "NONE")).strip(), r.get("why", "")))
    named = Counter(m for m, _ in votes if m and m.upper() != "NONE")
    verdict = {"cluster": cluster, "concept": concept, "trials": trials,
               "votes": [m for m, _ in votes]}
    if named:
        pattern, count = named.most_common(1)[0]
        if count >= quorum:
            why = next((w for m, w in votes if m == pattern), "")
            verdict.update({"disposition": "CLEARED", "matched": pattern,
                            "quorum": f"{count}/{trials}", "why": why})
            return verdict
    # short of quorum on any single pattern -> surface to steward
    verdict.update({"disposition": "SURFACE", "matched": None,
                    "quorum": f"{named.most_common(1)[0][1] if named else 0}/{trials}",
                    "why": "no sanctioned pattern reached quorum — uncatalogued divergence"})
    return verdict


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
    for _ in range(trials):
        try:
            r = _extract_json(judge(prompt))
        except Exception:
            r = {}
        for v in r.get("violations", []) or []:
            key = (v.get("module"), v.get("rule"))
            if key[0]:
                tally[key] += 1
                detail[key] = v.get("why", "")
    # surface a violation flagged in >= quorum trials (majority discipline)
    return [{"module": mod, "rule": rule, "why": detail[(mod, rule)], "quorum": f"{n}/{trials}"}
            for (mod, rule), n in tally.items() if n >= quorum]


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

    catalogue = []
    if catalogue_path and os.path.exists(catalogue_path):
        catalogue = json.load(open(catalogue_path, encoding="utf-8")).get("patterns", [])
    layering = {}
    if layering_path and os.path.exists(layering_path):
        layering = json.load(open(layering_path, encoding="utf-8"))

    clusters = [([h["canonical"]] + h["duplicates"], h["concept"]) for h in model.get("helpers", [])]
    modules = model.get("modules", [])

    # Layering: deterministic order check is free and always runs when layers are declared.
    layer_violations = []
    if layering.get("order") and layering.get("layer_of"):
        layer_violations = _deterministic_layer_violations(modules, layering["layer_of"], layering["order"])

    # Everything below needs the judge.
    if needs_llm_key:
        return {"skipped": True,
                "reason": "semantic gate skipped — set ANTHROPIC_API_KEY (deterministic layering ran)",
                "clusters": [], "layer_violations": layer_violations,
                "surfaced": len(clusters), "cleared": 0}

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
    if layering.get("responsibilities"):
        layer_violations += _llm_layer_violations(modules, layering, judge, trials, quorum)

    cleared = sum(1 for v in cluster_verdicts if v["disposition"] == "CLEARED")
    surfaced = sum(1 for v in cluster_verdicts if v["disposition"] == "SURFACE")
    return {"skipped": False, "clusters": cluster_verdicts, "layer_violations": layer_violations,
            "cleared": cleared, "surfaced": surfaced}


def render(report: dict) -> None:
    if report.get("skipped"):
        print(f"  {report['reason']}")
        if report["layer_violations"]:
            print(f"  deterministic layering violations: {len(report['layer_violations'])}")
            for v in report["layer_violations"]:
                print(f"    ✗ {v['module']} → {v.get('depends_on', v.get('rule'))}: {v['why']}")
        print(f"  (deterministic floor already flagged {report['surfaced']} duplicate clusters)")
        return
    print(f"  semantic gate: {report['cleared']} cleared, {report['surfaced']} surfaced to steward")
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
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    report = run(args.path, model_path=args.model, catalogue_path=args.catalogue,
                 layering_path=args.layering, trials=args.trials, quorum=args.quorum)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        render(report)
    return 0
