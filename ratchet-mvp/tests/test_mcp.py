"""The agent-facing interface returns standing, and refuses to let an agent create it.

Two properties here are the method rather than the implementation, and both are tested as behaviour
an agent could observe: a concept nobody ratified comes back as an explicit `NONE` rather than the
most frequent shape, and the one tool that could let an agent approve its own grounding is advertised
and always refuses.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import cli, mcp  # noqa: E402

STATES = os.path.join(ROOT, "playground", "_states")


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def _workspace(ratify=False):
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(STATES, "03-loyalty", "billing"), os.path.join(d, "billing"))
    _git(["init", "-q", "."], d)
    cwd = os.getcwd()
    os.chdir(d)
    try:
        cli.main(["selfmodel", "derive", "billing", "--model", "coherence/selfmodel.json"])
        if ratify:
            with open("coherence/selfmodel.json") as f:
                model = json.load(f)
            candidate = next(c["id"] for c in model["candidates"]
                             if c["kind"] == "reuse_helper" and "retry" in json.dumps(c).lower())
            cli.main(["selfmodel", "ratify", candidate,
                      "--model", "coherence/selfmodel.json",
                      "--intent", "coherence/intent.json",
                      "--by", "billing owner",
                      "--rationale", "one retry policy",
                      "--scope", "billing"])
    finally:
        os.chdir(cwd)
    return d


def _server(workspace):
    return mcp.Server(
        os.path.join(workspace, "billing"),
        os.path.join(workspace, "coherence", "selfmodel.json"),
        os.path.join(workspace, "coherence", "intent.json"),
        os.path.join(workspace, "coherence", "coherence-ledger.jsonl"),
    )


def _call(server, name, arguments):
    response = mcp.handle(server, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                   "params": {"name": name, "arguments": arguments}})
    return response["result"]


def _payload(result):
    return json.loads(result["content"][0]["text"])


# --- standing ---------------------------------------------------------------

def test_a_ratified_concept_is_binding_and_carries_its_provenance():
    server = _server(_workspace(ratify=True))
    payload = _payload(_call(server, "coherence_canonical", {"concept": "retry"}))

    assert payload["status"] == "RATIFIED"
    assert payload["binding"] is True
    assert payload["provenance"]["approved_by"] == "billing owner"
    assert payload["provenance"]["approved_at"]
    assert payload["provenance"]["scope"] == "billing"


def test_an_unratified_concept_is_a_candidate_and_says_it_is_not_an_instruction():
    server = _server(_workspace(ratify=False))
    payload = _payload(_call(server, "coherence_canonical", {"concept": "retry"}))

    assert payload["status"] == "CANDIDATE"
    assert payload["binding"] is False
    assert "not an instruction" in payload["warning"]


def test_nothing_ratified_returns_an_explicit_refusal_not_a_guess():
    """The differentiating answer: no other agent-facing tool can say 'nothing is approved here'."""
    server = _server(_workspace(ratify=True))
    payload = _payload(_call(server, "coherence_canonical", {"concept": "zzz_no_such_concept"}))

    assert payload["status"] == "NONE"
    assert payload["binding"] is False
    assert "no canonical answer" in payload["refusal"]


def test_every_response_declares_whether_the_model_is_current():
    server = _server(_workspace(ratify=True))
    payload = _payload(_call(server, "coherence_canonical", {"concept": "retry"}))

    assert payload["stale"] is False


def test_a_stale_model_downgrades_rather_than_describing_a_tree_that_moved():
    workspace = _workspace(ratify=False)
    with open(os.path.join(workspace, "billing", "extra.py"), "w") as f:
        f.write("def added_after_derivation(a, b, c):\n    return (a + b) * c\n")
    server = _server(workspace)
    payload = _payload(_call(server, "coherence_canonical", {"concept": "retry"}))

    assert payload["stale"] is True
    assert payload["status"] == "NONE"


# --- the refusal ------------------------------------------------------------

def test_ratify_is_advertised_so_the_boundary_is_discoverable():
    """Advertising the refusal means an agent reads the boundary in the tool list, rather than
    inventing a way around one it never saw."""
    names = [t["name"] for t in mcp.TOOLS]

    assert "coherence_ratify" in names
    entry = next(t for t in mcp.TOOLS if t["name"] == "coherence_ratify")
    assert "REFUSES" in entry["description"]


def test_an_agent_cannot_ratify():
    server = _server(_workspace())
    result = _call(server, "coherence_ratify",
                   {"candidate_id": "reuse_helper:abc", "rationale": "looks fine to me"})

    assert result.get("isError") is True
    text = result["content"][0]["text"]
    assert "cannot approve its own grounding" in text
    assert "--by" in text


def test_no_tool_mutates_intent():
    """Read-only is what makes the contract enforceable rather than aspirational."""
    workspace = _workspace(ratify=True)
    intent_path = os.path.join(workspace, "coherence", "intent.json")
    with open(intent_path) as f:
        before = f.read()

    server = _server(workspace)
    for name, args in (("coherence_canonical", {"concept": "retry"}),
                       ("coherence_grounding", {}),
                       ("coherence_exposure", {}),
                       ("coherence_ratify", {"candidate_id": "x"})):
        _call(server, name, args)

    with open(intent_path) as f:
        assert f.read() == before


# --- protocol ---------------------------------------------------------------

def test_initialize_and_tools_list():
    server = _server(_workspace())
    init = mcp.handle(server, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    listed = mcp.handle(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    assert init["result"]["serverInfo"]["name"] == "coherence-ratchet"
    assert init["result"]["protocolVersion"] == mcp.PROTOCOL_VERSION
    assert {t["name"] for t in listed["result"]["tools"]} == {
        "coherence_canonical", "coherence_grounding", "coherence_exposure",
        "coherence_advise", "coherence_ratify",
    }


def test_a_notification_gets_no_response():
    server = _server(_workspace())
    assert mcp.handle(server, {"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_an_unknown_tool_is_a_protocol_error():
    server = _server(_workspace())
    response = mcp.handle(server, {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                                   "params": {"name": "coherence_nope", "arguments": {}}})

    assert response["error"]["code"] == -32601


def test_serve_reads_a_stream_and_writes_one_response_per_request():
    server = _server(_workspace())
    stdin = io.StringIO(
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
        '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
    )
    stdout = io.StringIO()
    mcp.serve(server, stdin=stdin, stdout=stdout)
    lines = [json.loads(l) for l in stdout.getvalue().strip().split("\n")]

    assert [m["id"] for m in lines] == [1, 2]


def test_malformed_input_does_not_kill_the_server():
    server = _server(_workspace())
    stdin = io.StringIO('not json at all\n{"jsonrpc":"2.0","id":7,"method":"tools/list"}\n')
    stdout = io.StringIO()
    mcp.serve(server, stdin=stdin, stdout=stdout)

    assert json.loads(stdout.getvalue().strip())["id"] == 7
