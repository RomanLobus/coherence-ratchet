"""Turn a similarity threshold from an author's guess into a reader's measured choice.

`SIM_THRESHOLD = 0.45` was calibrated against a playground fixture, and the docstring beside it says
so. That is honest and it is not enough: a reader's codebase is not the fixture, and a book that
withholds the number at the point of decision leaves the reader with the author's uncertainty rather
than the author's work.

The procedure here is deliberately three steps with a person in the middle, because the contract
forbids automated architectural judgement and *what counts as the same idea* is exactly that
judgement. The machine samples, a human labels, the machine reports a curve. Then it stops.

    coherence-ratchet calibrate sample <path> --n 120 --seed 7 --out calibration/pairs.jsonl
    # a person edits the `label` field: same | different | unsure
    coherence-ratchet calibrate score calibration/pairs.jsonl

Two design decisions carry the result.

**The sample is stratified across the whole similarity range, including pairs below the current
threshold.** Sampling only above it would make recall unmeasurable — every pair in the sample would
already be a positive prediction — and an unmeasurable recall is how a precision figure flatters a
detector. The bands nearest the decision boundary are over-sampled because that is where the choice
actually lives, and the far bands are still represented so the estimate is not conditioned on them.

**The report recommends nothing.** It prints precision, recall and F1 at every candidate threshold
with the counts behind them, names the two rows a reader usually wants, and then says which value to
pass and refuses to write it anywhere. Precision and recall trade against each other, and the trade
is a judgement about a codebase and a team's review capacity, not a computation.

It also refuses to report at all below a floor of labels, for the same reason the ledger has
`NEEDS_ASSESSMENT`: a number too unstable to act on is worse than an absent one, because it looks
like evidence.
"""

from __future__ import annotations

import json
import os
import random
import sys

from .exitcodes import EXIT_HELD, EXIT_REFUSED
from .metrics import SIM_THRESHOLD, _collect_functions, _jaccard
from .paths import resolve_root

# Boundaries of the strata, low to high. The two bands around the shipped default are where the
# decision lives, so they are sampled hardest; the outer bands are represented so recall and
# precision are both estimable rather than conditioned on the interesting middle.
BANDS = ((0.0, 0.20), (0.20, 0.35), (0.35, 0.45), (0.45, 0.60), (0.60, 0.80), (0.80, 1.01))
BAND_WEIGHTS = (1, 2, 4, 4, 2, 1)

MIN_LABELS = 100
MIN_POSITIVES = 20

LABELS = ("same", "different", "unsure")


def _band(score: float) -> int:
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= score < hi:
            return i
    return len(BANDS) - 1


def _source_index(root: str) -> dict[str, tuple[str, int, str]]:
    """qualname -> (file, first line, source text), for the sampled pairs only.

    A labeller answers "would a change to one require the same change to the other", and that is not
    answerable from two dotted names. The pairs file therefore carries the code. This walks the tree a
    second time rather than widening ``FunctionRecord``, which sits on the measurement path every
    printed number depends on.
    """
    import ast

    from .metrics import MIN_TOKENS, _func_tokens, _iter_py_files, _module_name

    index: dict[str, tuple[str, int, str]] = {}
    for path in _iter_py_files(root):
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            tree = ast.parse(text)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        mod = _module_name(root, path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            if len(_func_tokens(node)) < MIN_TOKENS:
                continue
            end = getattr(node, "end_lineno", node.lineno) or node.lineno
            src = "\n".join(lines[node.lineno - 1:end])
            index[f"{mod}.{node.name}"] = (os.path.relpath(path, root), node.lineno, src)
    return index


def sample(root: str, *, n: int, seed: int) -> list[dict]:
    """A stratified sample of function pairs, across the whole similarity range."""
    resolve_root(root)
    funcs = _collect_functions(root)
    if len(funcs) < 2:
        return []

    buckets: list[list[dict]] = [[] for _ in BANDS]
    for i in range(len(funcs)):
        for j in range(i + 1, len(funcs)):
            score = _jaccard(funcs[i].shingles, funcs[j].shingles)
            buckets[_band(score)].append({
                "a": funcs[i].qualname,
                "b": funcs[j].qualname,
                "jaccard": round(score, 4),
                "label": None,
            })

    rng = random.Random(seed)
    total_weight = sum(w for w, b in zip(BAND_WEIGHTS, buckets) if b)
    out: list[dict] = []
    for weight, bucket in zip(BAND_WEIGHTS, buckets):
        if not bucket:
            continue
        want = max(1, round(n * weight / total_weight)) if total_weight else 0
        rng.shuffle(bucket)
        out.extend(bucket[:want])
    out.sort(key=lambda r: -r["jaccard"])

    # Attach the code, so the pairs file is labellable on its own.
    index = _source_index(root)
    for row in out:
        for side in ("a", "b"):
            where = index.get(row[side])
            if where:
                row[f"{side}_file"], row[f"{side}_line"], row[f"{side}_src"] = where
    return out


def _wilson(successes: int, total: int) -> tuple[float, float]:
    """A 95% interval that behaves at small n, where the normal approximation does not."""
    if total == 0:
        return (0.0, 0.0)
    z = 1.96
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


def curve(labelled: list[dict], thresholds=None) -> list[dict]:
    """Precision, recall and F1 at each candidate threshold, over the labelled pairs only."""
    thresholds = thresholds or [round(0.20 + 0.05 * i, 2) for i in range(13)]
    judged = [r for r in labelled if r.get("label") in ("same", "different")]
    rows = []
    for t in thresholds:
        tp = sum(1 for r in judged if r["jaccard"] >= t and r["label"] == "same")
        fp = sum(1 for r in judged if r["jaccard"] >= t and r["label"] == "different")
        fn = sum(1 for r in judged if r["jaccard"] < t and r["label"] == "same")
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append({
            "threshold": t,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "tp": tp, "fp": fp, "fn": fn,
            "precision_ci": _wilson(tp, tp + fp),
            "recall_ci": _wilson(tp, tp + fn),
        })
    return rows


def render(rows: list[dict], labelled: list[dict]) -> None:
    judged = [r for r in labelled if r.get("label") in ("same", "different")]
    unsure = sum(1 for r in labelled if r.get("label") == "unsure")
    positives = sum(1 for r in judged if r["label"] == "same")

    print(f"  labelled pairs ....... {len(judged)} judged, {unsure} unsure, "
          f"{len(labelled) - len(judged) - unsure} unlabelled")
    print(f"  positives ............ {positives}")
    print()
    print("  threshold  precision           recall              f1     tp  fp  fn")
    for row in rows:
        # 0.80 is the threshold `drift` publishes precision against, so the same gold pairs read at
        # 0.80 are the only like-for-like comparison available between the two tools.
        if row["threshold"] == SIM_THRESHOLD:
            marker = "  <- shipped default"
        elif abs(row["threshold"] - 0.80) < 1e-9:
            marker = "  <- drift's published threshold"
        else:
            marker = ""
        print(f"     {row['threshold']:.2f}     {row['precision']:.3f} "
              f"[{row['precision_ci'][0]:.2f},{row['precision_ci'][1]:.2f}]   "
              f"{row['recall']:.3f} [{row['recall_ci'][0]:.2f},{row['recall_ci'][1]:.2f}]   "
              f"{row['f1']:.3f}  {row['tp']:3d} {row['fp']:3d} {row['fn']:3d}{marker}")
    print()

    best_f1 = max(rows, key=lambda r: r["f1"])
    conservative = [r for r in rows if r["precision"] >= 0.90 and r["tp"]]
    print(f"  highest F1 ........... {best_f1['threshold']:.2f} "
          f"(precision {best_f1['precision']:.3f}, recall {best_f1['recall']:.3f})")
    if conservative:
        pick = min(conservative, key=lambda r: r["threshold"])
        print(f"  precision >= 0.90 at . {pick['threshold']:.2f} "
              f"(recall {pick['recall']:.3f})")
    else:
        print("  precision >= 0.90 .... not reached at any threshold in this sample")
    print()
    print("  No threshold is recommended. Precision and recall trade against each other, and the")
    print("  trade is a judgement about this codebase and the review attention available for it,")
    print("  not a computation. Choose one and pass it explicitly:")
    print()
    print("      coherence-ratchet measure <path> --similarity <value>")
    print()
    print("  Record the value and the reason in the region's decision record, the way a ceiling is")
    print("  recorded. A threshold nobody signed is the same problem as a candidate nobody ratified.")


def load_labels(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# --- CLI --------------------------------------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser("calibrate",
                       help="sample function pairs for labelling, and report the threshold curve")
    p.add_argument("action", choices=["sample", "score"])
    p.add_argument("target", help="source root (sample) or labelled JSONL (score)")
    p.add_argument("--n", type=int, default=120, help="approximate sample size")
    p.add_argument("--seed", type=int, default=7, help="sampling seed, recorded so a run repeats")
    p.add_argument("--out", help="where to write the sample")
    p.add_argument("--min-labels", type=int, default=MIN_LABELS)
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    if args.action == "sample":
        rows = sample(args.target, n=args.n, seed=args.seed)
        if not rows:
            print("refused: fewer than two comparable functions in this tree", file=sys.stderr)
            return EXIT_REFUSED
        out = args.out or "calibration/pairs.jsonl"
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True) + "\n")
        print(f"{len(rows)} pairs written to {out} (seed {args.seed})")
        print("Set each `label` to same, different, or unsure. `unsure` is a recorded outcome, not a")
        print("failure to decide: forcing it into a binary is how a ground truth stops being one.")
        print("See calibration/LABELLING.md for the rubric.")
        return EXIT_HELD

    labelled = load_labels(args.target)
    judged = [r for r in labelled if r.get("label") in ("same", "different")]
    positives = sum(1 for r in judged if r["label"] == "same")

    if len(judged) < args.min_labels or positives < MIN_POSITIVES:
        print(f"refused: {len(judged)} labelled pairs and {positives} positives; "
              f"this reports nothing below {args.min_labels} labels and {MIN_POSITIVES} positives. "
              f"A number too unstable to act on is worse than an absent one, because it looks like "
              f"evidence.", file=sys.stderr)
        return EXIT_REFUSED

    rows = curve(labelled)
    if args.json:
        print(json.dumps({"curve": rows, "judged": len(judged), "positives": positives},
                         indent=2, sort_keys=True))
    else:
        render(rows, labelled)
    return EXIT_HELD
