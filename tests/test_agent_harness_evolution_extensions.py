"""Frozen Evolution branch surfaces and explicit synthetic interventions."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from test_agent_harness_native_evolution import (
    REASONING_BACKEND_SHA, _ScriptedReasoningClient, _fake_ops, evolution,
)


def _run(tmp_path, *, ops=None, **kwargs):
    if ops is None:
        ops = _fake_ops(tmp_path)[0]
    options = dict(
        cell={"cell_id": "cell-1", "task_id": "task-1", "mode": "G2",
              "experimental_arm": "AlphaApollo-Evolution+EVAS", "executable_feedback": True},
        release=tmp_path / "release", output_dir=tmp_path / "run",
        branches=[evolution.NativeEvolutionBranch(
            "branch-good", "provider/good", REASONING_BACKEND_SHA,
            lambda: _ScriptedReasoningClient("provider/good", ["write", "vabench-submit"]),
        )],
        command="fake-final", evas_command="fake-evas", rounds=1, max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops,
    )
    options.update(kwargs)
    return evolution.run_native_evolution(**options)


def test_branch_generation_export_is_no_evas_while_checkers_keep_original_cell(tmp_path):
    ops, final_calls, validation_calls, _, environments = _fake_ops(tmp_path)
    exports = []

    def export(cell, release, output, **kwargs):
        exports.append((output.name, deepcopy(cell)))
        ops.export_runtime(cell, release, output, **kwargs)

    cell = {"cell_id": "cell-1", "task_id": "task-1", "mode": "G2",
            "experimental_arm": "AlphaApollo-Evolution+EVAS", "executable_feedback": True}
    before = deepcopy(cell)
    run = _run(tmp_path, cell=cell, ops=replace(ops, export_runtime=export))
    assert cell == before
    by_path = dict(exports)
    assert by_path["runtime"]["experimental_arm"] == "Agent-No-EVAS"
    assert by_path["runtime"]["executable_feedback"] is False
    branch_environment = next(row for row in environments if row["branch"] is not None)
    assert branch_environment["cell"]["experimental_arm"] == "Agent-No-EVAS"
    assert branch_environment["context"].condition == before["experimental_arm"]
    assert by_path["public-validation-runtime"] == before
    assert by_path["final-runtime"] == before
    assert len(final_calls) == len(validation_calls) == 1
    config = json.loads((run.output_dir / "request.json").read_text())["config"]
    assert config["condition"] == before["experimental_arm"]
    assert config["branch_generation"]["exported_experimental_arm"] == "Agent-No-EVAS"
    branch = next((run.output_dir / "evolution/branches").glob("round-*/*/branch-runtime.json"))
    assert json.loads(branch.read_text())["exported_experimental_arm"] == "Agent-No-EVAS"


def test_real_r53_branch_export_has_no_evas_runtime_or_stale_private_spectre_claim(tmp_path):
    from test_agent_harness_evolution_campaign import _campaign
    from scripts import run_v4_r53_clean_room_smoke as smoke

    _, original = _campaign(tmp_path)
    cell = {**original, "experimental_arm": "AlphaApollo-Evolution+EVAS"}
    generation = evolution._branch_generation_cell(cell)
    branch_runtime = tmp_path / "branch"
    checker_runtime = tmp_path / "checker"
    evolution.runner.export_runtime(generation, smoke.DEFAULT_RELEASE, branch_runtime, timeout_s=30)
    evolution.runner.export_runtime(cell, smoke.DEFAULT_RELEASE, checker_runtime, timeout_s=30)
    assert not (branch_runtime / "public/task/evas_runtime.json").exists()
    assert (checker_runtime / "public/task/evas_runtime.json").is_file()
    policy = json.loads((branch_runtime / "MODEL_ACCESS_POLICY.json").read_text())
    assert policy["experimental_arm"] == "Agent-No-EVAS"
    assert "evas" not in policy["executables"]
    prompt = (branch_runtime / "agent_prompt.txt").read_text()
    assert "EVAS execution is not available" in prompt
    assert "final private Spectre judge" not in prompt
    assert "frozen submission" in prompt


class _DocsClient(_ScriptedReasoningClient):
    def __init__(self, model="provider/good"):
        super().__init__(model, ["docs", "write", "vabench-submit"])
        self.requests = []
        self.tools = []

    def complete(self, messages, max_tokens, tools, **kwargs):
        self.requests.append(deepcopy(messages))
        self.tools.append(deepcopy(tools))
        response = super().complete(messages, max_tokens, tools, **kwargs)
        if self.calls == 1:
            response["choices"][0]["message"]["tool_calls"][0]["function"] = {
                "name": "vaevas_docs_search", "arguments": json.dumps({"query": "resistor"}),
            }
        return response


def test_synthetic_docs_evolution_binds_profile_and_keeps_retrieval_branch_local(tmp_path):
    from test_agent_harness_docs_integration import synthetic_corpus
    from runners.agent_harness import read_trajectory
    from runners.agent_harness.tools.offline_docs_tool import docs_tool_descriptor

    corpus = synthetic_corpus(tmp_path / "corpus")
    clients = []

    def factory(model):
        client = _DocsClient(model)
        clients.append(client)
        return client

    branches = [evolution.NativeEvolutionBranch(
        name, name, REASONING_BACKEND_SHA, lambda name=name: factory(name),
    ) for name in ("branch-good", "branch-other")]
    run = _run(tmp_path, docs_corpus=corpus, branches=branches, rounds=2, max_steps=3)
    assert len(clients) == 4
    for client in clients:
        assert {tool["function"]["name"] for tool in client.tools[0]} == {"bash", "vaevas_docs_search"}
        assert corpus.profile_sha256 in json.dumps(client.requests[0])
        assert "SYNTHETIC_DOC" not in json.dumps(client.requests[0])
        assert "SYNTHETIC_DOC" in json.dumps(client.requests[1])
        assert "final_judgment" not in json.dumps(client.requests)
    config = json.loads((run.output_dir / "request.json").read_text())["config"]
    docs = config["extensions"]["offline_docs"]
    assert docs == {"intervention": "synthetic-frozen-docs-v1", "tool_name": "vaevas_docs_search",
                    "profile": corpus.profile, "profile_sha256": corpus.profile_sha256}
    assert json.loads((run.output_dir / "request.json").read_text())["campaign_config_sha256"] == evolution._canonical_sha256(config)
    final = json.loads((run.output_dir / "final-result.json").read_text())
    assert final["extensions"] == config["extensions"]
    assert final["claim_boundary"]["single_trajectory_pooling_allowed"] is False
    assert final["claim_boundary"]["model_quality_claim_allowed"] is False
    for key, value in {"model_calls": 12, "tool_calls": 12, "public_validation_calls": 4}.items():
        assert run.evolution_result.usage[key] == value
        assert run.evolution_result.usage[key + "_unknown_count"] == 0
    for branch in (run.output_dir / "evolution/branches").glob("round-*/*"):
        events = read_trajectory(branch / "private-events.jsonl")
        observation = next(event["payload"]["observation"] for event in events
                           if event["event_type"] == "tool_result"
                           and event["payload"]["observation"]["tool_name"] == "vaevas_docs_search")
        assert observation["payload"]["corpus_profile_sha256"] == corpus.profile_sha256
    memory = json.dumps(run.evolution_result.memory_snapshots, default=dict)
    assert "vaevas_docs_search" not in memory and "SYNTHETIC_DOC" not in memory
    descriptor = docs_tool_descriptor(corpus.profile, condition="AlphaApollo-Evolution+EVAS")
    assert descriptor["evidence_policy"]["may_enter_shared_memory"] is False


@pytest.mark.parametrize("condition", ["Agentic", "Evolution+EVAS", "OneShot"])
def test_evolution_docs_require_exact_condition_before_output_reservation(tmp_path, condition):
    from test_agent_harness_docs_integration import synthetic_corpus
    corpus = synthetic_corpus(tmp_path / "corpus")
    with pytest.raises(ValueError, match="AlphaApollo-Evolution"):
        _run(tmp_path, docs_corpus=corpus, cell={"experimental_arm": condition})
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize("row", [
    {"experimental_arm": "AlphaApollo-Evolution+EVAS"},
    {"claim_boundary": {"single_trajectory_pooling_allowed": False}},
])
def test_ordinary_summary_rejects_evolution_rows_even_without_docs(row):
    import score_campaign
    with pytest.raises(ValueError, match="Evolution"):
        score_campaign.summarize([row], "final_trusted_replay")


def test_evolution_docs_bad_input_fails_before_output_reservation(tmp_path):
    with pytest.raises(TypeError, match="OfflineDocsCorpus"):
        _run(tmp_path, docs_corpus={"profile_sha256": "a" * 64})
    assert not (tmp_path / "run").exists()


def test_evolution_docs_consume_the_shared_tool_budget(tmp_path):
    from test_agent_harness_docs_integration import synthetic_corpus
    from runners.agent_harness import read_trajectory
    corpus = synthetic_corpus(tmp_path / "corpus")
    with pytest.raises(RuntimeError, match="no selected candidate"):
        _run(tmp_path, docs_corpus=corpus, max_steps=3,
             branches=[evolution.NativeEvolutionBranch("branch-good", "provider/good",
                        REASONING_BACKEND_SHA, _DocsClient)],
             budgets={"model_calls": 3, "tool_calls": 1, "public_validation_calls": 1})
    branch = next((tmp_path / "run/evolution/branches").glob("round-*/*"))
    events = read_trajectory(branch / "private-events.jsonl")
    requests = [event["payload"]["tool_name"] for event in events if event["event_type"] == "tool_request"]
    assert requests == ["vaevas_docs_search"]
    assert not (branch / "runtime/public/submission/model.va").exists()
