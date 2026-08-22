"""The optional ratification policy, and the honest limit it exists to bound.

`--by` is a string. A string looks the same whoever types it, so the CLI cannot tell a person from a
process and the book no longer claims it can. What a team can do is write a policy down, and these
tests pin both halves of that: absent by default and silent, enforced when present.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import selfmodel  # noqa: E402


def _policy(tmp, payload):
    path = os.path.join(tmp, "ratification-policy.json")
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(payload, stream)
    return path


def test_no_policy_file_means_no_check_and_no_output():
    """The default must stay silent, or every printed block in the book moves."""
    tmp = tempfile.mkdtemp()
    path = selfmodel.policy_path_for(os.path.join(tmp, "intent.json"))
    assert not os.path.exists(path)
    assert selfmodel.check_ratification_policy(path, approved_by="anybody at all") is None


def test_an_approver_allowlist_admits_a_listed_name():
    tmp = tempfile.mkdtemp()
    path = _policy(tmp, {"approvers": ["ada@example.com", "grace@example.com"]})
    assert selfmodel.check_ratification_policy(path, approved_by="ada@example.com")


def test_an_approver_allowlist_refuses_an_unlisted_name():
    tmp = tempfile.mkdtemp()
    path = _policy(tmp, {"approvers": ["ada@example.com"]})
    try:
        selfmodel.check_ratification_policy(path, approved_by="an agent")
    except selfmodel.RatificationRefused as exc:
        assert "does not list" in str(exc)
        assert "ada@example.com" in str(exc), "the refusal must say who may ratify"
        return
    raise AssertionError("an unlisted approver was admitted")


def test_ratify_time_does_not_pretend_to_check_a_commit_that_does_not_exist():
    """The old check ran `git verify-commit HEAD` before the intent file was written, so it verified
    the preceding commit. A process could ratify on top of any signed HEAD and commit the intent
    unsigned. Ratify time now says where the check lives instead of asserting a property it cannot
    see."""
    tmp = tempfile.mkdtemp()
    path = _policy(tmp, {"require_signed_commit": True})
    # No refusal, because there is nothing here to refuse on.
    assert selfmodel.check_ratification_policy(path, approved_by="ada", root=tmp) is not None


def test_verify_intent_checks_the_commit_that_changed_the_intent_not_head():
    """The commit the policy is about is the one carrying the ratification. Verifying HEAD instead
    is what made the guarantee empty, so this pins which commit is inspected."""
    tmp = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", "."], cwd=tmp, capture_output=True, check=False)

    def commit(name, body, message):
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as stream:
            stream.write(body)
        subprocess.run(["git", "add", "-A"], cwd=tmp, capture_output=True, check=False)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", message], cwd=tmp, capture_output=True, check=False)
        return subprocess.run(["git", "log", "-1", "--format=%H"], cwd=tmp,
                              capture_output=True, text=True, check=False).stdout.strip()

    intent = os.path.join(tmp, "intent.json")
    intent_sha = commit("intent.json", "{}\n", "ratify")
    head_sha = commit("unrelated.txt", "x\n", "something else")
    assert intent_sha != head_sha

    path = _policy(tmp, {"require_signed_commit": True})
    try:
        selfmodel.verify_intent(intent, policy_path=path, root=tmp)
    except selfmodel.RatificationRefused as exc:
        message = str(exc)
        assert intent_sha[:12] in message, "the intent file's commit is the one inspected"
        assert head_sha[:12] not in message, "HEAD is not what the policy is about"
        return
    raise AssertionError("an unsigned intent commit satisfied a policy requiring a signature")


def test_verify_intent_is_silent_when_no_policy_requires_it():
    tmp = tempfile.mkdtemp()
    path = _policy(tmp, {"approvers": ["ada"]})
    report = selfmodel.verify_intent(os.path.join(tmp, "intent.json"), policy_path=path, root=tmp)
    assert report["checked"] is False


def test_the_cli_refuses_when_the_policy_does():
    """End to end: the refusal has to reach the exit code, or it is decoration."""
    from coherence_ratchet import cli

    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "coherence"), exist_ok=True)
    _policy(os.path.join(tmp, "coherence"), {"approvers": ["ada@example.com"]})
    code = cli.main(["selfmodel", "ratify", "no-such-candidate",
                     "--model", os.path.join(tmp, "coherence", "selfmodel.json"),
                     "--intent", os.path.join(tmp, "coherence", "intent.json"),
                     "--by", "an agent", "--scope", "billing",
                     "--rationale", "because I said so"])
    assert code == 2, f"a refused ratifier must not exit 0 (got {code})"
