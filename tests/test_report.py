"""Tests for the leading-indicator report (deterministic, offline)."""

import datetime
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import report

TODAY = datetime.date(2026, 7, 1)


def _ledger(entries):
    d = tempfile.mkdtemp()
    path = os.path.join(d, "led.jsonl")
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


def test_empty_ledger_is_clean():
    r = report.report(_ledger([]), today=TODAY)
    assert r["total"] == 0
    assert r["coverage"] == 1.0


def test_coverage_counts_owned_and_dated():
    path = _ledger([
        {"when": "2026-01-01", "region": "a", "owner": "team", "repayment_trigger": "2027-01-01"},
        {"when": "2026-02-01", "region": "b", "owner": "", "repayment_trigger": "later"},
    ])
    r = report.report(path, today=TODAY)
    assert r["total"] == 2
    assert r["owned"] == 1
    assert r["coverage"] == 0.5  # only the first is owned AND dated


def test_overdue_detected_by_trigger_date():
    path = _ledger([
        {"when": "2026-01-01", "region": "a", "owner": "t", "repayment_trigger": "2025-12-01 refactor"},
        {"when": "2026-02-01", "region": "b", "owner": "t", "repayment_trigger": "2099-01-01"},
    ])
    r = report.report(path, today=TODAY)
    assert len(r["overdue"]) == 1
    assert r["overdue"][0]["region"] == "a"


def test_held_days_since_last_accepted():
    path = _ledger([
        {"when": "2026-06-01", "region": "a", "owner": "t", "repayment_trigger": "x"},
        {"when": "2026-01-01", "region": "b", "owner": "t", "repayment_trigger": "x"},
    ])
    r = report.report(path, today=TODAY)
    assert r["last_accepted"] == "2026-06-01"
    assert r["held_days"] == 30
