"""D3 probe — public-API contract check at consolidation time.

Ferdous et al. (MSR 2026, "Safer Builders, Risky Maintainers") measured agents breaking
public contracts 2-3x more on refactor/chore work (6.72%/9.35%) than on feat/fix. The
consolidation this method encourages is exactly that risky class, so `apidiff` adds a
deterministic contract check beside `prove`: diff the public surface (module-level
functions/classes, signatures) of the tree before and after the change.

Three runs:
  1. before -> after_breaking     (fixture: a careless consolidation — must be BREAKING)
  2. before -> after_compatible   (fixture: same paydown, surface preserved — must be COMPATIBLE)
  3. playground 03-loyalty -> 04-consolidated (the shipped playground's own consolidation)

The fixtures mirror the E4/codemod consolidation shape (four fetchers with inline retry
loops folded onto a canonical `retry` helper).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from coherence_ratchet.apidiff import diff_trees

FIX = os.path.join(HERE, "_fixtures", "apidiff")
STATES = os.path.join(HERE, "playground", "_states")


def show(name, old, new):
    findings, verdict = diff_trees(old, new)
    print(f"\n### {name} -> {verdict}")
    for f in findings:
        flag = "BREAKING" if f.breaking else "ok"
        print(f"  {f.status:<18} {f.symbol:<38} {flag}")
        for r in f.reasons:
            print(f"      - {r}")
    return findings, verdict


def main():
    ok = True

    findings, verdict = show("fixture: careless consolidation (before -> after_breaking)",
                             os.path.join(FIX, "before"), os.path.join(FIX, "after_breaking"))
    ok &= verdict == "BREAKING"
    caught = {f.symbol for f in findings if f.breaking}
    ok &= "billing.fetchers:fetch_report" in caught       # removed public helper
    ok &= "billing.retry:retry" in caught                 # renamed/removed params
    ok &= "billing.fetchers:fetch_user" in caught         # keyword-only restriction

    findings, verdict = show("fixture: faithful consolidation (before -> after_compatible)",
                             os.path.join(FIX, "before"), os.path.join(FIX, "after_compatible"))
    ok &= verdict == "COMPATIBLE"
    # the appended optional param is reported but does not fail
    ok &= any(f.status == "CHANGED-SIGNATURE" and not f.breaking for f in findings)

    _, verdict = show("playground: 03-loyalty -> 04-consolidated (the shipped consolidation)",
                      os.path.join(STATES, "03-loyalty", "billing"),
                      os.path.join(STATES, "04-consolidated", "billing"))
    print(f"\n  note: the playground's own consolidation narrowed a public signature "
          f"(submit_with_retry lost 'pause') — verdict {verdict}. The check catches the "
          f"shipped fixture too; whether that break is acceptable is the steward's call.")

    print("\nPROBE", "OK" if ok else "FAILED",
          "— breaking variant caught, compatible variant cleared" if ok else "")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
