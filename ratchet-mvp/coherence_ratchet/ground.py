"""Put ratified intent where the agents actually read it, and fail when it goes stale.

`selfmodel context` renders a grounding pack to a file and the trail ended there. Nothing consumed
it, so the loop the method describes — derive, ratify, ground, author, detect, hold — was open at its
most important join: the point where what a team decided reaches the thing writing the code.

This module closes it by writing into the files coding agents already read. The primary target is
`AGENTS.md`, the vendor-neutral convention every major agent reads, rather than any one vendor's
file; Claude Code picks it up through its own `@AGENTS.md` import, so targeting the standard costs a
reader nothing and dates better.

Three design decisions carry most of the weight.

**A managed block, never the whole file.** `AGENTS.md` is a shared human artefact that already exists
in most repositories. A tool that owns the file is a tool that gets deleted the first time it
overwrites somebody's notes, so this one rewrites only between its own markers and leaves every other
byte alone.

**The marker carries the hashes.** That is what makes staleness checkable rather than hoped about.
`ground --check` re-derives the tree and fails when the block describes a tree that no longer exists,
which turns the book's thesis into a build failure: the pull request stops when the file the agents
read no longer describes the code they are editing.

**The block states its own epistemic contract in plain words.** A derived model of "how we do things
here" that nobody confirmed is an automated guess wearing the authority of a decision. The labels are
not decoration; they are the difference between grounding an agent and laundering the codebase's
accidents into instructions. Only `[RATIFIED]` lines are imperative, and the block says so where the
agent will read it.
"""

from __future__ import annotations

import datetime
import os
import re

from .exitcodes import EXIT_HELD, EXIT_REFUSED
from .paths import resolve_root
from .selfmodel import _load_json, context_pack, derive, empty_intent, model_hash

BEGIN = "<!-- coherence-ratchet:begin"
END = "<!-- coherence-ratchet:end -->"

# Default targets, primary first. AGENTS.md is the vendor-neutral convention; the rest are named so a
# reader on one specific harness does not have to work out the mapping.
KNOWN_TARGETS = ("AGENTS.md", "CLAUDE.md", ".cursorrules", ".github/copilot-instructions.md")

DEFAULT_MAX_CANDIDATES = 25

_PREAMBLE = """\
These statements carry epistemic labels, and the labels are binding.

- **[RATIFIED]** — a named person approved this, in the scope shown, on the date shown. These are
  instructions. Follow them.
- **[OBSERVED]** — a fact read from the code at the revision in the marker above. It describes what
  exists. It does not tell you what to do.
- **[CANDIDATE]** — a heuristic inference that nobody has approved. It is not policy. Do not act on
  it. If it is relevant to your change, say so in your summary and ask.

Frequency is not authority. A pattern appearing many times in this codebase may be a decision or may
be an accident nobody has revisited, and only the [RATIFIED] section tells you which.
"""

_CLOSING = """\
### Before you finish

Run `coherence-ratchet advise --staged` and act on any finding that names ratified intent. A finding
that names only a candidate is for a human to judge: report it, do not resolve it on your own
authority.
"""


class GroundingStale(Exception):
    """The committed block no longer describes the tree it claims to describe."""


def _marker(model: dict, tool_version: str, today: str) -> str:
    tree = model.get("source", {}).get("tree_hash", "unknown")
    return (f"{BEGIN} model={model_hash(model)} tree={tree} "
            f"generated={today} tool={tool_version} -->")


def _cap_candidates(pack: str, limit: int) -> str:
    """Keep the pack inside a sane prompt budget, and say so rather than truncating silently."""
    if limit is None or limit <= 0:
        return pack
    lines = pack.split("\n")
    out, seen, dropped = [], 0, 0
    for line in lines:
        if line.startswith("- [CANDIDATE]"):
            seen += 1
            if seen > limit:
                dropped += 1
                continue
        out.append(line)
    if dropped:
        out.append(
            f"- ...and {dropped} further candidates, not shown. Query them with "
            f"`coherence-ratchet selfmodel query`."
        )
    return "\n".join(out)


def render_block(model: dict, intent: dict, *, tool_version: str, today: str,
                 max_candidates: int = DEFAULT_MAX_CANDIDATES) -> str:
    """The managed block, markers included."""
    pack = context_pack(model, intent)
    # The pack's own title and hash preamble are replaced here: the marker already carries the
    # hashes, and a second copy is one more thing to drift.
    body = pack.split("\n")
    while body and not body[0].startswith("## "):
        body.pop(0)
    pack_body = _cap_candidates("\n".join(body).rstrip(), max_candidates)

    return "\n".join([
        _marker(model, tool_version, today),
        "## Grounding for this repository",
        "",
        _PREAMBLE,
        pack_body,
        "",
        _CLOSING,
        END,
    ]) + "\n"


def _split(text: str) -> tuple[str, str | None, str]:
    """(before, existing_block, after). Raises when the markers are unbalanced."""
    starts = [m.start() for m in re.finditer(re.escape(BEGIN), text)]
    ends = [m.start() for m in re.finditer(re.escape(END), text)]
    if len(starts) != len(ends):
        raise GroundingStale(
            "unbalanced coherence-ratchet markers; refusing to guess where the managed block ends"
        )
    if len(starts) > 1:
        raise GroundingStale("more than one coherence-ratchet block; remove the duplicates")
    if not starts:
        return text, None, ""
    start, end = starts[0], ends[0] + len(END)
    return text[:start], text[start:end], text[end:]


def apply_to_file(path: str, block: str) -> str:
    """Write the block into ``path``, preserving every byte outside the markers."""
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            existing = f.read()
    before, current, after = _split(existing)
    if current is None:
        joiner = "" if not before or before.endswith("\n\n") else ("\n" if before.endswith("\n") else "\n\n")
        return before + joiner + block + after
    return before + block.rstrip("\n") + after


def block_hashes(text: str) -> dict[str, str]:
    """The model and tree hashes a committed block declares, or an empty dict."""
    match = re.search(re.escape(BEGIN) + r"(.*?)-->", text, re.S)
    if not match:
        return {}
    return dict(re.findall(r"(\w+)=(\S+)", match.group(1)))


# --- CLI --------------------------------------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser(
        "ground",
        help="write ratified intent into the files coding agents read, and check it is current",
    )
    p.add_argument("path", help="the package directory the model describes")
    p.add_argument("--model", default="coherence/selfmodel.json")
    p.add_argument("--intent", default="coherence/intent.json")
    p.add_argument("--target", action="append", default=[],
                   help=f"file to write (repeatable). Default AGENTS.md. Known: {', '.join(KNOWN_TARGETS)}")
    p.add_argument("--check", action="store_true",
                   help="verify the committed block matches a fresh derivation; write nothing")
    p.add_argument("--dry-run", action="store_true", help="print the block instead of writing it")
    p.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES,
                   help="cap the candidate list; the block states how many were omitted")


def run_cli(args) -> int:
    import sys

    from .cli import _version

    resolve_root(args.path)
    targets = args.target or ["AGENTS.md"]

    fresh = derive(args.path)
    expected = model_hash(fresh)

    if args.check:
        stale = []
        for target in targets:
            if not os.path.exists(target):
                print(f"refused: {target} has no grounding block; run `coherence-ratchet ground`",
                      file=sys.stderr)
                return EXIT_REFUSED
            with open(target, encoding="utf-8") as f:
                declared = block_hashes(f.read())
            if not declared:
                print(f"refused: {target} has no coherence-ratchet block", file=sys.stderr)
                return EXIT_REFUSED
            if declared.get("model") != expected:
                stale.append((target, declared.get("model"), expected))
        if stale:
            for target, was, now in stale:
                print(
                    f"refused: the grounding in {target} describes a tree that no longer exists "
                    f"(block model={was}, current model={now}); run `coherence-ratchet ground`",
                    file=sys.stderr,
                )
            return EXIT_REFUSED
        print(f"grounding is current ({len(targets)} file(s), model {expected[:12]})")
        return EXIT_HELD

    model = _load_json(args.model) if os.path.exists(args.model) else fresh
    if model_hash(model) != expected:
        print("refused: the saved self-model is stale for this source tree; "
              "run `coherence-ratchet selfmodel derive`", file=sys.stderr)
        return EXIT_REFUSED

    intent = _load_json(args.intent) if os.path.exists(args.intent) else empty_intent(model)
    if intent.get("source_model_hash") != model_hash(model):
        print("refused: intent does not match the saved self-model; "
              "re-ratify against the current model", file=sys.stderr)
        return EXIT_REFUSED

    today = datetime.date.today().isoformat()
    block = render_block(model, intent, tool_version=_version(), today=today,
                         max_candidates=args.max_candidates)

    if args.dry_run:
        print(block, end="")
        return EXIT_HELD

    for target in targets:
        directory = os.path.dirname(target)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            updated = apply_to_file(target, block)
        except GroundingStale as exc:
            print(f"refused: {target}: {exc}", file=sys.stderr)
            return EXIT_REFUSED
        with open(target, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"grounding written to {target}")
    return EXIT_HELD
