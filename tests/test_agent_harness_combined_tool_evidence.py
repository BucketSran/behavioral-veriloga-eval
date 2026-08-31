from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(CALIBRATION) not in sys.path:
    sys.path.insert(0, str(CALIBRATION))
MODULE_PATH = (
    CALIBRATION / "combined_tool_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("combined_tool_evidence_test_module", MODULE_PATH)
assert SPEC and SPEC.loader
combined = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(combined)

from runners.agent_harness import EpisodeContext, JsonlTrajectoryRecorder  # noqa: E402
from test_agent_harness_native_episode import native_case as native_case  # noqa: F401,E402
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401,E402


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _context(attempt: str = "attempt-1") -> EpisodeContext:
    return EpisodeContext(
        episode_id="episode-1",
        attempt_id=attempt,
        task_id="task-1",
        condition="Agentic",
        max_steps=4,
        budget_limits={},
    )


def _record(path: Path, event_type: str, payload: dict, *, context: EpisodeContext | None = None) -> str:
    if not hasattr(_record, "_recorders"):
        _record._recorders = {}  # type: ignore[attr-defined]
    recorders = _record._recorders  # type: ignore[attr-defined]
    if path not in recorders:
        recorders[path] = JsonlTrajectoryRecorder(path)
    recorder = recorders[path]
    return recorder.append(
        context=context or _context(),
        actor="fixture",
        event_type=event_type,
        visibility="trusted",
        payload=payload,
    )


def _native_run(tmp_path: Path) -> Path:
    run = tmp_path / "native-run"
    trajectory = run / "evidence/native-episode/trajectory.jsonl"
    private = run / "evidence/native-launcher/private-events.jsonl"
    _record(trajectory, "environment_observed", {
        "tool_name": "vaevas_docs_search",
        "observation": {"status": "succeeded", "payload": {"snippet": "RAW_DOC_SNIPPET"}},
    })
    _record(trajectory, "environment_observed", {
        "tool_name": "vaevas_public_simulate",
        "observation": {
            "status": "succeeded",
            "candidate_tree_sha256": SHA_A,
            "payload": {"receipt": {"receipt_sha256": SHA_B, "waveform": "RAW_WAVEFORM"}},
        },
    })
    _record(private, "provider_request", {"request_id": "req-1", "messages": [{"content": "initial"}]})
    _record(private, "provider_response", {"request_id": "req-1", "response": {"usage": {}}})
    _record(private, "tool_request", {"action_id": "act-doc", "tool_name": "vaevas_docs_search"})
    _record(private, "tool_result", {
        "action_id": "act-doc",
        "observation": {
            "observation_id": "act-doc/docs",
            "tool_name": "vaevas_docs_search",
            "status": "succeeded",
            "candidate_tree_sha256": SHA_A,
        },
    })
    _record(private, "tool_request", {"action_id": "act-wave", "tool_name": "vaevas_public_simulate"})
    _record(private, "tool_result", {
        "action_id": "act-wave",
        "observation": {
            "tool_name": "vaevas_public_simulate",
            "status": "succeeded",
            "observation_id": "act-wave/public-waveform",
            "candidate_tree_sha256": SHA_A,
            "payload": {"receipt": {"receipt_sha256": SHA_B}},
        },
    })
    _record(private, "provider_request", {
        "request_id": "req-false-tool-declaration",
        "messages": [{"content": "available tool: vaevas_public_simulate, public_validation"}],
        "tools": [{"function": {"name": "vaevas_public_simulate"}}],
    })
    _record(private, "provider_request", {
        "request_id": "req-2",
        "messages": [{
            "role": "tool",
            "content": json.dumps(
                {
                    "schema_version": "vaevas-reasoning-request-v1",
                    "observation": {
                        "tool_name": "vaevas_public_simulate",
                        "status": "succeeded",
                        "observation_id": "act-wave/public-waveform",
                        "candidate_tree_sha256": SHA_A,
                        "payload": {"receipt": {"receipt_sha256": SHA_B}},
                    },
                },
                sort_keys=True,
            ),
        }],
    })
    _record(private, "provider_response", {"request_id": "req-2", "response": {"usage": {}}})
    return run


def test_native_feature_use_counts_tools_and_exposure_without_raw_content(tmp_path: Path) -> None:
    run = _native_run(tmp_path)

    report = combined.collect_feature_use(run, backend="native-reasoning")

    assert report["backend"] == "native-reasoning"
    assert report["features"]["offline_docs"] == {
        "attempted": 1,
        "succeeded": 1,
        "feedback_exposed_requests": 0,
        "incomplete": [],
    }
    assert report["features"]["public_waveform"] == {
        "attempted": 1,
        "succeeded": 1,
        "feedback_exposed_requests": 1,
        "incomplete": [],
    }
    assert set(report["source"]["files"]) == {
        "evidence/native-episode/trajectory.jsonl",
        "evidence/native-launcher/private-events.jsonl",
    }
    dumped = json.dumps(report, sort_keys=True)
    assert "RAW_DOC_SNIPPET" not in dumped
    assert "RAW_WAVEFORM" not in dumped
    assert "feedback:" not in dumped
    assert report["claim_boundary"]["actual_model_consumption_claimed"] is False
    assert report["claim_boundary"]["actual_improvement_claimed"] is False


def test_native_feature_use_rejects_symlinked_roots_before_resolve(tmp_path: Path) -> None:
    real_run = _native_run(tmp_path)
    link = tmp_path / "linked-run"
    link.symlink_to(real_run, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        combined.collect_feature_use(link, backend="native-reasoning")


def test_native_feature_use_rejects_symlinked_evidence_paths(tmp_path: Path) -> None:
    run = _native_run(tmp_path)
    private = run / "evidence/native-launcher/private-events.jsonl"
    outside = tmp_path / "outside-private.jsonl"
    outside.write_bytes(private.read_bytes())
    private.unlink()
    private.symlink_to(outside)

    with pytest.raises(ValueError, match="symlink"):
        combined.collect_feature_use(run, backend="native-reasoning")


def test_native_feature_use_rejects_corrupt_event_chain(tmp_path: Path) -> None:
    run = _native_run(tmp_path)
    private = run / "evidence/native-launcher/private-events.jsonl"
    lines = private.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[-1])
    event["payload"]["request_id"] = "tampered"
    lines[-1] = json.dumps(event, sort_keys=True)
    private.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="event chain"):
        combined.collect_feature_use(run, backend="native-reasoning")


def test_evolution_feature_use_counts_receipts_and_next_round_exposure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = tmp_path / "evolution-run"
    branch0 = run / "evolution/branches/round-0000/branch-a"
    branch1 = run / "evolution/branches/round-0001/branch-a"
    for branch in (branch0, branch1):
        branch.mkdir(parents=True)
    request = {
        "schema_version": "vaevas-native-evolution-request-v1",
        "manifest_sha256": SHA_C,
        "config": {
            "rounds": 2,
            "branch_roster": [{"branch_id": "branch-a", "model_ref": "fixture"}],
        },
    }
    (run / "request.json").write_text(json.dumps(request, sort_keys=True), encoding="utf-8")
    _record(branch0 / "private-events.jsonl", "tool_request", {
        "action_id": "docs-1",
        "tool_name": "vaevas_docs_search",
    }, context=_context("round-0"))
    _record(branch0 / "private-events.jsonl", "tool_result", {
        "action_id": "docs-1",
        "observation": {
            "observation_id": "docs-1/docs",
            "tool_name": "vaevas_docs_search",
            "status": "succeeded",
            "candidate_tree_sha256": SHA_A,
        },
    }, context=_context("round-0"))
    _record(branch0 / "private-events.jsonl", "provider_request", {
        "request_id": "req-round0-docs",
        "messages": [{
            "content": json.dumps(
                {
                    "schema_version": "vaevas-reasoning-request-v1",
                    "observation": {
                        "observation_id": "docs-1/docs",
                        "tool_name": "vaevas_docs_search",
                        "status": "succeeded",
                        "candidate_tree_sha256": SHA_A,
                    },
                },
                sort_keys=True,
            )
        }],
    }, context=_context("round-0"))
    observation0 = {
        "tool_name": "vaevas_public_simulate",
        "status": "succeeded",
        "candidate_tree_sha256": SHA_B,
    }
    observation1 = {
        "tool_name": "vaevas_public_simulate",
        "status": "succeeded",
        "candidate_tree_sha256": SHA_A,
    }
    _record(branch1 / "private-events.jsonl", "provider_request", {
        "request_id": "req-false",
        "messages": [{"content": "generic public_validation " + combined.canonical_sha256(observation1)}],
    }, context=_context("round-1"))
    _record(branch1 / "private-events.jsonl", "provider_request", {
        "request_id": "req-next",
        "messages": [{
            "content": json.dumps(
                {
                    "prior_candidates": [
                        {
                            "candidate_tree_sha256": SHA_B,
                            "public_validation": {
                                "result": {
                                    "event_sha256": combined.canonical_sha256(observation0),
                                },
                            },
                        }
                    ]
                },
                sort_keys=True,
            )
        }],
    }, context=_context("round-1"))
    receipt0 = {
        "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
        "manifest_sha256": SHA_C,
        "branch_id": "branch-a",
        "round_index": 0,
        "candidate_tree_sha256": SHA_B,
        "candidate_store_sha256": SHA_A,
        "result": {"status": "succeeded", "sim_success": 1.0, "event_sha256": combined.canonical_sha256(observation0)},
        "observation": observation0,
    }
    receipt1 = {
        **receipt0,
        "round_index": 1,
        "candidate_tree_sha256": SHA_A,
        "candidate_store_sha256": SHA_B,
        "result": {"status": "succeeded", "sim_success": 1.0, "event_sha256": combined.canonical_sha256(observation1)},
        "observation": observation1,
    }
    (branch0 / "public-validation.json").write_text(json.dumps(receipt0, sort_keys=True), encoding="utf-8")
    (branch1 / "public-validation.json").write_text(json.dumps(receipt1, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(
        combined,
        "_validated_waveform_public_feedback_identity",
        lambda receipt, **_: (
            receipt["candidate_tree_sha256"],
            receipt["result"]["event_sha256"],
        ),
    )

    report = combined.collect_feature_use(run, backend="evolution")

    assert report["features"]["offline_docs"]["attempted"] == 1
    assert report["features"]["offline_docs"]["succeeded"] == 1
    assert report["features"]["offline_docs"]["feedback_exposed_requests"] == 1
    assert report["features"]["public_waveform"] == {
        "attempted": 2,
        "succeeded": 2,
        "feedback_exposed_requests": 1,
        "incomplete": [],
    }
    assert "evolution/branches/round-0000/branch-a/public-validation.json" in report["source"]["files"]


def test_evolution_ordinary_public_validation_does_not_count_as_waveform(tmp_path: Path) -> None:
    run = tmp_path / "ordinary-public-run"
    branch = run / "evolution/branches/round-0000/branch-a"
    branch.mkdir(parents=True)
    (run / "request.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-request-v1",
                "manifest_sha256": SHA_C,
                "config": {
                    "rounds": 1,
                    "branch_roster": [{"branch_id": "branch-a", "model_ref": "fixture"}],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _record(branch / "private-events.jsonl", "provider_request", {
        "request_id": "req-ordinary",
        "messages": [{"content": "ordinary public validation result"}],
    })
    (branch / "public-validation.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
                "manifest_sha256": SHA_C,
                "branch_id": "branch-a",
                "round_index": 0,
                "candidate_tree_sha256": SHA_A,
                "candidate_store_sha256": SHA_B,
                "result": {"status": "succeeded", "sim_success": 1.0, "event_sha256": SHA_B},
                "observation": None,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = combined.collect_feature_use(run, backend="evolution")

    assert report["features"]["public_waveform"] == {
        "attempted": 0,
        "succeeded": 0,
        "feedback_exposed_requests": 0,
        "incomplete": [],
    }


def test_evolution_waveform_receipt_requires_candidate_store(tmp_path: Path) -> None:
    run = tmp_path / "missing-store-run"
    branch = run / "evolution/branches/round-0000/branch-a"
    branch.mkdir(parents=True)
    (run / "request.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-request-v1",
                "manifest_sha256": SHA_C,
                "config": {
                    "rounds": 1,
                    "branch_roster": [{"branch_id": "branch-a", "model_ref": "fixture"}],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _record(branch / "private-events.jsonl", "provider_request", {
        "request_id": "req-waveform",
        "messages": [{"content": "waveform result exists"}],
    })
    observation = {
        "tool_name": "vaevas_public_simulate",
        "status": "succeeded",
        "candidate_tree_sha256": SHA_A,
    }
    (branch / "public-validation.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
                "manifest_sha256": SHA_C,
                "branch_id": "branch-a",
                "round_index": 0,
                "candidate_tree_sha256": SHA_A,
                "candidate_store_sha256": SHA_B,
                "result": {
                    "status": "succeeded",
                    "sim_success": 1.0,
                    "event_sha256": combined.canonical_sha256(observation),
                },
                "observation": observation,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="candidate store"):
        combined.collect_feature_use(run, backend="evolution")


def test_evolution_waveform_receipt_rejects_tampered_candidate_store(tmp_path: Path) -> None:
    run = tmp_path / "tampered-store-run"
    branch = run / "evolution/branches/round-0000/branch-a"
    store = branch / f"candidate-store/{SHA_A}"
    (store / "submission").mkdir(parents=True)
    (store / "submission/model.va").write_text("module tampered; endmodule\n", encoding="utf-8")
    store.mkdir(parents=True, exist_ok=True)
    (store / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-candidate-snapshot-v1",
                "tree_sha256": SHA_A,
                "artifacts": ["model.va"],
                "candidate_id": f"branch-a-round-0000-{SHA_A[:12]}",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (run / "request.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-request-v1",
                "manifest_sha256": SHA_C,
                "config": {
                    "rounds": 1,
                    "branch_roster": [{"branch_id": "branch-a", "model_ref": "fixture"}],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _record(branch / "private-events.jsonl", "provider_request", {
        "request_id": "req-waveform",
        "messages": [{"content": "waveform result exists"}],
    })
    observation = {
        "tool_name": "vaevas_public_simulate",
        "status": "succeeded",
        "candidate_tree_sha256": SHA_A,
    }
    (branch / "public-validation.json").write_text(
        json.dumps(
            {
                "schema_version": "vaevas-native-evolution-public-validation-receipt-v1",
                "manifest_sha256": SHA_C,
                "branch_id": "branch-a",
                "round_index": 0,
                "candidate_tree_sha256": SHA_A,
                "candidate_store_sha256": SHA_B,
                "result": {
                    "status": "succeeded",
                    "sim_success": 1.0,
                    "event_sha256": combined.canonical_sha256(observation),
                },
                "observation": observation,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="candidate store"):
        combined.collect_feature_use(run, backend="evolution")


def test_evolution_feature_use_reports_missing_files_as_incomplete(tmp_path: Path) -> None:
    run = tmp_path / "incomplete-evolution"
    branch = run / "evolution/branches/round-0000/branch-a"
    branch.mkdir(parents=True)
    request = {
        "schema_version": "vaevas-native-evolution-request-v1",
        "manifest_sha256": SHA_C,
        "config": {
            "rounds": 1,
            "branch_roster": [{"branch_id": "branch-a", "model_ref": "fixture"}],
        },
    }
    (run / "request.json").write_text(json.dumps(request, sort_keys=True), encoding="utf-8")

    report = combined.collect_feature_use(run, backend="evolution")

    assert report["features"]["offline_docs"] == {
        "attempted": None,
        "succeeded": None,
        "feedback_exposed_requests": None,
        "incomplete": ["evolution/branches/round-0000/branch-a/private-events.jsonl"],
    }
    assert report["features"]["public_waveform"]["attempted"] is None
    assert report["features"]["public_waveform"]["incomplete"] == [
        "evolution/branches/round-0000/branch-a/private-events.jsonl",
        "evolution/branches/round-0000/branch-a/public-validation.json"
    ]


def test_native_feature_use_reads_real_native_launcher_evidence(native_case, tmp_path: Path) -> None:  # noqa: F811
    from run_native_mini_swe import run_prepared_native_mini_swe
    from test_agent_harness_docs_integration import synthetic_corpus
    from test_agent_harness_native_conditions import _cell, _native_runtime
    from test_agent_harness_native_launcher import Provider

    corpus = synthetic_corpus(tmp_path / "corpus")
    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="combined-native")
    (runtime / "public/submission/model.va").write_text("module model; endmodule\n", encoding="utf-8")
    client = Provider(["unused", "vabench-submit"])
    original = client.complete

    def complete(messages, max_tokens, tools, **kwargs):
        response = original(messages, max_tokens, tools, **kwargs)
        message = response["choices"][0]["message"]
        function = message["tool_calls"][0]["function"]
        if len(client.requests) == 1:
            function.update(
                name="vaevas_docs_search",
                arguments=json.dumps({"query": "resistor", "top_k": 1}),
            )
        return response

    client.complete = complete
    run_prepared_native_mini_swe(
        runtime=runtime,
        cell={**_cell(arm="Agentic"), "family_id": "001"},
        client=client,
        attempt_id="combined-docs",
        evas_command=arguments["evas_command"],
        final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
        episode_backend="native-reasoning",
        reasoning_proposal_format="native_tool_calls",
        model_call_limit=2,
        campaign_file_sha256=SHA_C,
        docs_corpus=corpus,
    )

    report = combined.collect_feature_use(runtime, backend="native-reasoning")

    assert report["features"]["offline_docs"]["attempted"] == 1
    assert report["features"]["offline_docs"]["succeeded"] == 1
    assert report["features"]["offline_docs"]["feedback_exposed_requests"] == 1
    assert report["features"]["public_waveform"]["attempted"] == 0
    assert report["features"]["public_waveform"]["succeeded"] == 0


def test_evolution_feature_use_reads_real_evolution_engine_layout(tmp_path: Path) -> None:
    from test_agent_harness_native_evolution import (
        REASONING_BACKEND_SHA,
        _ScriptedReasoningClient,
        _fake_ops,
    )
    import run_native_evolution as evolution

    ops, *_ = _fake_ops(tmp_path)
    evolution.run_native_evolution(
        cell={
            "cell_id": "cell-1",
            "task_id": "task-1",
            "mode": "G2",
            "experimental_arm": "AlphaApollo-Evolution+EVAS",
        },
        release=tmp_path / "release",
        output_dir=tmp_path / "native-evolution",
        branches=[
            evolution.NativeEvolutionBranch(
                "branch-good",
                "provider/good",
                REASONING_BACKEND_SHA,
                lambda: _ScriptedReasoningClient(
                    "provider/good",
                    ["write", "vabench-submit"],
                ),
            )
        ],
        public_validation_profile=None,
        final_test_profile=None,
        command="fake-final",
        evas_command="fake-evas",
        rounds=2,
        max_steps=2,
        budgets={"model_calls": 3, "tool_calls": 3, "public_validation_calls": 1},
        ops=ops,
        max_workers=1,
    )

    report = combined.collect_feature_use(tmp_path / "native-evolution", backend="evolution")

    assert report["features"]["offline_docs"] == {
        "attempted": 0,
        "succeeded": 0,
        "feedback_exposed_requests": 0,
        "incomplete": [],
    }
    assert report["features"]["public_waveform"] == {
        "attempted": 0,
        "succeeded": 0,
        "feedback_exposed_requests": 0,
        "incomplete": [],
    }
    assert "evolution/branches/round-0001/branch-good/private-events.jsonl" in report["source"]["files"]
