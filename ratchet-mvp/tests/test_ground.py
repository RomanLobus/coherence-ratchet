"""The grounding pack must reach the agent, and must fail when it stops describing the code.

`selfmodel context` wrote a file and nothing read it, so the loop was open at the join that matters:
where what a team ratified reaches the thing writing the code. These tests pin the two properties
that make closing it safe — the tool never destroys a reader's own prose, and a block describing a
tree that no longer exists is a failure rather than a quietly wrong instruction.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import cli, ground  # noqa: E402
from coherence_ratchet.exitcodes import EXIT_HELD, EXIT_REFUSED  # noqa: E402
from coherence_ratchet.selfmodel import derive, empty_intent, model_hash  # noqa: E402

STATES = os.path.join(ROOT, "playground", "_states")
FIXTURE = os.path.join(STATES, "06-checkout-cycle", "checkout_pricing")


def _workspace():
    d = tempfile.mkdtemp()
    shutil.copytree(FIXTURE, os.path.join(d, "checkout_pricing"))
    return d


def _run(workspace, argv):
    cwd = os.getcwd()
    os.chdir(workspace)
    try:
        return cli.main(argv)
    finally:
        os.chdir(cwd)


def _block(root):
    model = derive(root)
    return ground.render_block(model, empty_intent(model), tool_version="test", today="2026-08-11")


# --- the block itself -------------------------------------------------------

def test_block_states_the_epistemic_contract():
    """A derived model piped into an agent without labels automates the codebase's accidents."""
    block = _block(FIXTURE)

    assert "[RATIFIED]" in block and "[OBSERVED]" in block and "[CANDIDATE]" in block
    assert "Frequency is not authority" in block
    # The candidate warning has to be an instruction not to act, not a hedge.
    assert "Do not act on" in block


def test_block_carries_the_hashes_that_make_staleness_checkable():
    block = _block(FIXTURE)
    declared = ground.block_hashes(block)

    assert declared["model"] == model_hash(derive(FIXTURE))
    assert declared["tree"] == derive(FIXTURE)["source"]["tree_hash"]


def test_candidates_are_capped_and_the_truncation_is_stated():
    model = derive(FIXTURE)
    block = ground.render_block(model, empty_intent(model), tool_version="test",
                                today="2026-08-11", max_candidates=1)
    shown = [l for l in block.split("\n") if l.startswith("- [CANDIDATE]")]

    assert len(shown) <= 1
    if len(model.get("candidates", [])) > 1:
        assert "further candidates, not shown" in block


# --- never destroy what the tool did not write ------------------------------

def test_prose_outside_the_markers_survives_byte_for_byte():
    workspace = _workspace()
    prose = "# My notes\n\nSomething a person wrote.\n"
    target = os.path.join(workspace, "AGENTS.md")
    with open(target, "w") as f:
        f.write(prose)

    assert _run(workspace, ["ground", "checkout_pricing", "--target", "AGENTS.md"]) == EXIT_HELD

    with open(target) as f:
        content = f.read()
    assert content.startswith(prose)
    assert ground.BEGIN in content and ground.END in content


def test_regrounding_replaces_the_block_and_does_not_stack_them():
    workspace = _workspace()
    for _ in range(3):
        assert _run(workspace, ["ground", "checkout_pricing", "--target", "AGENTS.md"]) == EXIT_HELD

    with open(os.path.join(workspace, "AGENTS.md")) as f:
        content = f.read()
    assert content.count(ground.BEGIN) == 1
    assert content.count(ground.END) == 1


def test_unbalanced_markers_are_refused_rather_than_guessed():
    workspace = _workspace()
    target = os.path.join(workspace, "AGENTS.md")
    with open(target, "w") as f:
        f.write("intro\n" + ground.BEGIN + " model=x -->\nhalf a block, no end marker\n")

    assert _run(workspace, ["ground", "checkout_pricing", "--target", "AGENTS.md"]) == EXIT_REFUSED


def test_writes_agents_md_by_default():
    """AGENTS.md is the vendor-neutral convention; targeting it dates better than any one harness."""
    workspace = _workspace()
    assert _run(workspace, ["ground", "checkout_pricing"]) == EXIT_HELD
    assert os.path.exists(os.path.join(workspace, "AGENTS.md"))


# --- the freshness gate -----------------------------------------------------

def test_check_passes_when_the_block_matches_the_tree():
    workspace = _workspace()
    _run(workspace, ["ground", "checkout_pricing", "--target", "AGENTS.md"])

    assert _run(workspace, ["ground", "checkout_pricing", "--check"]) == EXIT_HELD


def test_check_fails_once_the_code_moves_under_the_block():
    """The thesis as a build failure: the pull request stops when the file the agents read no longer
    describes the code they are editing."""
    workspace = _workspace()
    _run(workspace, ["ground", "checkout_pricing", "--target", "AGENTS.md"])

    with open(os.path.join(workspace, "checkout_pricing", "pricing.py"), "a") as f:
        f.write("\n\ndef added_after_grounding(x):\n    return x * 2\n")

    assert _run(workspace, ["ground", "checkout_pricing", "--check"]) == EXIT_REFUSED


def test_check_refuses_a_file_with_no_block():
    workspace = _workspace()
    with open(os.path.join(workspace, "AGENTS.md"), "w") as f:
        f.write("no block here\n")

    assert _run(workspace, ["ground", "checkout_pricing", "--check"]) == EXIT_REFUSED


def test_check_refuses_a_missing_target():
    workspace = _workspace()
    assert _run(workspace, ["ground", "checkout_pricing", "--check"]) == EXIT_REFUSED


def test_ground_refuses_an_unmeasurable_tree():
    workspace = _workspace()
    assert _run(workspace, ["ground", "no_such_package"]) == EXIT_REFUSED
