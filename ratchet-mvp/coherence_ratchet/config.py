"""Optional per-repository settings, and the paths a reading should not walk.

Two rules make this safe to ship in a book whose printed output is byte-verified.

**Absent by default, and absent from the fixtures.** Every default stays the literal it already was.
A repository with no `coherence/config.json` measures exactly as it did before this file existed, so
no printed block can move because a setting appeared.

**Every applied setting is reported.** A threshold that silently differs from the default is how two
readers compare numbers that were never comparable. Anything this module changes, the caller prints.

The format is JSON rather than TOML: `tomllib` is 3.11+, the package supports 3.10, and adding
`tomli` would break the zero-dependency property for a config file nobody is required to write.
"""

from __future__ import annotations

import fnmatch
import json
import os

CONFIG_NAME = os.path.join("coherence", "config.json")
IGNORE_NAME = ".coherenceignore"

# Only these may be set. An unknown key is a typo or a version gap, and either way the reader needs
# to hear about it rather than have it quietly ignored.
KNOWN = {
    "similarity": (float, "near-duplicate threshold; `calibrate` measures one for your own code"),
    "min_tokens": (int, "smallest function body the duplication signals will consider"),
    "max_candidates": (int, "cap on the candidate list a grounding block carries"),
}


class ConfigError(Exception):
    """The config file exists and cannot be honoured."""


def load(root: str = ".") -> tuple[dict, list[str]]:
    """Return (settings, notes). Absent file is not an error and yields no settings."""
    path = os.path.join(root, CONFIG_NAME)
    if not os.path.exists(path):
        return {}, []
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"{path} is not readable JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise ConfigError(f"{path} must hold a JSON object")

    unknown = sorted(set(doc) - set(KNOWN))
    if unknown:
        raise ConfigError(
            f"{path} sets unknown key(s): {', '.join(unknown)}. "
            f"Known keys are {', '.join(sorted(KNOWN))}."
        )

    settings, notes = {}, []
    for key, value in doc.items():
        want, _ = KNOWN[key]
        try:
            settings[key] = want(value)
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"{path}: {key} must be {want.__name__}, got {value!r}") from exc
        notes.append(f"{key} = {settings[key]} (from {CONFIG_NAME}, not the shipped default)")
    return settings, notes


def load_ignore(root: str = ".") -> list[str]:
    """Glob patterns from `.coherenceignore`, one per line, `#` comments."""
    path = os.path.join(root, IGNORE_NAME)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if line:
                out.append(line)
    return out


def is_ignored(rel_path: str, patterns: list[str]) -> bool:
    """Match a path relative to the measured root against the ignore patterns."""
    if not patterns:
        return False
    rel = rel_path.replace(os.sep, "/")
    parts = rel.split("/")
    for pat in patterns:
        p = pat.rstrip("/")
        if fnmatch.fnmatch(rel, p) or any(fnmatch.fnmatch(seg, p) for seg in parts):
            return True
        if fnmatch.fnmatch(rel, p + "/*") or rel.startswith(p + "/"):
            return True
    return False
