"""Sample the signal portfolio across committed Git history without changing the working tree."""
from __future__ import annotations

import io
import json
import os
import subprocess
import tarfile
import tempfile

from .signals import measure_all


def _git(repo: str, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", "-C", repo, *args], capture_output=True,
        text=not binary, timeout=120, check=False,
    )
    if result.returncode:
        error = result.stderr.decode() if binary else result.stderr
        raise ValueError(error.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def _history(repo: str) -> list[tuple[str, str]]:
    output = _git(repo, "log", "--first-parent", "--format=%H|%cI", "--reverse")
    return [tuple(line.split("|", 1)) for line in output.splitlines() if "|" in line]


def _sample_indexes(length: int, count: int) -> list[int]:
    if length <= count:
        return list(range(length))
    if count <= 1:
        return [length - 1]
    return sorted({round(index * (length - 1) / (count - 1)) for index in range(count)})


def _relative_source(path: str, repo: str) -> str:
    absolute_repo = os.path.abspath(repo)
    absolute_path = os.path.abspath(path if os.path.isabs(path) else os.path.join(repo, path))
    relative = os.path.relpath(absolute_path, absolute_repo)
    if relative == ".." or relative.startswith(".." + os.sep):
        raise ValueError("history path must be inside --repo")
    return relative.replace(os.sep, "/")


def _safe_extract(tar: tarfile.TarFile, directory: str) -> None:
    root = os.path.realpath(directory)
    for member in tar.getmembers():
        destination = os.path.realpath(os.path.join(directory, member.name))
        if destination != root and not destination.startswith(root + os.sep):
            raise ValueError(f"unsafe archive member: {member.name}")
    tar.extractall(directory)


def sample_history(path: str, *, repo: str, samples: int = 24) -> dict:
    commits = _history(repo)
    if not commits:
        raise ValueError("repository has no commits")
    relative = _relative_source(path, repo)
    points = []
    for index in _sample_indexes(len(commits), samples):
        sha, date = commits[index]
        try:
            archive = _git(repo, "archive", "--format=tar", sha, relative, binary=True)
            with tempfile.TemporaryDirectory(prefix="coherence-history-") as directory:
                with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
                    _safe_extract(tar, directory)
                source = os.path.join(directory, relative)
                snapshot = measure_all(source).to_dict()
            points.append({"sha": sha, "date": date, "snapshot": snapshot})
        except (OSError, tarfile.TarError, ValueError) as exc:
            points.append({"sha": sha, "date": date, "error": str(exc)})
    return {
        "repo": os.path.abspath(repo),
        "path": relative,
        "commits_total": len(commits),
        "samples_requested": samples,
        "points": points,
    }


def render(result: dict) -> None:
    print(f"history: {result['path']} ({len(result['points'])} samples from {result['commits_total']} commits)")
    print("  date        commit    modules  cycle    duplication  shared literals")
    for point in result["points"]:
        if point.get("error"):
            print(f"  {point['date'][:10]}  {point['sha'][:8]}  ERROR: {point['error']}")
            continue
        snapshot = point["snapshot"]
        print(
            f"  {point['date'][:10]}  {point['sha'][:8]}  {snapshot.get('n_modules', 0):>7}  "
            f"{snapshot.get('cycle_ratio', 0):>5}    {snapshot.get('duplication_ratio', 0):>10}  "
            f"{snapshot.get('connascence_shared', 0):>15}"
        )


def register_cli(sub) -> None:
    parser = sub.add_parser("history", help="sample the signal portfolio across committed history")
    parser.add_argument("path", help="source path inside the repository")
    parser.add_argument("--repo", required=True, help="Git repository containing the source path")
    parser.add_argument("--samples", type=int, default=24)
    parser.add_argument(
        "--json", nargs="?", const="-", metavar="OUT",
        help="write JSON to OUT, or to stdout when OUT is omitted",
    )


def run_cli(args) -> int:
    try:
        result = sample_history(args.path, repo=args.repo, samples=args.samples)
    except ValueError as exc:
        print(f"history failed: {exc}")
        return 2
    if args.json:
        payload = json.dumps(result, indent=2, sort_keys=True)
        if args.json == "-":
            print(payload)
        else:
            os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
            with open(args.json, "w", encoding="utf-8") as stream:
                stream.write(payload + "\n")
            print(f"history written to {args.json}")
    else:
        render(result)
    return 0
