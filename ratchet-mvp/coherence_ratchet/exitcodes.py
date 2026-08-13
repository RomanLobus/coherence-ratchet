"""The exit-code contract, in one place because the book prints it.

    0  held: nothing crossed, nothing found
    1  the line was crossed: a rule a person ratified, or a ceiling an owner set
    2  usage error, or the tool refused to measure
    3  advisory findings present; not a failure
    4  NOT MEASURED: the tool could not complete

Two rules make this contract the method rather than decoration.

**A candidate never exits non-zero.** Only a line a named person ratified, or a ceiling an owner set,
may fail a build. A heuristic the tool inferred is surfaced at 3 and decided by a human. This is the
difference between this tool and a detector, expressed as an integer.

**A failure never reads as a clean result.** A tool that could not measure exits 4 and says so; it
does not return zero findings. The rule a consumer is told to encode is that 4 is a failure, never a
pass. A pipeline that green-lights on 4 has exactly the defect this book spends a chapter describing.
"""

EXIT_HELD = 0
EXIT_CROSSED = 1
EXIT_REFUSED = 2
EXIT_ADVISORY = 3
EXIT_NOT_MEASURED = 4
