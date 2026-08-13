"""Refuse to measure a tree that is not there.

Every measurement in this package walks a source root. Before this module
existed, ``os.walk`` on a path that did not exist yielded nothing, so a
mistyped, renamed or moved directory produced a complete all-zero reading and
exit 0. In CI that is the worst available outcome: ``check`` passes against a
path that no longer exists, and ``check --tighten`` reads the zeros as an
improvement and ratchets every ceiling to zero, destroying the budgets file
that is the only artefact CI enforces.

The rule this module enforces governs every instrument here: a failure must
never read as a clean result. A tree that cannot be measured raises, and the CLI
turns that into exit 2 with the path named.

The second guard is for a documented footgun rather than a bug. The analyser
names a package after the directory it is given, so pointing it one level up —
at the directory *holding* the package, or at a repository root — silently
measures zero dependency edges. Where the root holds no Python files itself and
exactly one subdirectory does, that is almost always the mistake, and the
suggestion costs a reader nothing.
"""

from __future__ import annotations

import os

# Directories that never contain source worth measuring. Kept in step with
# metrics._iter_py_files, which does the same filtering while walking.
SKIP_DIRS = {"__pycache__", ".git"}


class SourceTreeError(Exception):
    """A source root cannot be measured, and no reading should be reported."""


def _py_files_under(path: str) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        total += sum(1 for fn in filenames if fn.endswith(".py"))
    return total


def resolve_root(root: str) -> str:
    """Return ``root`` if it can be measured, else raise ``SourceTreeError``.

    Call once at the top of any public entry point that walks a source tree.
    """
    if not os.path.exists(root):
        raise SourceTreeError(f"no such path: {root}")
    if not os.path.isdir(root):
        raise SourceTreeError(
            f"not a directory: {root} (point at the package directory, not a file)"
        )

    if _py_files_under(root) == 0:
        raise SourceTreeError(f"no Python files under {root}; nothing to measure")

    top_level = [
        fn for fn in os.listdir(root)
        if fn.endswith(".py") and os.path.isfile(os.path.join(root, fn))
    ]
    if not top_level:
        candidates = [
            d for d in sorted(os.listdir(root))
            if d not in SKIP_DIRS
            and os.path.isdir(os.path.join(root, d))
            and _py_files_under(os.path.join(root, d)) > 0
        ]
        if len(candidates) == 1:
            suggested = os.path.join(root, candidates[0])
            raise SourceTreeError(
                f"{root} holds no Python files of its own. The analyser names a "
                f"package after the directory it is given, so measuring here reads "
                f"zero dependency edges. Did you mean {suggested}?"
            )

    return root
