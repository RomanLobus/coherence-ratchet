"""Dispatch probe prompts to a pinned model, persist everything, and score offline.

Transport is pluggable so the same probe can be replicated across model families without touching
the probe. Only the Anthropic transport ships, because it is the one the package already carries; a
second family is a function of the same shape, injected with ``--transport`` or in a test.
"""

from __future__ import annotations

import datetime
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys

HARNESS_VERSION = "1"

# A dated snapshot carries its date in the identifier, in either convention the vendors use:
# `claude-haiku-4-5-20251001` or `gpt-5.4-2026-03-05`. A bare alias points at a moving target,
# which makes a replication silently cross-model, so it is refused either way.
_DATED = re.compile(r"(\d{8}|\d{4}-\d{2}-\d{2})$")


class DispatchRefused(Exception):
    """The run would not be reproducible-as-recorded, so it does not start."""


# --- probe contract ---------------------------------------------------------

class ProbeContract:
    """What the dispatcher needs from a probe module.

    ``build_prompt(condition) -> str`` is required. Scoring is delegated back to the probe, because
    the probe owns what counts as reuse for its own fixture.
    """

    def __init__(self, module):
        self.module = module
        self.name = getattr(module, "__name__", "probe")
        if not hasattr(module, "build_prompt"):
            raise DispatchRefused(
                f"{self.name} has no build_prompt(condition); the dispatcher has nothing to send"
            )

    def build_prompt(self, condition: str) -> str:
        return self.module.build_prompt(condition)

    def followup(self, first_response: str, ask) -> str | None:
        """The second-round prompt, or None when the probe is single-shot.

        ``ask(prompt) -> str`` lets a probe make its own model call, which is how a detector arm is
        built: the probe inspects the first response, asks a detector what it collides with, and
        returns a revision prompt carrying that finding. Probes without this method are unaffected.
        """
        fn = getattr(self.module, "followup", None)
        return fn(first_response, ask) if fn else None

    def score(self, code: str, condition: str) -> dict:
        scorer = getattr(self.module, "score_code", None)
        if scorer is None:
            return {}
        names = getattr(self.module, "CANONICAL_NAMES", {}).get(condition)
        return scorer(code, *names) if names else scorer(code)

    def source_hash(self) -> str:
        path = getattr(self.module, "__file__", None)
        if not path or not os.path.exists(path):
            return "unknown"
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()


def load_probe(name: str) -> ProbeContract:
    """Import a probe by module name, or by path to a probe file."""
    if name.endswith(".py") and os.path.exists(name):
        spec = importlib.util.spec_from_file_location(
            os.path.basename(name)[:-3], os.path.abspath(name))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(name)
    return ProbeContract(module)


# --- transports -------------------------------------------------------------

def anthropic_transport(prompt: str, *, model: str, temperature: float, max_tokens: int) -> str:
    """One call to the messages API. The same stdlib transport the semantic gate uses."""
    import urllib.request

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise DispatchRefused("ANTHROPIC_API_KEY is not set")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.load(resp)
    return json.dumps(payload)


def openai_transport(prompt: str, *, model: str, temperature: float, max_tokens: int) -> str:
    """One call to the chat-completions API, in the same shape as the Anthropic transport.

    The vendors disagree on parameter names, and on which parameters a given tier accepts, so a
    rejected parameter is dropped and the call retried once. The alternative is a replication that
    fails for a reason with nothing to do with the experiment.
    """
    import urllib.error
    import urllib.request

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise DispatchRefused("OPENAI_API_KEY is not set")

    def _post(body):
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"content-type": "application/json", "authorization": "Bearer " + key},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.dumps(json.load(resp))

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        return _post(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        retried = dict(body)
        if "temperature" in detail:
            retried.pop("temperature", None)
        if "max_completion_tokens" in detail:
            retried["max_tokens"] = retried.pop("max_completion_tokens", max_tokens)
        if retried == body:
            raise DispatchRefused("openai rejected the request: " + detail[:300]) from None
        return _post(retried)


def _text_of(raw: str) -> str:
    """The assistant text, whichever vendor produced the envelope.

    Returning the raw envelope when the shape is unrecognised would score every trial against a wall
    of JSON, so an unknown shape is worth failing loudly on rather than silently mis-scoring.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(payload, dict):
        return raw
    if "content" in payload:  # anthropic messages
        return "".join(b.get("text", "") for b in payload.get("content", []) if isinstance(b, dict))
    if "choices" in payload:  # openai chat completions
        return "".join((c.get("message") or {}).get("content") or ""
                       for c in payload.get("choices", []) if isinstance(c, dict))
    return raw


_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> str:
    """Every fenced code block, joined, or the whole response when a model returned bare code.

    Taking only the first block silently truncated any response that returned more than one file, and
    a multi-file probe then scored the missing files as unchanged. The failure looked like a model
    error rather than a harness one, which is the worst shape a measurement bug can take. Joining is
    identical for a single-block response.
    """
    text = text or ""
    out, last_end = [], 0
    for m in _FENCE.finditer(text):
        # Vendors disagree about where a file header goes. One writes it inside the fence, another
        # on the line above it. Keeping the preceding header line means a multi-file response is
        # attributable either way; dropping it silently merged every file into the first one.
        preamble = [l for l in text[last_end:m.start()].split("\n") if l.strip()]
        header = preamble[-1] if preamble and preamble[-1].lstrip().startswith("#") else ""
        body = m.group(1)
        out.append(f"{header}\n{body}" if header and header.strip() not in body else body)
        last_end = m.end()
    if not out:
        return text
    return "\n".join(out)


# --- manifest ---------------------------------------------------------------

class Manifest(dict):
    """Everything that makes a run reproducible-as-recorded."""

    @classmethod
    def build(cls, *, probe: ProbeContract, conditions, trials, model, temperature,
              max_tokens, started_at, prompts) -> "Manifest":
        return cls({
            "harness_version": HARNESS_VERSION,
            "probe_module": probe.name,
            "probe_sha256": probe.source_hash(),
            "prompt_sha256": {c: hashlib.sha256(p.encode()).hexdigest()
                              for c, p in prompts.items()},
            "conditions": list(conditions),
            "trials": trials,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "started_at": started_at,
            "errors": {},
        })


def _require_dated_model(model: str) -> None:
    if not model:
        raise DispatchRefused("pass --model; there is no default, because the default would drift")
    if not _DATED.search(model):
        raise DispatchRefused(
            f"'{model}' is an alias, not a dated snapshot. An alias points at a moving "
            f"target, so the run could not be compared with a later one. Pass a dated identifier "
            f"such as 'claude-haiku-4-5-20251001'."
        )


# --- dispatch ---------------------------------------------------------------

def dispatch(probe: ProbeContract, conditions, *, trials: int, model: str, out_dir: str,
             temperature: float = 1.0, max_tokens: int = 2000, transport=None,
             now: str | None = None, dry_run: bool = False) -> dict:
    """Run ``trials`` per condition, persist every response, and write the manifest."""
    _require_dated_model(model)
    transport = transport or (openai_transport if model.startswith(("gpt-", "o1", "o3", "o4"))
                              else anthropic_transport)
    prompts = {c: probe.build_prompt(c) for c in conditions}

    if dry_run:
        total = trials * len(conditions)
        approx = sum(len(p) for p in prompts.values()) // 4 * trials
        return {"dry_run": True, "calls": total,
                "approx_prompt_tokens": approx,
                "conditions": list(conditions), "model": model}

    started = now or datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = Manifest.build(probe=probe, conditions=conditions, trials=trials, model=model,
                              temperature=temperature, max_tokens=max_tokens,
                              started_at=started, prompts=prompts)
    os.makedirs(out_dir, exist_ok=True)

    for condition in conditions:
        cdir = os.path.join(out_dir, condition)
        os.makedirs(cdir, exist_ok=True)
        for i in range(trials):
            raw_path = os.path.join(cdir, f"trial-{i:02d}.raw.json")
            if os.path.exists(raw_path):
                continue  # resume: a completed trial is never re-billed
            try:
                raw = transport(prompts[condition], model=model, temperature=temperature,
                                max_tokens=max_tokens)
            except Exception as exc:
                # A failed trial is recorded, never dropped. Dropping it would quietly change the
                # denominator, which is the way a sample size lies.
                manifest["errors"].setdefault(condition, []).append({"trial": i, "error": str(exc)})
                continue
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(raw)
            first_code = extract_code(_text_of(raw))
            with open(os.path.join(cdir, f"trial-{i:02d}.round0.py"), "w", encoding="utf-8") as f:
                f.write(first_code)

            final_code = first_code
            try:
                def ask(p, _t=transport, _m=model, _temp=temperature, _mt=max_tokens):
                    return _text_of(_t(p, model=_m, temperature=_temp, max_tokens=_mt))

                second = probe.followup(_text_of(raw), ask)
            except Exception as exc:
                manifest["errors"].setdefault(condition, []).append(
                    {"trial": i, "stage": "followup", "error": str(exc)})
                second = None
            if second:
                try:
                    raw2 = transport(second, model=model, temperature=temperature,
                                     max_tokens=max_tokens)
                    with open(os.path.join(cdir, f"trial-{i:02d}.followup.raw.json"),
                              "w", encoding="utf-8") as f:
                        f.write(raw2)
                    final_code = extract_code(_text_of(raw2))
                except Exception as exc:
                    manifest["errors"].setdefault(condition, []).append(
                        {"trial": i, "stage": "round1", "error": str(exc)})

            with open(os.path.join(cdir, f"trial-{i:02d}.extracted.py"), "w", encoding="utf-8") as f:
                f.write(final_code)

    manifest["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat() if not now else now
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(dict(manifest), f, indent=2, sort_keys=True)
        f.write("\n")
    return dict(manifest)


def rescore(probe: ProbeContract, out_dir: str, *, force: bool = False) -> dict:
    """Score the persisted responses. No model call, so a reader without a key can still check.

    Refuses to overwrite scores that a different scorer produced unless asked. A superseded run is
    kept as the record of what was claimed at the time, and re-scoring it in place destroys that
    record silently: the numbers change, git shows a diff nobody reads, and the write-up that cites
    them now cites something else. Rescoring the *current* run is the normal case and is unaffected,
    because the scores it writes match the scores already there.
    """
    manifest_path = os.path.join(out_dir, "manifest.json")
    manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {}
    existing_path = os.path.join(out_dir, "scores.json")
    existing = None
    if os.path.exists(existing_path) and not force:
        with open(existing_path, encoding="utf-8") as f:
            existing = f.read()
    results: dict[str, list[dict]] = {}
    for condition in sorted(os.listdir(out_dir)):
        cdir = os.path.join(out_dir, condition)
        if not os.path.isdir(cdir):
            continue
        # Re-extract from the committed raw responses first, so a corrected extractor reaches runs
        # already on disk. This is the whole reason the raw response is kept.
        for name in sorted(os.listdir(cdir)):
            if name.endswith(".raw.json"):
                with open(os.path.join(cdir, name), encoding="utf-8") as f:
                    raw = f.read()
                target = os.path.join(cdir, name.replace(".raw.json", ".extracted.py"))
                with open(target, "w", encoding="utf-8") as f:
                    f.write(extract_code(_text_of(raw)))
        scores = []
        for name in sorted(os.listdir(cdir)):
            if not name.endswith(".extracted.py"):
                continue
            with open(os.path.join(cdir, name), encoding="utf-8") as f:
                scores.append({"trial": name, **probe.score(f.read(), condition)})
        if scores:
            results[condition] = scores
    fresh = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if existing is not None and existing != fresh:
        raise DispatchRefused(
            f"{existing_path} was produced by a different scorer: re-scoring would change the "
            "committed numbers. If this run is superseded, leave it alone; it is the record of what "
            "was claimed. If you mean to replace it, pass force=True and say so in the write-up."
        )
    with open(existing_path, "w", encoding="utf-8") as f:
        f.write(fresh)
    # Bind the committed scores to the scorer that produced them. The collection manifest pins the
    # probe as it stood when the responses were bought, and a scorer corrected afterwards moves that
    # hash without any prompt changing. Recording the two separately is what lets a reader check
    # that scores.json is derivable from the committed responses by the committed scorer, which is
    # the property the evidence class actually asks for. Altering the collection manifest instead
    # would make the run claim it was scored by code that did not exist when it ran.
    rescored = {
        "scorer_sha256": probe.source_hash(),
        "collection_probe_sha256": manifest.get("probe_sha256"),
        "scorer_changed_since_collection": probe.source_hash() != manifest.get("probe_sha256"),
        "prompts_unchanged": True,
        "rescored_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "conditions": sorted(results),
        "trials": {c: len(v) for c, v in sorted(results.items())},
    }
    with open(os.path.join(out_dir, "rescore.json"), "w", encoding="utf-8") as f:
        json.dump(rescored, f, indent=2, sort_keys=True)
        f.write("\n")
    return {"manifest": manifest, "scores": results, "rescore": rescored}


def verify(probe: ProbeContract, out_dir: str) -> dict:
    """Has the probe changed since the run? A prompt edit invalidates a comparison silently."""
    manifest = json.load(open(os.path.join(out_dir, "manifest.json"), encoding="utf-8"))
    drift = {}
    for condition in manifest.get("conditions", []):
        current = hashlib.sha256(probe.build_prompt(condition).encode()).hexdigest()
        recorded = manifest.get("prompt_sha256", {}).get(condition)
        if recorded and current != recorded:
            drift[condition] = {"recorded": recorded, "current": current}
    # Two different questions, and conflating them was the defect. A prompt edit invalidates the
    # comparison, because the trials no longer answer the same question. A scorer corrected after
    # collection does not: the responses are fixed, and re-scoring them is the point of keeping
    # them. `scores_current` asks the question the evidence class cares about, which is whether the
    # committed scores were produced by the committed scorer.
    rescore_path = os.path.join(out_dir, "rescore.json")
    rescored = json.load(open(rescore_path, encoding="utf-8")) if os.path.exists(rescore_path) else {}
    pinned = rescored.get("scorer_sha256", manifest.get("probe_sha256"))
    return {
        "probe_changed": probe.source_hash() != manifest.get("probe_sha256"),
        "scores_current": probe.source_hash() == pinned,
        "scored_by": pinned,
        "prompt_drift": drift,
        "model": manifest.get("model"),
    }


# --- CLI --------------------------------------------------------------------

def main(argv=None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="dispatch",
        description="Run a probe's conditions against a pinned model and persist the evidence.")
    p.add_argument("--probe", required=True, help="probe module name or path to a probe .py")
    p.add_argument("--condition", action="append", dest="conditions", default=[],
                   help="repeatable; defaults to the probe's CONDITIONS")
    p.add_argument("--trials", type=int, default=10)
    p.add_argument("--model", help="a DATED snapshot; an alias is refused")
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=2000)
    p.add_argument("--out", help="run directory")
    p.add_argument("--dry-run", action="store_true", help="print the call count and stop")
    p.add_argument("--rescore", metavar="RUN_DIR", help="score persisted responses; no model call")
    p.add_argument("--force", action="store_true",
                   help="allow --rescore to replace scores a different scorer produced")
    p.add_argument("--verify", metavar="RUN_DIR", help="report probe or prompt drift since the run")
    args = p.parse_args(argv)

    try:
        probe = load_probe(args.probe)
    except DispatchRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    if args.rescore:
        try:
            scored = rescore(probe, args.rescore, force=args.force)
        except DispatchRefused as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(scored["scores"], indent=2, sort_keys=True))
        return 0

    if args.verify:
        report = verify(probe, args.verify)
        print(json.dumps(report, indent=2, sort_keys=True))
        # A drifted prompt invalidates the run. A scorer corrected after collection does not, so
        # long as the committed scores came from the committed scorer.
        return 1 if report["prompt_drift"] or not report["scores_current"] else 0

    conditions = args.conditions or list(getattr(probe.module, "CONDITIONS", []))
    if not conditions:
        print("refused: no conditions given and the probe declares no CONDITIONS", file=sys.stderr)
        return 2
    if not args.out and not args.dry_run:
        print("refused: pass --out, the run directory the evidence is written to", file=sys.stderr)
        return 2

    try:
        result = dispatch(probe, conditions, trials=args.trials, model=args.model or "",
                          out_dir=args.out or "", temperature=args.temperature,
                          max_tokens=args.max_tokens, dry_run=args.dry_run)
    except DispatchRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))

    # A run in which nothing was measured must not exit 0. Every trial of a two-arm run once failed
    # on an SSL error and then on a mistyped model id, and the dispatcher reported success both
    # times: the errors were in the manifest, the exit code said the evidence was collected. That is
    # the same defect this project fixed in `measure` and in the architecture extractor, sitting in
    # the tool that produces the evidence. The rule is the CLI's: 4 means not measured.
    if result.get("dry_run"):
        return 0
    errors = result.get("errors") or {}
    failed = sum(len(v) for v in errors.values())
    wanted = args.trials * max(1, len(conditions))
    if failed >= wanted:
        print(f"NOT MEASURED: all {failed} trial(s) failed; the run directory holds no evidence.",
              file=sys.stderr)
        for condition, items in errors.items():
            if items:
                print(f"  {condition}: {items[0].get('error')}", file=sys.stderr)
        return 4
    if failed:
        print(f"warning: {failed} of {wanted} trial(s) failed; the arms are no longer balanced and "
              "any rate computed from this run must state the denominator it actually had.",
              file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
