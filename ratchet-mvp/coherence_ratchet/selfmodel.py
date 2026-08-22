"""Derive observed code structure and evidence-backed ratification candidates.

Schema v2 separates facts read from code, heuristic candidates inferred from those facts, and the
human-owned intent stored in a separate file. A frequent literal, shared key, or plausible helper is
never architecture policy merely because the extractor found it.
"""
from __future__ import annotations

import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

from . import archmetrics as am
from . import metrics as fm
from .paths import resolve_root
from .signals import connascence_of_meaning

SELFMODEL_VERSION = 2
EXTRACTOR_VERSION = "0.2.0"
INTENT_VERSION = 1
DEFAULT_MODEL = "coherence/selfmodel.json"
DEFAULT_INTENT = "coherence/intent.json"
_RULESET = "python-ast:v2:modules-functions-entities-literals-near-duplicate-candidates"


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _tree_hash(root: str) -> str:
    digest = hashlib.sha256()
    for path in fm._iter_py_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        try:
            with open(path, "rb") as stream:
                digest.update(stream.read())
        except OSError:
            continue
        digest.update(b"\0")
    return digest.hexdigest()


def _revision(root: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", os.path.abspath(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def model_hash(model: dict) -> str:
    """Stable identity for the evidence content, excluding paths and generation time."""
    payload = {
        "schema_version": model.get("schema_version"),
        "source_tree_hash": model.get("source", {}).get("tree_hash"),
        "extractor": model.get("extractor"),
        "observed": model.get("observed", {}),
        "candidates": model.get("candidates", []),
    }
    return _sha(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))


def _candidate_id(kind: str, evidence: dict) -> str:
    material = json.dumps({"kind": kind, "evidence": evidence}, sort_keys=True, separators=(",", ":"))
    return f"{kind}:{_sha(material)[:16]}"


def _name_tokens(name: str) -> list[str]:
    """Split an identifier into lowercase concept tokens (snake_case and camelCase)."""
    parts = re.split(r"[_\W]+", name)
    out = []
    for p in parts:
        out.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", p) or [p])
    return [t.lower() for t in out if t]


def _docline(node: ast.AST) -> str:
    doc = ast.get_docstring(node)
    return doc.strip().splitlines()[0] if doc else ""


def _call_names(node: ast.AST) -> list[str]:
    calls = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                calls.append(f.id)
            elif isinstance(f, ast.Attribute):
                calls.append(f.attr)
    return calls


# --- modules ----------------------------------------------------------------

def _module_structure(root: str) -> list[dict]:
    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    depends = {m: sorted(am._edges_for(p, m, pkg, internal) - {m}) for m, p in mods.items()}
    fan_in = {m: 0 for m in mods}
    for m, deps in depends.items():
        for t in deps:
            fan_in[t] = fan_in.get(t, 0) + 1

    # am names modules with the package prefix (billing.money) for import resolution; the function
    # and entity indexes use bare names relative to root (money). Strip the prefix so cross-references
    # between the module graph and the function/helper indexes line up.
    def bare(name: str) -> str:
        return name[len(pkg) + 1:] if name.startswith(pkg + ".") else name

    out = []
    for m in sorted(mods):
        fo, fi = len(depends[m]), fan_in.get(m, 0)
        if fo == 0 and fi > 0:
            role = "foundation"       # depended upon, depends on nothing internal
        elif fi == 0 and fo > 0:
            role = "entry"            # depends on others, nobody depends on it
        elif fi == 0 and fo == 0:
            role = "isolated"
        else:
            role = "intermediate"
        out.append({"module": bare(m), "depends_on": [bare(d) for d in depends[m]],
                    "fan_in": fi, "fan_out": fo, "role": role})
    return out


# --- functions --------------------------------------------------------------

def _functions(root: str) -> list[dict]:
    out = []
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                out.append({
                    "qualname": f"{mod}.{node.name}",
                    "module": mod,
                    "name": node.name,
                    "args": [a.arg for a in node.args.args if a.arg not in ("self", "cls")],
                    "calls": sorted(set(_call_names(node))),
                    "doc": _docline(node),
                    "tokens": sorted(set(_name_tokens(node.name))),
                })
    out.sort(key=lambda f: f["qualname"])
    return out


# --- observed entities -------------------------------------------------------

_STRUCTURAL_BASES = {"TypedDict", "NamedTuple"}


def _explicit_entities(root: str) -> list[dict]:
    out = []
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            is_dc = any(am._attr_name(d).split(".")[-1] == "dataclass" for d in node.decorator_list)
            base_names = {am._attr_name(b).split(".")[-1] for b in node.bases}
            kind = None
            if is_dc:
                kind = "dataclass"
            elif base_names & _STRUCTURAL_BASES:
                kind = (base_names & _STRUCTURAL_BASES).pop()
            if not kind:
                continue
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
                elif isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name):
                            fields.append(t.id)
            out.append({"name": node.name, "kind": kind, "module": mod, "fields": sorted(set(fields))})
    return out


def _dict_shapes(root: str) -> list[dict]:
    """Observed string-key access grouped by variable name and module."""
    per_name_keys: dict = defaultdict(lambda: defaultdict(Counter))  # base -> module -> Counter(keys)
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for n in ast.walk(tree):
            if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                    and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)):
                per_name_keys[n.value.id][mod][n.slice.value] += 1
    out = []
    for base, by_mod in per_name_keys.items():
        keyfreq: Counter = Counter()
        sites = sorted(by_mod)
        for mod, keys in by_mod.items():
            for k in keys:
                keyfreq[k] += 1
        # Only interesting when the same shape appears in >=2 sites or has >=2 keys.
        if len(sites) < 2 and sum(keyfreq.values()) < 2:
            continue
        out.append({
            "name": base,
            "kind": "dict-shape",
            "sites": sites,
            "key_frequency": dict(keyfreq),
            "per_site_keys": {m: sorted(k) for m, k in by_mod.items()},
        })
    out.sort(key=lambda e: (-len(e["sites"]), e["name"]))
    return out


# --- heuristic helper evidence ----------------------------------------------

def _helpers(root: str) -> list[dict]:
    snap = fm.measure(root)
    out = []
    for cluster in snap.clusters:
        # concept = the name token shared by the most members
        tokens = Counter()
        for q in cluster:
            for t in _name_tokens(q.rsplit(".", 1)[-1]):
                tokens[t] += 1
        concept = tokens.most_common(1)[0][0] if tokens else ""

        # Rank a suggested site for human review. The ranking is evidence, never ratified intent.
        def rank(q):
            mod, _, fn = q.rpartition(".")
            fn_tokens = _name_tokens(fn)
            score = 0
            if fn == concept:
                score += 4
            if mod.split(".")[-1] == concept:
                score += 3
            if fn_tokens == [concept]:
                score += 2
            return (-score, len(fn_tokens), q)

        ordered = sorted(cluster, key=rank)
        suggested = ordered[0]
        out.append({
            "concept": concept,
            "suggested_site": suggested,
            "other_sites": [q for q in cluster if q != suggested],
            "ranking_basis": "concept-name and generic-name heuristic",
        })
    return out


# --- top level --------------------------------------------------------------

def derive(root: str) -> dict:
    resolve_root(root)
    _conc_count, conc_rows = connascence_of_meaning(root)
    root = os.path.abspath(os.path.normpath(root))
    modules = _module_structure(root)
    functions = _functions(root)
    entities = _explicit_entities(root) + _dict_shapes(root)
    conventions = [{"value": r["value"], "modules": r["modules"]} for r in conc_rows]
    helper_evidence = _helpers(root)

    candidates = []
    for helper in helper_evidence:
        evidence = {
            "concept": helper["concept"],
            "sites": [helper["suggested_site"], *helper["other_sites"]],
            "ranking_basis": helper["ranking_basis"],
        }
        candidates.append({
            "id": _candidate_id("reuse_helper", evidence),
            "kind": "reuse_helper",
            "confidence": "medium",
            "suggestion": {
                "concept": helper["concept"],
                "reuse_site": helper["suggested_site"],
            },
            "evidence": evidence,
        })
    for entity in entities:
        if entity.get("kind") == "dict-shape":
            site_count = len(entity["sites"])
            common = sorted(k for k, count in entity["key_frequency"].items() if count == site_count)
            evidence = {
                "name": entity["name"],
                "sites": entity["sites"],
                "per_site_keys": entity["per_site_keys"],
                "keys_observed_at_every_site": common,
            }
            candidates.append({
                "id": _candidate_id("entity_shape", evidence),
                "kind": "entity_shape",
                "confidence": "low" if not common else "medium",
                "suggestion": {"name": entity["name"], "fields": common},
                "evidence": evidence,
            })
    for convention in conventions:
        evidence = {"value": convention["value"], "modules": convention["modules"]}
        candidates.append({
            "id": _candidate_id("shared_value", evidence),
            "kind": "shared_value",
            "confidence": "low",
            "suggestion": {"value": convention["value"]},
            "evidence": evidence,
        })

    model = {
        "schema_version": SELFMODEL_VERSION,
        "source": {
            "root": root,
            "revision": _revision(root),
            "tree_hash": _tree_hash(root),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        "extractor": {
            "tool": "coherence-ratchet",
            "version": EXTRACTOR_VERSION,
            "ruleset_hash": _sha(_RULESET),
        },
        "observed": {
            "modules": modules,
            "functions": functions,
            "entities": entities,
            "conventions": conventions,
        },
        "candidates": sorted(candidates, key=lambda item: item["id"]),
    }
    model["model_hash"] = model_hash(model)
    return model


def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def empty_intent(model: dict) -> dict:
    return {
        "schema_version": INTENT_VERSION,
        "source_model_hash": model_hash(model),
        "ratifications": [],
    }


def _contract_for(candidate: dict) -> dict:
    suggestion = candidate.get("suggestion", {})
    if candidate["kind"] == "reuse_helper":
        return {"concept": suggestion.get("concept"), "reuse_site": suggestion.get("reuse_site")}
    if candidate["kind"] == "entity_shape":
        return {"entity": suggestion.get("name"), "fields": suggestion.get("fields", [])}
    if candidate["kind"] == "shared_value":
        return {"shared_value": suggestion.get("value")}
    return dict(suggestion)


DEFAULT_POLICY = "ratification-policy.json"


class RatificationRefused(Exception):
    """A configured policy did not admit this ratifier."""


def policy_path_for(intent_path: str) -> str:
    """The policy file lives beside the intent file it governs."""
    return os.path.join(os.path.dirname(intent_path) or ".", DEFAULT_POLICY)


def check_ratification_policy(path: str, *, approved_by: str, root: str = ".") -> dict | None:
    """Enforce a team's ratification policy, if it has written one down.

    The book's claim about ratification is a claim about authority, and for most of this tool's life
    the CLI could not support it: `--by` is a string, a string looks the same whoever types it, and an
    agent with shell access can pass one. That limit is now stated plainly in the book rather than
    papered over, and this function is the part a team can do something about.

    **Absent by default, and silent when absent.** No policy file means no check and no output, so
    every printed block in the manuscript and every existing workflow behaves exactly as before. A
    team that needs the human-only property mechanically writes the file and gets it enforced.

    Two controls, either or both:

        {"approvers": ["ada@example.com", "grace@example.com"],
         "require_signed_commit": true}

    `approvers` is an allowlist checked against `--by`, and is enforced here. `require_signed_commit`
    is about the commit that carries the ratification, which does not exist at this point, so it is
    enforced by `selfmodel verify-intent` against the commit git says last changed the intent file.

    Neither makes ratification unforgeable by someone with the key and the commit rights. Both make it
    attributable, which is the property a review path can actually rest on.
    """
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as stream:
        policy = json.load(stream)

    approvers = policy.get("approvers")
    if approvers:
        if approved_by not in approvers:
            raise RatificationRefused(
                f"ratification policy at {path} does not list {approved_by!r} as an approver. "
                f"Listed: {', '.join(sorted(approvers))}"
            )

    if policy.get("require_signed_commit"):
        # This cannot be checked here, and pretending otherwise was worse than not checking. At this
        # point the ratification has not been written, let alone committed, so the only thing `git
        # verify-commit HEAD` can inspect is the commit before it. A process could ratify on top of
        # any signed HEAD and commit the intent unsigned, and the check would have passed. The
        # property is real but it is a property of a commit that does not exist yet, so it is
        # enforced by `selfmodel verify-intent` at the point where that commit does exist.
        print(
            f"note: {path} sets require_signed_commit. The commit carrying this ratification does "
            "not exist yet, so it cannot be verified here. Run `coherence-ratchet selfmodel "
            "verify-intent <intent>` in CI to enforce it against the commit that introduces the "
            "change.",
            file=sys.stderr,
        )

    return policy


def verify_intent(intent_path: str, *, policy_path: str | None = None, root: str | None = None) -> dict:
    """Check the commit that last changed the intent file, which is the one the policy is about.

    `check_ratification_policy` runs before the intent file is written, so the signature it could
    inspect is never the signature that matters. This runs afterwards, against the commit git says
    last touched the file, and is the surface a CI job should call.
    """
    import subprocess

    root = root or (os.path.dirname(intent_path) or ".")
    path = policy_path or policy_path_for(intent_path)
    policy = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    if not policy.get("require_signed_commit"):
        return {"checked": False, "reason": "no policy requires a signed commit"}

    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)

    rev = git("log", "-1", "--format=%H", "--", os.path.abspath(intent_path))
    sha = rev.stdout.strip()
    if rev.returncode != 0 or not sha:
        raise RatificationRefused(
            f"{intent_path} has no commit history, so the signature the policy requires cannot "
            "exist. Commit the intent file before verifying it."
        )

    verified = git("verify-commit", sha)
    if verified.returncode != 0:
        raise RatificationRefused(
            f"the commit that last changed {intent_path} ({sha[:12]}) does not carry a good "
            f"signature; `git verify-commit` exited {verified.returncode}. Sign that commit, or "
            "remove require_signed_commit from the policy."
        )

    signer = git("log", "-1", "--format=%GS", sha).stdout.strip()
    approvers = policy.get("approvers")
    if approvers and signer not in approvers:
        raise RatificationRefused(
            f"the commit that last changed {intent_path} ({sha[:12]}) is signed by {signer!r}, "
            f"who is not an approver. Listed: {', '.join(sorted(approvers))}"
        )
    return {"checked": True, "commit": sha, "signer": signer}


def ratify(model: dict, intent: dict, candidate_id: str, *, approved_by: str, rationale: str,
           scope: str, exceptions: list[str] | None = None,
           approved_at: str | None = None, review_date: str | None = None,
           advisers: list[str] | None = None, objections: list[str] | None = None,
           buy_in: str | None = None, superseded_at: str | None = None) -> dict:
    """Record a human decision that a candidate becomes intent.

    Ratified intent is the one artefact that issues imperative instructions to an agent, and it does
    so indefinitely, so it carries a review date and keeps its own history. `scope` is required: a
    scope that defaults to the whole tree is the failure the method names as design policing.
    """
    if not scope or not str(scope).strip():
        raise ValueError(
            "scope is required: an omitted scope ratifies the whole tree, which is the "
            "over-reach this method exists to prevent"
        )
    expected = model_hash(model)
    if intent.get("source_model_hash") != expected:
        raise ValueError("intent source_model_hash does not match the supplied model")
    candidate = next((item for item in model.get("candidates", []) if item["id"] == candidate_id), None)
    if candidate is None:
        raise ValueError(f"candidate not found: {candidate_id}")

    prior = [item for item in intent.get("ratifications", [])
             if item.get("candidate_id") == candidate_id and not item.get("superseded_by")]
    revision = 1 + max((item.get("revision", 1) for item in prior), default=0)

    # The identifier must differ between revisions, or a supersession link points at itself and the
    # history it is meant to preserve is unreadable. Revision 1 keeps the plain hash so existing intent
    # files and the printed record stay valid; later revisions mix the revision in.
    _seed = candidate_id + approved_by + scope
    if revision > 1:
        _seed += f"#{revision}"
    record = {
        "id": f"ratified:{_sha(_seed)[:16]}",
        "candidate_id": candidate_id,
        "kind": candidate["kind"],
        "contract": _contract_for(candidate),
        "scope": scope,
        "approved_by": approved_by,
        "approved_at": approved_at or datetime.date.today().isoformat(),
        "review_date": review_date,
        "rationale": rationale,
        "exceptions": list(exceptions or []),
        "revision": revision,
    }
    # Who was consulted, who objected, and at what level of buy-in the decision was taken. Recorded
    # only when supplied, so a solo ratification stays as terse as it was.
    if advisers:
        record["advisers"] = list(advisers)
    if objections:
        record["objections"] = list(objections)
    if buy_in:
        record["buy_in"] = buy_in

    # A superseded ratification is retained and linked, never dropped: intent that changes without
    # a trace is the least auditable artefact in a method whose argument is that intent is accountable.
    kept = []
    stamp = superseded_at or record["approved_at"]
    for item in intent.get("ratifications", []):
        if item.get("candidate_id") == candidate_id and not item.get("superseded_by"):
            item = dict(item)
            item["superseded_by"] = record["id"]
            item["superseded_at"] = stamp
        kept.append(item)

    updated = dict(intent)
    updated["ratifications"] = kept + [record]
    return updated


def context_pack(model: dict, intent: dict | None = None) -> str:
    """Render labelled evidence. Only ratified records use imperative language."""
    observed = model.get("observed", {})
    lines = [
        "# Coherence grounding pack",
        "",
        f"Source tree hash: `{model.get('source', {}).get('tree_hash', 'unknown')}`",
        f"Model hash: `{model_hash(model)}`",
        "",
        "## Ratified intent",
    ]
    # Superseded records stay in the intent file so intent has a history, but they must never reach the
    # grounding pack: a [RATIFIED] line is an imperative to an agent, and a decision that has been
    # replaced is no longer one. Rendering both would instruct against the current intent.
    ratifications = [item for item in (intent or {}).get("ratifications", [])
                     if not item.get("superseded_by")]
    if not ratifications:
        lines.append("- No ratified intent is available. Observations and candidates below are not instructions.")
    for item in ratifications:
        contract = json.dumps(item.get("contract", {}), sort_keys=True)
        lines.append(
            f"- [RATIFIED] Apply `{contract}` within `{item.get('scope', '.')}`. "
            f"Approved by {item.get('approved_by')} on {item.get('approved_at')}. "
            f"Rationale: {item.get('rationale')}"
        )
        for exception in item.get("exceptions", []):
            lines.append(f"  - Exception: {exception}")

    lines += ["", "## Observed structure"]
    for module in observed.get("modules", []):
        deps = ", ".join(module.get("depends_on", [])) or "none"
        lines.append(f"- [OBSERVED] `{module['module']}` depends on: {deps}.")
    for entity in observed.get("entities", []):
        if entity.get("kind") == "dict-shape":
            lines.append(
                f"- [OBSERVED] `{entity['name']}` string-key access appears in "
                f"{', '.join(entity['sites'])}; per-site keys: "
                f"{json.dumps(entity['per_site_keys'], sort_keys=True)}."
            )
        else:
            lines.append(
                f"- [OBSERVED] `{entity['name']}` ({entity.get('kind')}) in "
                f"`{entity.get('module')}` has fields {', '.join(entity.get('fields', []))}."
            )

    lines += ["", "## Candidates requiring judgement"]
    if not model.get("candidates"):
        lines.append("- No candidates were inferred.")
    for candidate in model.get("candidates", []):
        # The sites are the whole point of the artefact. The measured visibility result rests on the
        # model naming every site that computes a concept, and rendering the suggestion alone gave
        # an agent one site and left the divergent ones unnamed: a reuse_helper suggestion carries
        # the canonical site, while the sites needing the change live in the candidate's evidence.
        # A pack that omits them cannot do the job the pack exists to do.
        evidence = candidate.get("evidence") or {}
        # reuse_helper and entity_shape record `sites`; shared_value records the `modules` that
        # carry the literal. Either way it is the locations that make the candidate actionable.
        sites = evidence.get("sites") or evidence.get("modules") or []
        detail = ""
        if sites:
            detail = " Sites: " + ", ".join(f"`{site}`" for site in sites) + "."
        lines.append(
            f"- [CANDIDATE] `{candidate['id']}` ({candidate['confidence']} confidence): "
            f"{json.dumps(candidate.get('suggestion', {}), sort_keys=True)}.{detail}"
        )
    return "\n".join(lines) + "\n"


def write(root: str, out_path: str) -> dict:
    model = derive(root)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, sort_keys=True)
        f.write("\n")
    return model


# --- CLI wiring (called from cli.py) ----------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser("selfmodel", help="derive facts, query evidence, ratify intent, or render context")
    p.add_argument("action", choices=["derive", "query", "ratify", "context", "verify-intent"])
    p.add_argument("target", help="source path (derive/context) or a question (query)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="path to selfmodel.json")
    p.add_argument("--intent", default=DEFAULT_INTENT, help="path to the human-owned intent file")
    p.add_argument("--llm", action="store_true", help="use the optional LLM matcher (needs an API key)")
    p.add_argument("--out", help="write output to this path (context)")
    p.add_argument("--by", dest="approved_by", help="ratifier identity (ratify)")
    p.add_argument("--policy", help="ratification policy file (ratify); defaults to "
                                    "ratification-policy.json beside the intent file, and no policy "
                                    "file means no check")
    p.add_argument("--rationale", help="why the candidate is sanctioned (ratify)")
    p.add_argument("--scope", help="scope of a ratification (required; no default)")
    p.add_argument("--exception", action="append", default=[], help="declared exception (repeatable)")
    p.add_argument("--review-date", dest="review_date",
                   help="when this intent must be re-examined (ratify)")
    p.add_argument("--adviser", action="append", default=[],
                   help="who was consulted (repeatable, ratify)")
    p.add_argument("--objection", action="append", default=[],
                   help="an objection recorded but not resolved (repeatable, ratify)")
    p.add_argument("--buy-in", dest="buy_in",
                   help="level of buy-in the decision was taken at (ratify)")
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    from . import query as q

    if args.action == "derive":
        model = write(args.target, args.model)
        print(f"self-model derived from {args.target} -> {args.model}")
        observed = model["observed"]
        print(f"  observed modules: {len(observed['modules'])}  functions: {len(observed['functions'])}  "
              f"entities: {len(observed['entities'])}  candidates: {len(model['candidates'])}")
        print(f"  model hash: {model['model_hash']}")
        return 0
    if args.action == "query":
        model = _load_json(args.model)
        intent = _load_json(args.intent) if os.path.exists(args.intent) else None
        result = q.answer(model, args.target, intent=intent, use_llm=args.llm)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            q.render(result)
        return 0
    if args.action == "ratify":
        if not (args.approved_by and args.rationale):
            print("selfmodel ratify requires --by and --rationale", file=sys.stderr)
            return 2
        # Authority is checked before any work is done. A ratifier the policy will not admit is
        # refused whatever the state of the model file, because the refusal is about who is asking.
        try:
            check_ratification_policy(
                args.policy or policy_path_for(args.intent),
                approved_by=args.approved_by,
                root=os.path.dirname(args.intent) or ".",
            )
        except RatificationRefused as exc:
            print(str(exc), file=sys.stderr)
            return 2
        model = _load_json(args.model)
        intent = _load_json(args.intent) if os.path.exists(args.intent) else empty_intent(model)
        try:
            updated = ratify(
                model, intent, args.target, approved_by=args.approved_by,
                rationale=args.rationale, scope=args.scope, exceptions=args.exception,
                review_date=args.review_date, advisers=args.adviser,
                objections=args.objection, buy_in=args.buy_in,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        os.makedirs(os.path.dirname(args.intent) or ".", exist_ok=True)
        with open(args.intent, "w", encoding="utf-8") as stream:
            json.dump(updated, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(f"candidate {args.target} ratified -> {args.intent}")
        return 0
    if args.action == "verify-intent":
        try:
            report = verify_intent(args.intent, policy_path=args.policy,
                                   root=os.path.dirname(args.intent) or ".")
        except RatificationRefused as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if not report["checked"]:
            print(report["reason"])
        else:
            print(f"intent signed by {report['signer']} in {report['commit'][:12]}")
        return 0

    if args.action == "context":
        model = _load_json(args.model)
        fresh = derive(args.target)
        expected = model_hash(model)
        if model_hash(fresh) != expected:
            print("saved self-model is stale for this source tree; run selfmodel derive", file=sys.stderr)
            return 2
        intent = _load_json(args.intent) if os.path.exists(args.intent) else empty_intent(model)
        if intent.get("source_model_hash") != expected:
            print("intent does not match the saved self-model; re-ratify against the current model", file=sys.stderr)
            return 2
        pack = context_pack(model, intent)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(pack)
            print(f"grounding pack written to {args.out}")
        else:
            print(pack, end="")
        return 0
    return 2


if __name__ == "__main__":
    print(json.dumps(derive(sys.argv[1]), indent=2, sort_keys=True))
