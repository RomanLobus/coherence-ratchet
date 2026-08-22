"""Regression pins for the 2026-08 editorial review's mechanism findings.

Each test corresponds to a defect the review found in the shipped tool, and exists so the defect
cannot return. Deterministic, offline, stdlib only.
"""

import datetime
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import report
from coherence_ratchet.ratchet import (
    Budget, BudgetExists, assess_exposure, init_budget, numerators_for, tighten,
)


class FakeSnap:
    """A snapshot stand-in: the ratchet only ever calls .to_dict()."""

    def __init__(self, d):
        self._d = d

    def to_dict(self):
        return dict(self._d)


def _budgets_file(payload):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "budgets.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    return path


# --- the pawl: a falling ratio is not necessarily an improvement -------------------------------

def test_tighten_declines_when_numerator_grew():
    """The review's reproduction: cyclic modules double, the ratio falls, the ceiling must hold.

    Printing the raw counts beside the ratio is disclosure, not enforcement. This is enforcement.
    """
    budget = Budget(ceilings={"cycle_ratio": 0.5}, numerators={"cycle_ratio": 2})
    grown = FakeSnap({"cycle_ratio": 0.4, "cyclic_modules": 4, "n_modules": 10})

    tightened, declined = tighten(budget, grown)

    assert tightened.ceilings["cycle_ratio"] == 0.5, "the ceiling must not follow a diluted ratio"
    assert "cycle_ratio" in declined
    assert "cyclic" in declined["cycle_ratio"]
    assert tightened.numerators["cycle_ratio"] == 2, "the remembered numerator must not drift up"


def test_tighten_lowers_when_numerator_also_fell():
    """The positive case. A guard that never tightens is a guard somebody deletes."""
    budget = Budget(ceilings={"cycle_ratio": 0.5}, numerators={"cycle_ratio": 2})
    improved = FakeSnap({"cycle_ratio": 0.25, "cyclic_modules": 1, "n_modules": 4})

    tightened, declined = tighten(budget, improved)

    assert declined == {}
    assert tightened.ceilings["cycle_ratio"] == 0.25
    assert tightened.numerators["cycle_ratio"] == 1


def test_tighten_declines_when_no_numerator_was_recorded():
    """A legacy budgets file cannot be verified, so the pawl holds rather than guessing."""
    budget = Budget(ceilings={"cycle_ratio": 0.5})
    improved = FakeSnap({"cycle_ratio": 0.25, "cyclic_modules": 1, "n_modules": 4})

    tightened, declined = tighten(budget, improved)

    assert tightened.ceilings["cycle_ratio"] == 0.5
    assert "cycle_ratio" in declined


def test_tighten_still_lowers_a_count_metric():
    """Counts have no denominator to dilute, so they tighten unconditionally."""
    budget = Budget(ceilings={"redundant_clusters": 4})
    tightened, declined = tighten(budget, FakeSnap({"redundant_clusters": 2}))

    assert tightened.ceilings["redundant_clusters"] == 2
    assert declined == {}


# --- budgets provenance: the one artefact CI enforces must not be authorless -------------------

def test_budget_load_accepts_legacy_flat_ceilings():
    """A 0.2.0 budgets file must still check. An early adopter's CI must not break."""
    path = _budgets_file({"ceilings": {"cycle_ratio": 0.5}})
    budget = Budget.load(path)

    assert budget.ceilings == {"cycle_ratio": 0.5}
    assert budget.numerators == {}
    assert budget.provenance == {}


def test_budget_roundtrips_provenance_and_numerators():
    budget = Budget(
        ceilings={"cycle_ratio": 0.5},
        numerators={"cycle_ratio": 2},
        provenance={"author": "pricing architecture owner", "reason": "regional baseline",
                    "set_at": "2026-08-05"},
    )
    path = os.path.join(tempfile.mkdtemp(), "b.json")
    budget.save(path)
    again = Budget.load(path)

    assert again.ceilings == budget.ceilings
    assert again.numerators == budget.numerators
    assert again.provenance["author"] == "pricing architecture owner"


def test_init_refuses_to_overwrite_existing_budgets():
    """Re-baselining is how worsening enters unsigned, so it cannot be the default."""
    path = _budgets_file({"ceilings": {"cycle_ratio": 0.9}})
    before = open(path, encoding="utf-8").read()

    try:
        init_budget(os.path.join(ROOT, "playground", "_states", "05-checkout-clean",
                                 "checkout_pricing"), path, author="someone")
    except BudgetExists:
        pass
    else:  # pragma: no cover - the guard is the point of the test
        raise AssertionError("init must refuse an existing budgets file without force")

    assert open(path, encoding="utf-8").read() == before, "the file must be byte-unchanged"


def test_init_force_records_prior_ceilings_and_author():
    path = _budgets_file({"ceilings": {"cycle_ratio": 0.9}})
    budget = init_budget(
        os.path.join(ROOT, "playground", "_states", "05-checkout-clean", "checkout_pricing"),
        path, author="pricing architecture owner", reason="post-consolidation re-baseline",
        set_at="2026-08-05", force=True,
    )

    assert budget.provenance["prior"] == {"cycle_ratio": 0.9}
    assert budget.provenance["author"] == "pricing architecture owner"
    assert budget.provenance["reason"] == "post-consolidation re-baseline"


def test_numerators_for_covers_every_ratio_it_can():
    ceilings = {"cycle_ratio": 0.5, "duplication_ratio": 0.2, "redundant_clusters": 2}
    d = {"cyclic_modules": 2, "n_modules": 4, "redundant_functions": 5, "total_functions": 25}

    assert numerators_for(ceilings, d) == {"cycle_ratio": 2, "duplication_ratio": 5}


# --- the exposure tier rule: breadth must not supply two highs ---------------------------------

WORKED_SEAM = {
    "volatility": "medium",
    "coordination_span": "high",
    "criticality": "high",
    "discoverability": "medium",
    "blast_radius": "high",
}


def test_exposure_worked_seam_still_high():
    """The dimension set printed in chapter 6 and appendix B.4. Protects three printed blocks."""
    assert assess_exposure(WORKED_SEAM) == "HIGH"


def test_exposure_worked_receipt_formatter_still_low():
    assert assess_exposure(dict.fromkeys(
        ("volatility", "coordination_span", "criticality", "discoverability", "blast_radius"),
        "low")) == "LOW"


def test_exposure_breadth_plus_one_unrelated_high_is_not_high():
    """Many consumers reads high on both span and blast radius, so breadth alone supplied two of
    the three highs the count clause needed. A stable, low-criticality region must not reach HIGH.
    """
    assert assess_exposure({
        "volatility": "low",
        "coordination_span": "high",
        "criticality": "low",
        "discoverability": "high",
        "blast_radius": "high",
    }) == "MODERATE"


def test_exposure_breadth_with_volatility_is_high():
    """Consequence can arrive through volatility as well as criticality."""
    assert assess_exposure({
        "volatility": "high",
        "coordination_span": "high",
        "criticality": "low",
        "discoverability": "low",
        "blast_radius": "high",
    }) == "HIGH"


def test_exposure_incomplete_assessment_needs_assessment():
    assert assess_exposure({
        "volatility": "low", "coordination_span": "low", "criticality": "low",
        "discoverability": "low",
    }) == "NEEDS_ASSESSMENT"


# --- the ledger's review date must actually be read -------------------------------------------

def _ledger(entries):
    path = os.path.join(tempfile.mkdtemp(), "led.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


BOOK_ENTRIES = [
    {  # chapter 6 and appendix B.4's worked seam
        "region": "checkout-pricing seam", "owner": "pricing team", "status": "accepted",
        "when": "2026-08-01", "repayment_trigger": "before contract v2 becomes the default",
        "review_date": "2026-10-01", "exposure_tier": "HIGH",
    },
    {  # chapter 6's receipt formatter
        "region": "receipt formatting", "owner": "receipt team", "status": "accepted",
        "when": "2026-08-01", "repayment_trigger": "next touch of either template",
        "review_date": "2027-02-01", "exposure_tier": "LOW",
    },
]


def test_book_printed_entries_become_overdue_after_their_review_date():
    """Both printed entries carry event-worded triggers with no date, so reading the trigger text
    alone left the book's own worked examples permanently unchaseable.
    """
    r = report.report(_ledger(BOOK_ENTRIES), today=datetime.date(2027, 3, 1))
    regions = {o["region"] for o in r["overdue"]}

    assert regions == {"checkout-pricing seam", "receipt formatting"}


def test_review_date_not_yet_passed_is_not_overdue():
    r = report.report(_ledger(BOOK_ENTRIES), today=datetime.date(2026, 9, 1))
    assert r["overdue"] == []


def test_chapter6_printed_report_is_read_at_the_worked_examples_own_clock():
    """Chapter 6 prints `overdue ... none` for appendix B.4's entry, which was accepted on
    2026-08-03 and carries a review date of 2026-10-01. Read against the reader's clock that block
    turned false on 1 October 2026; read at `--as-of 2026-08-03` it stays true for every reader.
    Guards the invariant the printed block now depends on: acceptance date before review date, and
    a zero-day held line at the moment of acceptance.
    """
    entry = dict(BOOK_ENTRIES[0], when="2026-08-03")
    r = report.report(_ledger([entry]), today=datetime.date(2026, 8, 3))

    assert r["overdue"] == []
    assert r["held_days"] == 0
    assert r["last_accepted"] == "2026-08-03"


def test_overdue_section_is_labelled_by_the_date_it_actually_tests():
    """The heading named the repayment trigger while the code reads the review date first, so an
    entry overdue on its review date reported under the wrong noun.
    """
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        report.render(report.report(_ledger(BOOK_ENTRIES), today=datetime.date(2027, 3, 1)))
    out = buf.getvalue()

    assert "review date passed" in out
    assert "repayment trigger date passed" not in out


def test_overdue_still_falls_back_to_a_trigger_date():
    """The prior behaviour survives as a fallback for an entry with no review date."""
    r = report.report(_ledger([{
        "region": "legacy", "owner": "someone", "status": "accepted",
        "repayment_trigger": "by 2026-06-01",
    }]), today=datetime.date(2026, 7, 1))

    assert [o["region"] for o in r["overdue"]] == ["legacy"]


# --- ratified intent: the durable artefact must be as accountable as the deferral --------------

def _ratify_fixture():
    from coherence_ratchet import selfmodel as sm
    state = os.path.join(ROOT, "playground", "_states", "06-checkout-cycle", "checkout_pricing")
    model = sm.derive(state)
    candidate = next(c for c in model["candidates"] if c["kind"] == "reuse_helper")
    return sm, model, candidate


def test_ratification_records_a_review_date():
    """Intent instructs agents indefinitely, so it carries the same re-examination commitment the
    reversible ledger entry already required."""
    sm, model, candidate = _ratify_fixture()
    intent = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                       rationale="one canonical conversion", scope="checkout-pricing seam",
                       review_date="2027-08-01", approved_at="2026-08-05")

    assert intent["ratifications"][-1]["review_date"] == "2027-08-01"
    assert intent["ratifications"][-1]["revision"] == 1


def test_ratify_requires_an_explicit_scope():
    """A scope defaulting to the whole tree is the over-reach the method exists to prevent."""
    sm, model, candidate = _ratify_fixture()
    for bad_scope in ("", "   "):
        try:
            sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                      rationale="r", scope=bad_scope)
        except ValueError as exc:
            assert "scope is required" in str(exc)
        else:  # pragma: no cover
            raise AssertionError(f"ratify must refuse scope {bad_scope!r}")


def test_reratification_supersedes_and_retains_the_prior_record():
    """Intent that changes without a trace is unauditable, which is the opposite of the claim."""
    sm, model, candidate = _ratify_fixture()
    first = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                      rationale="first call", scope="checkout-pricing seam",
                      approved_at="2026-08-05")
    second = sm.ratify(model, first, candidate["id"], approved_by="architecture owner",
                       rationale="revised after the receipt team objected",
                       scope="checkout-pricing seam", approved_at="2026-11-01")

    records = second["ratifications"]
    assert len(records) == 2, "the superseded record must be retained, not dropped"
    superseded, current = records[0], records[-1]
    assert superseded["superseded_by"] == current["id"]
    assert superseded["superseded_at"] == "2026-11-01"
    assert current.get("superseded_by") is None
    assert current["revision"] == 2


def test_query_does_not_render_a_superseded_ratification_as_live():
    """Both the grounding pack and `selfmodel query` print the same [RATIFIED] imperative label.
    The pack was filtered when this defect was first found; query was not, so a question about the
    seam answered with the superseded revision beside the current one, indistinguishable. Retaining
    history in the file is the point; rendering it as a live instruction is the defect.
    """
    from coherence_ratchet import query as q

    sm, model, candidate = _ratify_fixture()
    first = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                      rationale="first call", scope="checkout-pricing seam",
                      approved_at="2026-08-05")
    second = sm.ratify(model, first, candidate["id"], approved_by="architecture owner",
                       rationale="revised", scope="checkout-pricing seam",
                       approved_at="2026-11-01")

    assert len(second["ratifications"]) == 2, "history must still be retained in the file"

    answer = q.answer(model, "where should total live?", intent=second)

    assert len(answer["ratified"]) == 1
    assert answer["ratified"][0]["approved_by"] == "architecture owner"
    assert all(not r.get("superseded_by") for r in answer["ratified"])


def test_ratification_records_advisers_objections_and_buy_in():
    sm, model, candidate = _ratify_fixture()
    intent = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                       rationale="r", scope="checkout-pricing seam",
                       advisers=["receipt team", "revenue reporting"],
                       objections=["revenue reporting prefers half-even"], buy_in="consent")
    record = intent["ratifications"][-1]

    assert record["advisers"] == ["receipt team", "revenue reporting"]
    assert record["objections"] == ["revenue reporting prefers half-even"]
    assert record["buy_in"] == "consent"


def test_solo_ratification_stays_terse():
    """The new fields appear only when supplied, so an uncontested decision is not padded."""
    sm, model, candidate = _ratify_fixture()
    intent = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="steward",
                       rationale="r", scope="checkout-pricing seam")
    record = intent["ratifications"][-1]

    for absent in ("advisers", "objections", "buy_in", "superseded_by"):
        assert absent not in record


# --- the gate: an unavailable judge is not a finding -------------------------------------------

def test_judge_request_body_pins_temperature():
    """The quorum only means anything if trials can differ, so sampling is a design precondition
    rather than an API default to inherit. Stubs the transport; never reaches the network."""
    import urllib.request
    from coherence_ratchet import gate

    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"content": [{"text": "{\\"match\\": \\"NONE\\"}"}]}'

    def fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode())
        return FakeResp()

    real_open, real_key = urllib.request.urlopen, os.environ.get("ANTHROPIC_API_KEY")
    urllib.request.urlopen = fake_urlopen
    os.environ["ANTHROPIC_API_KEY"] = "test-key-not-used"
    try:
        gate._anthropic_judge("prompt")
    finally:
        urllib.request.urlopen = real_open
        if real_key is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = real_key

    assert "temperature" in captured["body"], "the sampling temperature must be pinned in the request"
    assert captured["body"]["temperature"] == gate.DEFAULT_JUDGE_TEMPERATURE
    assert captured["body"]["model"] == gate.judge_model()


def test_all_trials_failed_reads_as_unavailable_not_uncatalogued():
    """A retired model or an expired key must not be reported as a genuine divergence finding."""
    from coherence_ratchet import gate

    def broken_judge(prompt):
        raise RuntimeError("model retired")

    verdict = gate._match_cluster(
        ["a.f", "b.f"], "total", [{"name": "p", "description": "d"}], {},
        broken_judge, trials=3, quorum=2,
    )

    assert verdict["disposition"] == "SURFACE", "the conservative disposition still holds"
    assert verdict["errors"] == 3
    assert "judge unavailable" in verdict["why"]
    assert "uncatalogued divergence" not in verdict["why"]


def test_partial_trial_failures_still_surface_conservatively():
    """Zero-false-clear is preserved: a failed trial can never help reach quorum."""
    from coherence_ratchet import gate

    calls = {"n": 0}

    def flaky_judge(prompt):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("rate limited")
        return '{"match": "p", "why": "matches"}'

    verdict = gate._match_cluster(
        ["a.f", "b.f"], "total", [{"name": "p", "description": "d"}], {},
        flaky_judge, trials=3, quorum=3,
    )

    assert verdict["disposition"] == "SURFACE"
    assert verdict["errors"] == 1
    assert "1/3 trials failed" in verdict["why"]


def test_catalogue_line_carries_provenance_when_present():
    """The catalogue authorises clearing, so an authorised pattern must not look like an anonymous one."""
    from coherence_ratchet import gate

    anonymous = gate._catalogue_line({"name": "p", "description": "d"})
    authorised = gate._catalogue_line({
        "name": "p", "description": "d", "approved_by": "pricing owner",
        "approved_at": "2026-08-05", "scope": "checkout-pricing seam",
        "ratified_id": "ratified:abc123",
    })

    assert anonymous == "- p: d"
    assert "approved by pricing owner" in authorised
    assert "ratification ratified:abc123" in authorised


# --- the ledger's remaining routes ------------------------------------------------------------

def test_close_appends_a_closing_record_and_report_drops_it():
    """The ledger stays append-only, so closing supersedes rather than edits."""
    from coherence_ratchet.ratchet import close_ledger_entry

    path = _ledger([{
        "region": "receipt formatting", "owner": "receipt team", "status": "accepted",
        "when": "2026-08-01", "review_date": "2027-02-01", "exposure_tier": "LOW",
    }])
    closed = close_ledger_entry(path, region="receipt formatting", when="2026-09-01",
                                by="receipt team", reason="repaid: one shared formatter")

    assert closed == 1
    lines = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    assert len(lines) == 2, "the original entry must remain in the file"
    assert lines[-1]["status"] == "closed"
    assert lines[-1]["closed_reason"].startswith("repaid")
    assert lines[-1]["closes"] == "2026-08-01"

    r = report.report(path, today=datetime.date(2027, 3, 1))
    assert r["total"] == 0, "a closed entry leaves the open register"


def test_close_is_a_no_op_for_an_unknown_region():
    from coherence_ratchet.ratchet import close_ledger_entry

    path = _ledger(BOOK_ENTRIES)
    assert close_ledger_entry(path, region="nowhere", when="2026-09-01", by="x", reason="y") == 0


def test_report_names_a_malformed_ledger_line_instead_of_crashing():
    """A pretty-printed entry yields lines that parse as fragments; a bare string used to crash."""
    path = os.path.join(tempfile.mkdtemp(), "led.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write('  "region": "checkout",\n')
        f.write('  "status": "accepted"\n')
        f.write('}\n')

    r = report.report(path, today=datetime.date(2026, 9, 1))
    assert r["total"] == 0, "unparseable lines are skipped, not fatal"


# --- the grown fixture: the defect demonstrated through the real tool -------------------------

GROWN = os.path.join(ROOT, "playground", "_states", "07-checkout-cycle-grown", "checkout_pricing")
CYCLE = os.path.join(ROOT, "playground", "_states", "06-checkout-cycle", "checkout_pricing")


def test_grown_fixture_dilutes_the_ratio_and_isolates_the_effect():
    """The state exists to make the pawl's failure mode visible in print, so it must move the cycle
    ratio down while worsening the cycle count, and must trip nothing else — otherwise the breach
    path fires first and the demonstration never reaches the tighten step."""
    from coherence_ratchet.signals import measure_all

    base = measure_all(CYCLE).to_dict()
    grown = measure_all(GROWN).to_dict()

    assert grown["cycle_ratio"] < base["cycle_ratio"], "the ratio must fall"
    assert grown["cyclic_modules"] > base["cyclic_modules"], "the cycle count must rise"
    assert (grown["cycle_ratio"], grown["cyclic_modules"], grown["n_modules"]) == (0.4, 4, 10)
    for quiet in ("connascence_shared", "redundant_clusters", "redundant_functions",
                  "duplication_ratio"):
        assert grown[quiet] <= base[quiet], f"{quiet} must not trip in the grown state"


def test_pawl_holds_both_diluted_ceilings_on_the_real_fixture():
    """End to end through the real signals, not a stub.

    Both watched ratios fall in the grown state and neither is an improvement: the cyclic count rises
    2 -> 4, and the redundant-function count holds flat at 5 while the function total grows. Under the
    rule the book states — the ratio improves and its raw count improves with it — both are refused.
    The selective half of the behaviour is pinned by `test_tighten_lowers_when_numerator_also_fell`.
    """
    from coherence_ratchet.signals import measure_all

    budget = Budget.from_snapshot(measure_all(CYCLE), author="pricing architecture owner")
    tightened, declined = tighten(budget, measure_all(GROWN))

    assert tightened.ceilings["cycle_ratio"] == 0.5, "the diluted ratio must not become the floor"
    assert "cycle_ratio" in declined and "cyclic rose 2 -> 4" in declined["cycle_ratio"]
    assert tightened.ceilings["duplication_ratio"] == budget.ceilings["duplication_ratio"]
    assert "duplication_ratio" in declined and "held at 5" in declined["duplication_ratio"], (
        "a flat count with a grown denominator is dilution and must also be refused"
    )


# --- regressions introduced by the supersession change, caught in re-review ---------------------

def test_superseded_ratification_never_reaches_the_grounding_pack():
    """A [RATIFIED] line is an imperative to an agent. Retaining history must not mean instructing
    against current intent — the whole authority rule depends on this."""
    sm, model, candidate = _ratify_fixture()
    intent = sm.ratify(model, sm.empty_intent(model), candidate["id"], approved_by="owner",
                       rationale="first", scope="seam", approved_at="2026-08-01")
    intent = sm.ratify(model, intent, candidate["id"], approved_by="owner",
                       rationale="revised", scope="seam", approved_at="2026-11-01")

    assert len(intent["ratifications"]) == 2, "history must be retained in the file"
    assert sm.context_pack(model, intent).count("[RATIFIED]") == 1, (
        "only the live ratification may issue an instruction"
    )


def test_each_revision_gets_a_distinct_id_and_no_self_supersession():
    """A colliding id made the supersession link point at itself, so the retained history was
    unreadable. Revision 1 keeps the plain hash so existing files and the printed record stay valid."""
    sm, model, candidate = _ratify_fixture()
    intent = sm.empty_intent(model)
    for n, when in enumerate(("2026-08-01", "2026-11-01", "2027-01-01"), start=1):
        intent = sm.ratify(model, intent, candidate["id"], approved_by="owner",
                           rationale=f"revision {n}", scope="seam", approved_at=when)

    records = intent["ratifications"]
    ids = [r["id"] for r in records]
    assert len(set(ids)) == len(ids), "each revision needs its own identifier"
    assert [r["revision"] for r in records] == [1, 2, 3]
    for record in records:
        assert record.get("superseded_by") != record["id"], "a record cannot supersede itself"
    assert records[-1].get("superseded_by") is None, "the newest record is live"
    assert records[0]["id"] == "ratified:" + sm._sha(candidate["id"] + "owner" + "seam")[:16], (
        "revision 1's identifier must be unchanged, or the printed record breaks"
    )


def test_a_held_ceiling_does_not_refresh_its_remembered_numerator():
    """The dilution defence compares today's count against the one recorded at the baseline. A
    metric sitting at its ceiling skipped the decline path and had its numerator refreshed anyway,
    so a worsening could launder itself over two runs: hold the ratio at the ceiling while the count
    climbs, then grow the denominator so the ratio dips and the pawl tightens against the inflated
    count. The count ends worse and the ceiling ends lower.
    """
    from coherence_ratchet.ratchet import Budget, tighten

    class Snap:
        def __init__(self, **kw):
            self._d = kw

        def to_dict(self):
            return dict(self._d)

    budget = Budget(ceilings={"cycle_ratio": 0.5}, numerators={"cycle_ratio": 2}, provenance={})

    # step one: cyclic modules double, the denominator grows with them, the ratio holds
    budget, declined = tighten(budget, Snap(cycle_ratio=0.5, cyclic_modules=4, n_modules=8))
    assert budget.numerators["cycle_ratio"] == 2, "the baseline count must survive a held ceiling"

    # step two: the ratio dips, but the count is still worse than the baseline
    budget, declined = tighten(budget, Snap(cycle_ratio=0.3, cyclic_modules=3, n_modules=10))
    assert budget.ceilings["cycle_ratio"] == 0.5, "the ceiling must not move on a diluted ratio"
    assert "cycle_ratio" in declined


def test_tighten_records_who_moved_the_ceiling():
    """The budgets file is the one artefact CI enforces, and the honest-metric argument rests on its
    provenance. Carrying the baseline provenance forward unchanged left a lowered ceiling
    attributable only to whoever took the baseline.
    """
    from coherence_ratchet.ratchet import Budget, tighten

    class Snap:
        def to_dict(self):
            return {"cycle_ratio": 0.2, "cyclic_modules": 1, "n_modules": 5}

    budget = Budget(ceilings={"cycle_ratio": 0.5}, numerators={"cycle_ratio": 2},
                    provenance={"author": "baseline owner", "reason": "first baseline"})
    tightened, _ = tighten(budget, Snap(), by="pricing steward", at="2026-08-11")

    assert tightened.provenance["author"] == "baseline owner"
    event = tightened.provenance["tightened"][-1]
    assert event["by"] == "pricing steward"
    assert event["at"] == "2026-08-11"
    assert event["metrics"]["cycle_ratio"] == {"from": 0.5, "to": 0.2}


def test_rebaselining_without_a_reason_is_refused():
    """--force replaces the enforced ceilings, which is how worsening enters without a signed
    decision. The CLI's own error text, the appendix and the honest-metric argument all said the
    reason was required while only --by was checked.
    """
    import tempfile

    from coherence_ratchet import cli

    budgets = os.path.join(tempfile.mkdtemp(), "b.json")
    root = os.path.join(ROOT, "playground", "_states", "05-checkout-clean", "checkout_pricing")

    assert cli.main(["init", root, "--budgets", budgets, "--by", "owner", "--reason", "first"]) == 0
    assert cli.main(["init", root, "--budgets", budgets, "--by", "owner", "--force"]) == 2
    assert cli.main(["init", root, "--budgets", budgets, "--by", "owner", "--force",
                     "--reason", "regional baseline after consolidation"]) == 0
