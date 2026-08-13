"""An agent-facing interface that returns standing, not findings.

Several tools now expose a codebase model to coding agents over MCP, and they are good at what they
do. What none of them can answer is the question this method exists to make answerable: *did a person
agree to this, and who was it?* They return derived facts, scored findings, and generated advice, all
of it inferred, none of it signed. An agent reading them cannot tell a decision from an accident,
which is precisely the confusion the three labels exist to prevent.

The argument for building this is stronger than differentiation. If an agent working in a reader's
editor can reach a derived-heuristics server and cannot reach the ratified intent, then the
heuristics instruct the agent and the human-approved lines do not — the method inverted, inside the
reader's own tooling. Shipping the epistemics only as a markdown file loses that argument by default.

So every response here carries its label and, where something is ratified, a typed provenance object:
who approved it, when, in what scope, on what rationale, and when it is due for review. Three
properties follow, and each is a deliberate design choice rather than an implementation detail.

**`NONE` is a first-class answer.** Asked for the canonical form of something nobody has ratified,
this server says so plainly instead of reaching for the most frequent shape. A derived model of "how
we do things here" that nobody confirmed is an automated guess wearing the authority of a decision,
and an agent told "there is no canonical answer" behaves better than one handed a confident guess.

**Nothing here mutates intent.** Ratification is a human act at a terminal, with `--by`, `--scope`
and `--rationale` recorded. The server is read-only, and that is what makes the contract enforceable
rather than aspirational.

**One tool exists only to refuse.** `coherence_ratify` is advertised in the tool list and always
returns an error explaining that an agent cannot approve its own grounding. Advertising the refusal
means the agent discovers the boundary by reading the tool list, rather than inventing a way around a
boundary it never saw.

The transport is newline-delimited JSON-RPC 2.0 over stdin and stdout, implemented here in about two
hundred lines of standard library, so the package keeps its zero-runtime-dependency property.
"""

from __future__ import annotations

import json
import os
import sys

PROTOCOL_VERSION = "2024-11-05"

_REFUSAL = (
    "Ratification requires a person at a terminal running "
    "`coherence-ratchet selfmodel ratify <candidate-id> --by NAME --scope SCOPE --rationale TEXT`. "
    "An agent cannot approve its own grounding. Surface the candidate in your summary and stop."
)


def _load(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _live(intent: dict) -> list[dict]:
    return [r for r in (intent or {}).get("ratifications", []) if not r.get("superseded_by")]


def _provenance(record: dict) -> dict:
    return {
        "approved_by": record.get("approved_by"),
        "approved_at": record.get("approved_at"),
        "scope": record.get("scope"),
        "rationale": record.get("rationale"),
        "review_date": record.get("review_date"),
        "buy_in": record.get("buy_in"),
        "revision": record.get("revision"),
    }


class Server:
    """The tool implementations, separated from the transport so they can be tested directly."""

    def __init__(self, root: str, model_path: str, intent_path: str, ledger_path: str):
        self.root = root
        self.model_path = model_path
        self.intent_path = intent_path
        self.ledger_path = ledger_path

    # --- freshness ---------------------------------------------------------

    def _staleness(self) -> dict:
        """Every response says whether it describes the tree as it stands."""
        from .selfmodel import derive, model_hash

        model = _load(self.model_path)
        if not model:
            return {"stale": True, "reason": "no self-model has been derived"}
        try:
            current = model_hash(derive(self.root))
        except Exception as exc:
            return {"stale": True, "reason": f"the tree could not be measured: {exc}"}
        saved = model_hash(model)
        if saved != current:
            return {"stale": True, "reason": "the saved self-model is stale for this source tree",
                    "model_hash": saved, "current_model_hash": current}
        return {"stale": False, "model_hash": saved}

    # --- tools -------------------------------------------------------------

    def canonical(self, concept: str, scope: str | None = None) -> dict:
        """Standing for a concept: ratified, merely observed, or nothing at all."""
        intent = _load(self.intent_path)
        model = _load(self.model_path)
        state = self._staleness()

        for record in _live(intent):
            contract = record.get("contract") or {}
            haystack = " ".join(str(v) for v in contract.values()).lower()
            if concept.lower() in haystack:
                if scope and record.get("scope") and scope.lower() not in record["scope"].lower():
                    continue
                return {
                    "status": "RATIFIED",
                    "binding": True,
                    "concept": concept,
                    "instruction": f"Use `{contract.get('reuse_site')}` for {contract.get('concept', concept)}.",
                    "reuse_site": contract.get("reuse_site"),
                    "exceptions": record.get("exceptions", []),
                    "provenance": _provenance(record),
                    **state,
                }

        # A stale model may not supply observations: describing a tree that no longer exists is worse
        # than declining to describe it.
        if state["stale"]:
            return {"status": "NONE", "binding": False, "concept": concept,
                    "refusal": "The model is not current, so nothing can be said about this concept.",
                    **state}

        for candidate in model.get("candidates", []):
            if concept.lower() in json.dumps(candidate).lower():
                evidence = candidate.get("evidence") or {}
                return {
                    "status": "CANDIDATE",
                    "binding": False,
                    "concept": concept,
                    "warning": ("This is an unratified heuristic, not an instruction. Nobody has "
                                "approved it. Name it in your summary and stop for a human."),
                    "candidate_id": candidate.get("id"),
                    "confidence": candidate.get("confidence"),
                    "sites": evidence.get("sites") or evidence.get("modules") or [],
                    **state,
                }

        return {
            "status": "NONE",
            "binding": False,
            "concept": concept,
            "refusal": (f"Nothing is ratified for `{concept}`"
                        + (f" in scope `{scope}`" if scope else "")
                        + ". There is no canonical answer to give you. Proceed, and say in your "
                          "summary what you chose."),
            **state,
        }

    def grounding(self, scope: str | None = None) -> dict:
        from .selfmodel import context_pack, empty_intent

        state = self._staleness()
        model = _load(self.model_path)
        if not model:
            return {"error": "no self-model; run `coherence-ratchet selfmodel derive`", **state}
        intent = _load(self.intent_path) or empty_intent(model)
        return {"pack": context_pack(model, intent), "scope": scope, **state}

    def exposure(self, path: str | None = None) -> dict:
        """Open coherence-debt entries covering a path.

        Telling an agent that a region carries accepted debt, who owns it and when it is reviewed, is
        the single most useful thing to say before it edits a seam, and nothing else exposes it.
        """
        from .report import _load_ledger, _open_entries

        records = _load_ledger(self.ledger_path)
        entries = _open_entries(records)
        if path:
            entries = [e for e in entries
                       if path.lower() in (e.get("region") or "").lower()
                       or (e.get("region") or "").lower() in path.lower()]
        return {
            "open_entries": [{
                "region": e.get("region"),
                "owner": e.get("owner"),
                "exposure": e.get("exposure"),
                "trigger": e.get("trigger"),
                "review_date": e.get("review_date"),
                "accepted_on": e.get("when"),
                "note": e.get("note"),
            } for e in entries],
            "advisory": True,
            "note": ("Accepted debt is a decision somebody recorded, not a defect to fix in passing. "
                     "If your change touches one of these regions, say so."),
        }

    def advise(self, diff: str) -> dict:
        from . import advise as advise_mod

        state = self._staleness()
        files = advise_mod._added_paths_from_diff(diff)
        files = {os.path.join(self.root, os.path.basename(f)) if not os.path.isabs(f) else f
                 for f in files}
        findings = advise_mod.analyse(self.root, files, _load(self.model_path),
                                      _load(self.intent_path))
        return {
            "findings": findings,
            "revision_instruction": "\n\n".join(
                advise_mod.render_instruction(f) for f in findings),
            "note": ("Only a RATIFIED_CONFLICT is an instruction. A CANDIDATE_COLLISION is surfaced "
                     "for a human to judge and must not be resolved on your own authority."),
            **state,
        }

    def ratify(self, **_kwargs) -> dict:
        raise ToolRefused(_REFUSAL)


class ToolRefused(Exception):
    """A tool that exists so the agent can discover the boundary by reading the tool list."""


TOOLS = [
    {
        "name": "coherence_canonical",
        "description": (
            "The standing of a concept in this codebase: RATIFIED (a person approved it; binding, "
            "with provenance), CANDIDATE (a heuristic nobody approved; not an instruction), or NONE "
            "(nothing is ratified, and there is no canonical answer)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "the concept, e.g. 'retry' or 'to_cents'"},
                "scope": {"type": "string", "description": "optional scope to filter by"},
            },
            "required": ["concept"],
        },
    },
    {
        "name": "coherence_grounding",
        "description": (
            "The labelled grounding pack. Only [RATIFIED] lines are instructions; [OBSERVED] lines "
            "describe what exists; [CANDIDATE] lines are heuristics and must not be acted on."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"scope": {"type": "string"}},
        },
    },
    {
        "name": "coherence_exposure",
        "description": (
            "Open coherence-debt entries covering a path: who accepted them, on what trigger, and "
            "when they are due for review. Read this before editing a seam."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
    },
    {
        "name": "coherence_advise",
        "description": (
            "Measure a unified diff against what the codebase already contains. Returns findings and "
            "a revision instruction. Only a RATIFIED_CONFLICT is an instruction."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"diff": {"type": "string", "description": "a unified diff"}},
            "required": ["diff"],
        },
    },
    {
        "name": "coherence_ratify",
        "description": (
            "REFUSES. Ratification is a human act. This tool exists so that the boundary is visible "
            "in the tool list rather than discovered by working around it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"candidate_id": {"type": "string"}, "rationale": {"type": "string"}},
        },
    },
]


# --- transport: newline-delimited JSON-RPC 2.0 over stdio --------------------

def _result(request_id, payload):
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _text_content(payload) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, sort_keys=True)}]}


def handle(server: Server, message: dict):
    """One request in, one response out (or None for a notification)."""
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "coherence-ratchet", "version": _tool_version()},
        })

    if method in ("notifications/initialized", "initialized"):
        return None

    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handlers = {
            "coherence_canonical": lambda: server.canonical(
                arguments.get("concept", ""), arguments.get("scope")),
            "coherence_grounding": lambda: server.grounding(arguments.get("scope")),
            "coherence_exposure": lambda: server.exposure(arguments.get("path")),
            "coherence_advise": lambda: server.advise(arguments.get("diff", "")),
            "coherence_ratify": lambda: server.ratify(**arguments),
        }
        if name not in handlers:
            return _error(request_id, -32601, f"unknown tool: {name}")
        try:
            return _result(request_id, _text_content(handlers[name]()))
        except ToolRefused as exc:
            # A refusal is a tool result the agent can read and reason about, not a transport error.
            return _result(request_id, {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            })
        except Exception as exc:  # pragma: no cover - defensive
            return _error(request_id, -32603, f"{type(exc).__name__}: {exc}")

    return _error(request_id, -32601, f"unknown method: {method}")


def _tool_version() -> str:
    from .cli import _version

    return _version()


def serve(server: Server, stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(server, message)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0


def register_cli(sub) -> None:
    p = sub.add_parser("serve", help="expose ratified intent to coding agents over MCP (stdio)")
    p.add_argument("path", help="the package directory the model describes")
    p.add_argument("--model", default="coherence/selfmodel.json")
    p.add_argument("--intent", default="coherence/intent.json")
    p.add_argument("--ledger", default="coherence/coherence-ledger.jsonl")


def run_cli(args) -> int:
    from .paths import resolve_root

    resolve_root(args.path)
    return serve(Server(args.path, args.model, args.intent, args.ledger))
