# The experiment harness

## Exit codes (fixed 12 August 2026)

The dispatcher follows the CLI's contract, because a harness that reports success while measuring
nothing is the defect this project exists to prevent, sitting in the tool that produces the evidence.

    0   every trial completed
    2   refused before spending anything (undated model alias, no --out, unreadable probe)
    3   some trials failed; the arms are no longer balanced and a rate must state its real denominator
    4   NOT MEASURED — every trial failed; the run directory holds no evidence

It previously returned 0 in all four cases. A two-arm run whose forty trials failed on an SSL error,
and then a run that failed on a mistyped model id, both reported success; the errors were in the
manifest and the exit code said the evidence had been collected.
