"""History sampling must not checkout or modify the repository under analysis."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import history


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


def test_history_samples_commits_without_moving_head():
    with tempfile.TemporaryDirectory() as repo:
        _git(repo, "init")
        _git(repo, "config", "user.email", "test@example.com")
        _git(repo, "config", "user.name", "Test")
        source = os.path.join(repo, "billing")
        os.makedirs(source)
        with open(os.path.join(source, "pricing.py"), "w") as stream:
            stream.write("def total(value: int):\n    return value\n")
        _git(repo, "add", "billing/pricing.py")
        _git(repo, "commit", "-m", "baseline")
        with open(os.path.join(source, "receipt.py"), "w") as stream:
            stream.write("from .pricing import total\n")
        _git(repo, "add", "billing/receipt.py")
        _git(repo, "commit", "-m", "consumer")
        before = _git(repo, "rev-parse", "HEAD")
        result = history.sample_history(source, repo=repo, samples=2)
        after = _git(repo, "rev-parse", "HEAD")
        assert before == after
        assert len(result["points"]) == 2
        assert all("snapshot" in point for point in result["points"])
