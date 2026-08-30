"""Fresh attempts reuse the production native pipeline, never hidden feedback."""

import json
import shutil
from types import SimpleNamespace

import pytest

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401
from test_agent_harness_native_launcher import Provider
import run_campaign as runner
import score_campaign as scorer


@pytest.fixture
def attempt_case(native_case, tmp_path, monkeypatch):  # noqa: F811
    arguments, _, _ = native_case
    source = arguments["runtime"]
    cell = {
        "cell_id": "cell-001", "task_id": "v4-001", "family_id": "001",
        "mode": "G2", "base_mode": "G2", "form": "dut", "experimental_arm": "Agentic",
        "executable_feedback": True, "per_turn_max_tokens": 128,
    }

    def export(cell, release, runtime, **kwargs):
        shutil.copytree(source / "public/task", runtime / "public/task")
        shutil.copytree(source / "evaluator", runtime / "evaluator")
        (runtime / "public/submission").mkdir()
        (runtime / "agent_prompt.txt").write_text("Implement the public task.")

    monkeypatch.setattr(runner, "export_runtime", export)
    args = SimpleNamespace(
        output=tmp_path / "run", release=runner.DEFAULT_RELEASE,
        resume=False, dry_run=False, episode_backend="native-mini-swe",
        native_max_attempts=2, campaign_file_sha256="c" * 64,
        setup_timeout_s=10, request_timeout_s=10, tool_timeout_s=10,
        judge_timeout_s=10, agent_timeout_s=300,
        evas_command=arguments["evas_command"], final_judge_command=arguments["command"],
        allow_insecure_test_sandbox=True,
    )
    # The public production API uses argparse.Namespace.
    from argparse import Namespace
    return cell, Namespace(**vars(args))


def test_real_native_pipeline_retries_transport_with_fresh_lineage(attempt_case):
    cell, args = attempt_case
    clients = []

    def factory():
        client = Provider([
            "printf 'module model; endmodule\\n' > public/submission/model.va",
            "vabench-submit",
        ])
        if not clients:
            def fail(*args, **kwargs):
                raise TimeoutError("provider unavailable")
            client.complete = fail
        clients.append(client)
        return client

    result = runner.run_cell_preserving_failure(cell, args, None, client_factory=factory)
    assert result["attempt_count"] == 2
    assert len(clients) == 2
    assert result["status"] == "behavior_failure"
    attempts = result["attempt_sequence"]["attempts"]
    assert [item["retry_index"] for item in attempts] == [0, 1]
    assert attempts[1]["parent_attempt_id"] == attempts[0]["attempt_id"]
    root = args.output / cell["cell_id"]
    for item in attempts:
        runtime = root / item["cell_runtime"]
        events = [json.loads(line) for line in
                  (runtime / "evidence/native-episode/trajectory.jsonl").read_text().splitlines()]
        assert events[0]["attempt_id"] == item["attempt_id"]
        assert events[0]["payload"]["attempt_lineage"]["retry_index"] == item["retry_index"]
    assert not (root / attempts[0]["cell_runtime"] / "evidence/bound-final-test").exists()
    from run_native_attempts import retry_policy, read_native_attempt_sequence
    reread = read_native_attempt_sequence(
        root, cell, campaign_file_sha256="c" * 64, expected_retry_policy=retry_policy(2),
    )
    assert reread == result
    report = scorer.summarize([reread], "final_trusted_replay", scheduled_cells=[cell])
    assert report["cell_count"] == 1
    assert report["telemetry_by_arm"]["Agentic"]["model_calls_total"] == 3
    assert report["telemetry_by_arm"]["Agentic"]["output_tokens_total"] is None
    assert report["telemetry_by_arm"]["Agentic"]["output_tokens_reported_subtotal"] == 10
    assert len(clients) == 2  # scoring cannot run the provider or judge again


def test_real_protocol_failure_is_not_automatically_retried(attempt_case):
    cell, args = attempt_case
    clients = []

    def factory():
        client = Provider([])
        client.complete = lambda *a, **k: {
            "choices": [{"message": {"role": "assistant", "content": "no action"}}],
        }
        clients.append(client)
        return client

    result = runner.run_cell_preserving_failure(cell, args, None, client_factory=factory)
    assert result["attempt_count"] == 1
    assert result["status"] == "protocol_failure"
    assert len(clients) == 1


def test_preflight_timeout_retries_only_before_agent_deadline(attempt_case, monkeypatch):
    import mini_swe_vabench as mini

    cell, args = attempt_case
    original = mini.VaBenchBashEnvironment.preflight
    starts = []

    def preflight(self):
        starts.append(self.runtime)
        if len(starts) == 1:
            raise TimeoutError("fixture sandbox startup timeout")
        return original(self)

    monkeypatch.setattr(mini.VaBenchBashEnvironment, "preflight", preflight)
    result = runner.run_cell_preserving_failure(
        cell, args, None, client_factory=lambda: Provider([
            "printf 'module model; endmodule\\n' > public/submission/model.va",
            "vabench-submit",
        ]),
    )
    assert result["attempt_count"] == 2
    assert result["attempt_sequence"]["attempts"][0]["failure_category"] == "sandbox_startup"


def test_expired_agent_deadline_is_not_a_startup_retry(attempt_case, monkeypatch):
    import mini_swe_vabench as mini
    import run_native_mini_swe as launcher

    cell, args = attempt_case
    clock = [0.0]
    monkeypatch.setattr(launcher.time, "monotonic", lambda: clock[0])

    def preflight(self):
        clock[0] = 1e9
        raise TimeoutError("deadline exhausted")

    monkeypatch.setattr(mini.VaBenchBashEnvironment, "preflight", preflight)
    result = runner.run_cell_preserving_failure(
        cell, args, None, client_factory=lambda: Provider([]),
    )
    assert result["attempt_count"] == 1
    assert result["attempt_sequence"]["attempts"][0]["failure_category"] == "unknown"
