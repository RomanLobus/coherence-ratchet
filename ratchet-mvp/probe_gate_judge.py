"""Probe: the subjective consolidation judge, on the eight `requests` clusters.

This is the experiment that opens Chapter 12 and is summarised in the front matter: a model asked to
judge which duplicate clusters deserve consolidation agreed with itself almost perfectly while a
second model family, equally unanimous and equally confident, returned the opposite verdict on the
same cluster. The earlier framing, "unanimously wrong on the clearest candidate in the set", was
retired on 22 August 2026: see the two limits on the oracle recorded above CLUSTERS.

It is a replication rather than a new experiment, and it is the only one of the four Tier 1 records
that could be. `semantic-gate-on-requests.md` enumerates all eight clusters, their members, and the
hand-assigned ground truth, and the target library is public, so the inputs that produced the printed
figure still exist. The reconstructability audit in `EXPERIMENT-INDEX.md` records why the other three
could not be rebuilt.

Pre-registered prediction, fixed before the first dispatch (see the protocol in `EXPERIMENT-INDEX.md`):

    mean pairwise trial agreement   0.97
    verdict on C3 (hash helpers)    SANCTIONED, 5 trials of 5, against a CONSOLIDATE ground truth
    CONSOLIDATE verdicts overall    none, on any cluster

A run that reproduces those promotes the entry to `REPRODUCIBLE_AS_RECORDED`. A run that contradicts
them goes to the set-aside register at Appendix C.9 with both figures and the date. Neither outcome is
suppressed, and the trial count is not adjusted after the fact.

Scoring is deterministic and makes no model call: it parses the forced schema out of each response and
counts. The judge's opinion is the datum; nothing downstream is allowed to interpret it.
"""

from __future__ import annotations

import itertools
import json
import os
import re

# --- the eight clusters, verbatim from the record ---------------------------
#
# Members are the qualified names the detector grouped. GROUND_TRUTH is the hand-assigned label with
# the confidence the record states; only the label is scored, and the confidence is carried so that a
# reader can see which two anchors were "certain" when the judge missed one of them.
#
# Two limits on this oracle, recorded 22 August 2026, because claims were being drawn from it that it
# cannot carry.
#
# 1. The labels below were assigned by one person with no written decision rule. `certainty` and
#    `gloss` are annotations, not criteria: nothing here maps a property of the code to a label, so
#    "the judge was wrong" means "the judge disagreed with one unnamed rater". The repo's own standard
#    for a labelling task is `calibration/LABELLING.md` ("Two labellers are better than one, and the
#    disagreement rate is worth reporting when there are two"), and this fixture does not meet it. A
#    corrected re-run with a second rater and a written rubric is logged in EXPERIMENT-INDEX.md.
#
# 2. The prompt asks whether a group "should be consolidated into one implementation". It does not
#    mention callers, public entry points, or backwards compatibility, so a CONSOLIDATE verdict
#    carries no position on whether the public API should change. On C1 every one of the five haiku
#    trials proposed a factory or a decorator, which preserves all four verb names. Any claim that
#    acting on the verdict would break callers is therefore an inference about a remedy the model was
#    never asked for, and the manuscript no longer makes it. Splitting the question in two, one for
#    the implementation and one for the interface, is what the re-run is for.

CLUSTERS = {
    "C1": {
        "members": ["requests.api:get", "requests.api:patch",
                    "requests.api:post", "requests.api:put"],
        "ground_truth": "SANCTIONED",
        "certainty": "certain",
        "gloss": "the public HTTP verb helpers, each delegating to request()",
    },
    "C2": {
        "members": ["requests.sessions:Session.get", "requests.sessions:Session.post",
                    "requests.api:get", "requests.api:post"],
        "ground_truth": "SANCTIONED",
        "certainty": "certain",
        "gloss": "session methods mirroring the module-level verb helpers",
    },
    "C3": {
        "members": ["requests.auth:md5_utf8", "requests.auth:sha_utf8",
                    "requests.auth:sha256_utf8", "requests.auth:sha512_utf8"],
        "ground_truth": "CONSOLIDATE",
        "certainty": "certain",
        "gloss": "four hash helpers differing only by the digest primitive",
    },
    "C4": {
        "members": ["requests.cookies:RequestsCookieJar._find",
                    "requests.cookies:RequestsCookieJar._find_no_duplicates"],
        "ground_truth": "SANCTIONED",
        "certainty": "ambiguous",
        "gloss": "two cookie lookups with different duplicate semantics",
    },
    "C5": {
        "members": ["requests.cookies:RequestsCookieJar.iterkeys",
                    "requests.cookies:RequestsCookieJar.itervalues"],
        "ground_truth": "SANCTIONED",
        "certainty": "likely",
        "gloss": "dict-interface mirrors over the same jar",
    },
    "C6": {
        "members": ["requests.cookies:RequestsCookieJar.list_domains",
                    "requests.cookies:RequestsCookieJar.list_paths"],
        "ground_truth": "CONSOLIDATE",
        "certainty": "ambiguous",
        "gloss": "per-attribute accessors over the same iteration",
    },
    "C7": {
        "members": ["requests.models:Response.is_redirect",
                    "requests.models:Response.is_permanent_redirect"],
        "ground_truth": "SANCTIONED",
        "certainty": "likely",
        "gloss": "two status properties over the same header check",
    },
    "C8": {
        "members": ["requests.utils:from_key_val_list", "requests.utils:to_key_val_list"],
        "ground_truth": "SANCTIONED",
        "certainty": "ambiguous",
        "gloss": "a conversion pair in opposite directions",
    },
}

CONDITIONS = tuple(CLUSTERS)

VERDICTS = ("CONSOLIDATE", "SANCTIONED", "UNSURE")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "_fixtures", "gatejudge")


def _member_source(member: str) -> str:
    """The committed snippet for one member.

    The bodies are committed beside this probe rather than read from an installed `requests`, because
    the judge must see the same text on every run. A pip-installed library moves; a committed snippet
    does not, and the snippet's provenance is recorded in the fixture's own README.
    """
    fname = member.replace(":", "__").replace(".", "_") + ".py"
    path = os.path.join(SRC, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no committed snippet for {member} at {path}; the probe refuses to send a "
            f"reconstruction it cannot pin"
        )
    with open(path, encoding="utf-8") as f:
        return f.read()


# --- the prompt -------------------------------------------------------------
#
# The framing is the subjective one the record describes as the first of three: judge whether the
# cluster should consolidate. The two later framings (conservative auto-clear, catalogue matching)
# are different experiments and are not this probe's subject.

_SCHEMA = (
    "Answer with JSON and nothing else, in exactly this shape:\n"
    '{"verdict": "CONSOLIDATE" | "SANCTIONED" | "UNSURE", '
    '"reason": "<one sentence>", "confidence": "low" | "medium" | "high"}'
)


def build_prompt(condition: str) -> str:
    cluster = CLUSTERS[condition]
    bodies = "\n\n".join(
        f"# {m}\n{_member_source(m)}".rstrip() for m in cluster["members"]
    )
    return (
        "These functions were grouped as near-duplicates by a structural detector in a Python "
        "library.\n\n"
        f"{bodies}\n\n"
        "Judge whether this group should be consolidated into one implementation, or whether the "
        "repetition is sanctioned and should be left alone.\n\n"
        f"{_SCHEMA}"
    )


# --- scoring ----------------------------------------------------------------

_JSON = re.compile(r"\{.*\}", re.S)


def score_code(text: str, *_names) -> dict:
    """Parse one response. Deterministic, and it makes no model call.

    A response that does not carry a parseable verdict scores as `UNPARSEABLE` rather than being
    dropped, because a judge that cannot answer in the schema it was given is a result about the
    judge and silently discarding it would flatter the agreement figure.
    """
    match = _JSON.search(text or "")
    if not match:
        return {"verdict": "UNPARSEABLE", "confidence": None, "parsed": False}
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"verdict": "UNPARSEABLE", "confidence": None, "parsed": False}
    verdict = str(payload.get("verdict", "")).strip().upper()
    if verdict not in VERDICTS:
        return {"verdict": "UNPARSEABLE", "confidence": None, "parsed": False}
    return {
        "verdict": verdict,
        "confidence": payload.get("confidence"),
        "reason": payload.get("reason"),
        "parsed": True,
    }


def _agreement(verdicts) -> float | None:
    """Majority fraction for one cluster: how many trials landed on the modal verdict.

    This is the metric the record's 0.97 is computed on, and getting it right matters more than it
    looks. The record's own table is seven clusters at 5/5 and one at 4/5. Under majority fraction
    that averages (7 x 1.00 + 0.80) / 8 = 0.975, which is the printed 0.97. Under mean *pairwise*
    agreement the same data averages 0.95, because a 4/1 split scores 0.6 pairwise and 0.8 by
    majority. Pre-registering 0.97 and then scoring pairwise would make a faithful replication look
    like a contradiction, which is the class of defect this whole programme exists to catch.

    Reported as None below two trials, because a single trial trivially agrees with itself.
    """
    if len(verdicts) < 2:
        return None
    return verdicts.count(max(set(verdicts), key=verdicts.count)) / len(verdicts)


def _pairwise(verdicts) -> float | None:
    """Mean pairwise agreement, reported beside the majority fraction for contrast only."""
    pairs = list(itertools.combinations(verdicts, 2))
    if not pairs:
        return None
    return sum(1 for a, b in pairs if a == b) / len(pairs)


def tally(results_dir: str) -> None:
    """Print the three pre-registered figures beside what this run produced."""
    per_cluster = {}
    for cid in CLUSTERS:
        path = os.path.join(results_dir, cid)
        if not os.path.isdir(path):
            continue
        verdicts = []
        for name in sorted(os.listdir(path)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(path, name), encoding="utf-8") as f:
                verdicts.append(json.load(f).get("verdict"))
        if verdicts:
            per_cluster[cid] = verdicts

    if not per_cluster:
        print("no scored trials found; nothing to tally")
        return

    agreements = [a for a in (_agreement(v) for v in per_cluster.values()) if a is not None]
    mean_agreement = sum(agreements) / len(agreements) if agreements else None

    print("cluster  ground truth   majority      trials  majority-frac  pairwise")
    for cid, verdicts in per_cluster.items():
        majority = max(set(verdicts), key=verdicts.count)
        agree, pair = _agreement(verdicts), _pairwise(verdicts)
        hit = "ok " if majority == CLUSTERS[cid]["ground_truth"] else "MISS"
        print(f"  {cid:5} {CLUSTERS[cid]['ground_truth']:13} {majority:13} "
              f"{verdicts.count(majority)}/{len(verdicts):<4}  "
              f"{'n/a' if agree is None else f'{agree:.2f}':13}  "
              f"{'n/a' if pair is None else f'{pair:.2f}'}  {hit}")

    consolidates = sum(v.count("CONSOLIDATE") for v in per_cluster.values())
    c3 = per_cluster.get("C3", [])

    print()
    print("pre-registered                          this run")
    print(f"  mean trial agreement   0.97          "
          f"{'n/a' if mean_agreement is None else f'{mean_agreement:.2f}'}")
    print(f"  C3 verdict             SANCTIONED    "
          f"{max(set(c3), key=c3.count) if c3 else 'n/a'} "
          f"({c3.count('SANCTIONED')}/{len(c3)} sanctioned)" if c3 else "  C3 verdict  n/a")
    print(f"  CONSOLIDATE verdicts   0             {consolidates}")
    print()
    print("A figure that differs from the pre-registration goes to Appendix C.9 with both numbers")
    print("and the date. It does not get re-run until it agrees.")
