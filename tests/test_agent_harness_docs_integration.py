"""Synthetic corpus -> native request/action -> terminal score evidence."""

import hashlib
import json
import os
import shlex
from dataclasses import replace

import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401
from test_agent_harness_native_conditions import _cell, _native_runtime
from test_agent_harness_native_launcher import Provider, runner


def synthetic_corpus(root):
    from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus
    root.mkdir()
    text = "Resistor SYNTHETIC_DOC: offline bounded retrieval fixture."
    (root / "guide.txt").write_text(text)
    return OfflineDocsCorpus.from_manifest(root, {
        "schema_version": 1, "synthetic_only": True, "network_enabled": False,
        "builder": "unit-test", "exclusions": ["hidden", "r53-test-task"],
        "documents": [{"id": "guide", "path": "guide.txt", "source": "synthetic_fixture",
                       "license": "CC0-1.0", "section": "public_notes",
                       "sha256": hashlib.sha256(text.encode()).hexdigest()}],
    })


@pytest.mark.parametrize("backend,fmt", [
    ("native-mini-swe", "native_tool_calls"),
    ("native-reasoning", "native_tool_calls"),
    ("native-reasoning", "strict_json"),
])
@pytest.mark.parametrize("arm", ["Agentic", "Agent-No-EVAS"])
def test_synthetic_docs_reach_both_backends_and_scored_identity(native_case, tmp_path, backend, fmt, arm):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    from runners.agent_harness import read_trajectory
    import score_campaign as scorer

    corpus = synthetic_corpus(tmp_path / "corpus")
    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="docs-runtime")
    (runtime / "public/submission/model.va").write_text("module model; endmodule\n")
    cell = {**_cell(arm=arm), "family_id": "001"}
    client = Provider(["unused", "vabench-submit"])
    original = client.complete
    requested_tools = []

    def complete(messages, max_tokens, tools, **kwargs):
        requested_tools.append(tools)
        response = original(messages, max_tokens, tools, **kwargs)
        message = response["choices"][0]["message"]
        function = message["tool_calls"][0]["function"]
        if len(client.requests) == 1:
            function.update(name="vaevas_docs_search", arguments=json.dumps({"query": "resistor", "top_k": 1}))
        if fmt == "strict_json":
            message.pop("tool_calls")
            message["content"] = json.dumps({"tool_name": function["name"], "arguments": json.loads(function["arguments"])})
        return response

    client.complete = complete
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=client, attempt_id="docs",
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True, episode_backend=backend,
        reasoning_proposal_format=fmt, model_call_limit=2,
        campaign_file_sha256="c" * 64, docs_corpus=corpus,
    )
    assert run.artifact_path is not None, run.result
    assert len(client.requests) == 2
    visible = json.dumps(client.requests[-1])
    assert "SYNTHETIC_DOC" in visible
    assert corpus.profile_sha256 in visible
    assert "FINAL_JUDGE_SENTINEL" not in visible
    if fmt != "strict_json":
        assert {tool["function"]["name"] for tool in requested_tools[0]} == {"bash", "vaevas_docs_search"}
    manifest = runner.read_json(runtime / "evidence/native-launcher/manifest.json")
    assert manifest["extensions"]["offline_docs"]["profile"] == corpus.profile
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["extensions"]["offline_docs"]["profile_sha256"] == corpus.profile_sha256
    events = read_trajectory(run.trajectory_path)
    docs = [event for event in events if event["event_type"] == "environment_observed"
            and event["payload"]["tool_name"] == "vaevas_docs_search"]
    assert len(docs) == 1
    private = read_trajectory(runtime / "evidence/native-launcher/private-events.jsonl")
    result = next(event["payload"]["observation"] for event in private
                  if event["event_type"] == "tool_result"
                  and event["payload"]["observation"]["tool_name"] == "vaevas_docs_search")
    assert docs[0]["payload"]["payload_sha256"] == result["payload_sha256"]
    assert result["payload"]["corpus_profile_sha256"] == corpus.profile_sha256


def test_oneshot_rejects_interactive_docs_before_reserving_runtime(native_case, tmp_path):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    corpus = synthetic_corpus(tmp_path / "corpus")
    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="oneshot-docs")
    with pytest.raises(ValueError, match="OneShot"):
        run_prepared_native_mini_swe(
            runtime=runtime, cell=_cell(arm="OneShot"), client=Provider([]),
            attempt_id="docs", evas_command=arguments["evas_command"], docs_corpus=corpus,
        )
    assert not (runtime / "evidence/native-launcher").exists()


@pytest.mark.parametrize("identity_field", ["registry_sha256", "effective_capability_sha256"])
def test_scorer_rejects_undeclared_docs_capability(native_case, tmp_path, identity_field):  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    from runners.agent_harness import ToolRegistry
    from runners.agent_harness.backends.mini_swe import mini_swe_bash_tool_descriptor
    from runners.agent_harness.tools.offline_docs_tool import docs_tool_descriptor
    import score_campaign as scorer

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="undeclared-docs")
    cell = {**_cell(arm="Agent-No-EVAS"), "family_id": "001"}
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=Provider(["pwd"]), attempt_id="no-docs",
        evas_command=arguments["evas_command"], allow_insecure_test_sandbox=True,
        model_call_limit=1, campaign_file_sha256="c" * 64,
    )
    assert run.artifact_path is None
    assert "extensions" not in scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    corpus = synthetic_corpus(tmp_path / "identity-corpus")
    registry = ToolRegistry([
        mini_swe_bash_tool_descriptor(allowed_conditions=["Agent-No-EVAS"]),
        docs_tool_descriptor(corpus.profile, condition="Agent-No-EVAS"),
    ])
    identities = {
        "registry_sha256": registry.registry_sha256,
        "effective_capability_sha256": registry.resolve(
            condition_id="Agent-No-EVAS", model_visible=True,
        ).effective_capability_sha256,
    }
    path = runtime / "evidence/native-episode/request.json"
    request = json.loads(path.read_text())
    request[identity_field] = identities[identity_field]
    path.chmod(0o600)  # Mutate only newly generated fixture evidence, never a live run.
    path.write_text(json.dumps(request))
    with pytest.raises(ValueError, match="capability"):
        scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)


def test_docs_schema_is_closed_and_freezes_bounded_source_payload(tmp_path):
    import copy
    import jsonschema
    from runners.agent_harness.tools.offline_docs_tool import docs_tool_descriptor

    corpus = synthetic_corpus(tmp_path / "schema-corpus")
    schema = docs_tool_descriptor(corpus.profile, condition="Agentic")["observation_schema"]
    payload = corpus.search("resistor")
    jsonschema.validate(payload, schema)
    mutations = []
    extra = copy.deepcopy(payload)
    extra["unexpected"] = True
    mutations.append(extra)
    for key in ("source_tree_sha256", "index_sha256", "query_sha256", "matches", "truncated"):
        missing = copy.deepcopy(payload)
        missing.pop(key)
        mutations.append(missing)
    for key, value in (("source_sha256", "bad"), ("content_sha256", "bad"),
                       ("snippet", "x" * 601), ("unexpected", True)):
        invalid = copy.deepcopy(payload)
        invalid["matches"][0][key] = value
        mutations.append(invalid)
    for invalid in mutations:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid, schema)


def test_docs_preserves_internal_failure_instead_of_blame_model(tmp_path, monkeypatch):
    from runners.agent_harness import AgentAction, ToolRegistry
    from runners.agent_harness.tools.offline_docs_tool import OfflineDocsTool

    corpus = synthetic_corpus(tmp_path / "failure-corpus")
    tool = OfflineDocsTool(corpus, condition="Agentic")
    capability = ToolRegistry([tool.descriptor]).resolve(
        condition_id="Agentic", model_visible=True,
    ).capabilities[0]
    action = AgentAction("action-1", "vaevas_docs_search", {"query": "resistor"},
                         "fixture", candidate_tree_sha256="a" * 64)

    def internal_failure(*args, **kwargs):
        raise ValueError("internal invariant broken")

    invalid = replace(action, arguments={"query": ""})
    assert tool.step(invalid, capability, candidate_sha256="a" * 64).code == "invalid_tool_arguments"
    monkeypatch.setattr(corpus, "search", internal_failure)
    with pytest.raises(ValueError, match="internal invariant broken"):
        tool.step(action, capability, candidate_sha256="a" * 64)


def test_synthetic_extension_rows_cannot_silently_enter_existing_comparison():
    import score_campaign as scorer
    from test_agent_harness_result_ledger import _campaign, _row, result_ledger
    campaign = _campaign()
    rows = [_row(cell, score=0, status="behavior_failure") for cell in campaign["cells"]]
    rows[-1]["extensions"] = {"offline_docs": {"profile_sha256": "c" * 64}}
    with pytest.raises(ValueError, match="extension"):
        scorer.summarize(rows, judge_kind="final_trusted_replay")
    with pytest.raises(ValueError, match="extension"):
        result_ledger.build_native_campaign_ledger(campaign, rows, campaign_file_sha256="c" * 64)


def test_docs_reuses_controller_tool_budget_before_second_dispatch(native_case, tmp_path):  # noqa: F811
    from native_episode import run_native_episode
    from run_native_mini_swe import _RecordedEnvironment
    from runners.agent_harness import AgentAction, ToolRegistry, read_trajectory
    from runners.agent_harness.tools.offline_docs_tool import OfflineDocsTool

    args, _, validator = native_case
    tool = OfflineDocsTool(synthetic_corpus(tmp_path / "budget-corpus"), condition="Agentic")
    calls = []
    args["environment"] = _RecordedEnvironment(
        record=lambda name, payload: calls.append((name, payload)), docs_tool=tool,
        legacy_environment=validator.environment, task_payload={"prompt": "synthetic task"},
        candidate_tree_sha256=validator.candidate_tree_sha256,
        freeze_submission=args["environment"].freeze_submission,
        submitted_exception_types=(),
    )

    class Policy:
        count = 0

        def act(self, observation):
            self.count += 1
            return AgentAction(f"action-{self.count}", "vaevas_docs_search", {"query": "resistor"},
                               "fixture", candidate_tree_sha256=observation.candidate_tree_sha256)

    args.update(policy=Policy(), tool_registry=ToolRegistry([tool.descriptor]),
                context=replace(args["context"], max_steps=3, budget_limits={"tool_calls": 1}))
    run = run_native_episode(**args)
    assert run.result.primary_outcome == "budget_exhausted"
    assert len([event for event in calls if event[0] == "tool_request"]) == 1
    budgets = [event["payload"] for event in read_trajectory(run.trajectory_path)
               if event["event_type"] == "budget_updated"]
    assert budgets[0]["delta"] == {"tool_calls": 1}
    assert run.artifact_path is None


@pytest.mark.parametrize("backend", ["native-mini-swe", "native-reasoning"])
def test_r53_docker_synthetic_docs_freeze_and_evas_score(tmp_path, backend):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker synthetic docs integration")
    from pathlib import Path
    from run_native_mini_swe import run_prepared_native_mini_swe
    from scripts import run_v4_r53_clean_room_smoke as smoke
    import score_campaign as scorer

    release = runner.DEFAULT_RELEASE
    corpus = synthetic_corpus(tmp_path / "corpus")
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(release, "v4-001"))
    cell = next(row for row in smoke.three_arm_cells(release, "v4-001", "fixture-model")
                if row["experimental_arm"] == "Agentic")
    runtime = tmp_path / "runtime"
    runner.export_runtime(cell, release, runtime, timeout_s=60)
    write = " && ".join(f"printf %s {shlex.quote(value)} > {shlex.quote('public/submission/' + name)}"
                        for name, value in artifacts.items())
    provider = Provider(["unused", write,
                         "evas simulate public/task/visible_test.scs -o /tmp/vabench-visible/evas-output --spectre-strict",
                         "vabench-submit"])
    original = provider.complete

    def complete(*args, **kwargs):
        response = original(*args, **kwargs)
        if len(provider.requests) == 1:
            response["choices"][0]["message"]["tool_calls"][0]["function"].update(
                name="vaevas_docs_search", arguments=json.dumps({"query": "resistor"}))
        return response

    provider.complete = complete
    run = run_prepared_native_mini_swe(
        runtime=runtime, cell=cell, client=provider, attempt_id="synthetic-docs-smoke",
        evas_command=str(Path(__file__).resolve().parents[1] / ".venv/bin/evas"),
        episode_backend=backend, docs_corpus=corpus, model_call_limit=4,
        campaign_file_sha256="c" * 64,
    )
    assert run.artifact_path is not None, run.result
    assert "SYNTHETIC_DOC" in json.dumps(provider.requests[1])
    row = scorer.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    assert row["submission_status"] == "submitted"
    assert row["extensions"]["offline_docs"]["profile_sha256"] == corpus.profile_sha256
    assert row["trusted_replay"]["final_test_profile"]["judge"] == {"engine": "evas", "version": "0.8.7"}
