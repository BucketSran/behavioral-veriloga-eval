from __future__ import annotations

from argparse import Namespace
import hashlib
import json
from pathlib import Path
import sys

import pytest

from runners.agent_harness.attempt_sequence import RetryPolicy


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))

import run_native_attempts as attempts  # noqa: E402


CAMPAIGN_SHA = "c" * 64


@pytest.mark.parametrize("marker", ["trusted_replay_result.json", "bound-final-test"])
@pytest.mark.parametrize("broken_link", [False, True])
def test_terminal_marker_or_broken_reservation_blocks_retry(tmp_path, marker, broken_link):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    path = evidence / marker
    if broken_link:
        path.symlink_to(evidence / "missing")
    else:
        path.write_text("{}")
    assert attempts._has_post_freeze_or_cleanup_evidence(tmp_path)


def _cell() -> dict:
    return {
        "cell_id": "cell-001",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "base_mode": "G2",
        "experimental_arm": "Agentic",
        "executable_feedback": True,
    }


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        output=tmp_path / "campaign",
        campaign_file_sha256=CAMPAIGN_SHA,
        resume=True,
        native_max_attempts=9,
    )


def _policy(max_attempts: int = 2) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=max_attempts,
        retry_categories=frozenset({"provider_transport", "sandbox_startup"}),
    )


class _Client:
    def __init__(self, name: str) -> None:
        self.name = name


class _Runner:
    def __init__(self, statuses: list[str]) -> None:
        self.statuses = iter(statuses)
        self.calls: list[dict] = []

    def run_cell_preserving_failure(self, cell: dict, args: Namespace, client: _Client) -> dict:
        status = next(self.statuses)
        assert args.output.is_dir()
        assert args.resume is False
        assert args.native_max_attempts == 1
        assert args._native_attempt_context.attempt_id
        runtime = args.output / cell["cell_id"]
        runtime.mkdir()
        launcher = runtime / "evidence/native-launcher"
        episode = runtime / "evidence/native-episode"
        launcher.mkdir(parents=True)
        episode.mkdir(parents=True)
        lineage = _lineage(args._native_attempt_context)
        (launcher / "manifest.json").write_text(
            json.dumps(
                {
                    "attempt_id": args._native_attempt_context.attempt_id,
                    "attempt_lineage": lineage,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (episode / "trajectory.jsonl").write_text(
            json.dumps(
                {"event_type": "episode_started", "payload": {"attempt_lineage": lineage}},
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (runtime / "marker.txt").write_text(
            f"{status}:{client.name}:{args._native_attempt_context.attempt_id}",
            encoding="utf-8",
        )
        private = launcher / "private-events.jsonl"
        if status in {"provider_transport", "provider_transport_sandbox_cleanup_failure"}:
            private.write_text(
                json.dumps(
                    {
                        "event_type": "provider_failure",
                        "payload": {"error_type": "TimeoutError"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
        elif status == "provider_transport_cleanup":
            private.write_text(
                json.dumps(
                    {
                        "event_type": "provider_failure",
                        "payload": {"error_type": "TimeoutError"},
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "event_type": "launcher_cleanup_failed",
                        "payload": {"error_type": "RuntimeError"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            private.write_text("", encoding="utf-8")
        if status == "provider_transport_after_freeze":
            private.write_text(
                json.dumps(
                    {
                        "event_type": "provider_failure",
                        "payload": {"error_type": "TimeoutError"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "evidence/final_submission").mkdir(parents=True)
        if status == "provider_transport_after_final":
            private.write_text(
                json.dumps(
                    {
                        "event_type": "provider_failure",
                        "payload": {"error_type": "TimeoutError"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "evidence/bound-final-test").mkdir(parents=True)
        if status == "provider_transport_trusted_marker":
            private.write_text(
                json.dumps(
                    {
                        "event_type": "provider_failure",
                        "payload": {"error_type": "TimeoutError"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "evidence/trusted_replay").mkdir(parents=True)
        self.calls.append(
            {
                "cell": dict(cell),
                "output": args.output,
                "runtime": runtime,
                "context": args._native_attempt_context,
                "client": client,
                "status": status,
            }
        )
        return {"status": status}


class _Scorer:
    def __init__(self, runner: _Runner) -> None:
        self.runner = runner
        self.calls: list[Path] = []

    def read_native_cell(
        self,
        runtime: Path,
        cell: dict,
        *,
        campaign_file_sha256: str,
    ) -> dict:
        assert cell == _cell()
        assert campaign_file_sha256 == CAMPAIGN_SHA
        self.calls.append(runtime)
        status = (runtime / "marker.txt").read_text(encoding="utf-8").split(":")[0]
        common = {
            **{
                key: cell[key]
                for key in (
                    "cell_id",
                    "task_id",
                    "family_id",
                    "form",
                    "mode",
                    "experimental_arm",
                )
            },
            "backend": "native-mini-swe",
            "attempt_id": runtime.parent.parent.name,
            "output_tokens": None,
            "telemetry": {"model_calls": None},
            "metering": {
                "provider": {
                    "requests": None,
                    "usage": {"completion_tokens": None},
                    "usage_status": "unknown",
                },
                "tools": {"requests": None},
            },
            "evas_usage": {"calls_executed": None},
        }
        if status == "pass":
            return {
                **common,
                "submission_status": "submitted",
                "judge_status": "passed",
                "outcome": "passed",
                "score": 1,
                "termination_reason": "submitted",
                "terminal_reason": "submitted",
                "incidents": [],
                "trusted_replay": {"status": "passed"},
            }
        if status == "provider_transport":
            return {
                **common,
                "submission_status": "not_submitted",
                "judge_status": "infrastructure_failure",
                "outcome": "infrastructure_failure",
                "score": None,
                "termination_reason": "provider_transport_failure",
                "terminal_reason": "provider_transport_failure",
                "incidents": [{"category": "backend_failure"}],
            }
        if status in {
            "provider_transport_cleanup",
            "provider_transport_after_freeze",
            "provider_transport_after_final",
            "provider_transport_trusted_marker",
        }:
            return {
                **common,
                "submission_status": "not_submitted",
                "judge_status": "infrastructure_failure",
                "outcome": "infrastructure_failure",
                "score": None,
                "termination_reason": "provider_transport_failure",
                "terminal_reason": "provider_transport_failure",
                "incidents": [{"category": "backend_failure"}],
            }
        if status == "provider_transport_sandbox_cleanup_failure":
            return {
                **common,
                "submission_status": "not_submitted",
                "judge_status": "infrastructure_failure",
                "outcome": "infrastructure_failure",
                "score": None,
                "termination_reason": "provider_transport_failure",
                "terminal_reason": "provider_transport_failure",
                "incidents": [{"category": "sandbox_cleanup_failure"}],
            }
        if status == "sandbox_startup":
            return {
                **common,
                "submission_status": "not_submitted",
                "judge_status": "infrastructure_failure",
                "outcome": "infrastructure_failure",
                "score": None,
                "termination_reason": "sandbox_startup",
                "terminal_reason": "sandbox_startup",
                "incidents": [{"category": "sandbox_startup"}],
            }
        return {
            **common,
            "submission_status": "not_submitted",
            "judge_status": "infrastructure_failure",
            "outcome": "infrastructure_failure",
            "score": None,
            "termination_reason": "cleanup_failed",
            "terminal_reason": "cleanup_failed",
            "incidents": [{"category": "cleanup"}],
        }


def _install(monkeypatch: pytest.MonkeyPatch, runner: _Runner) -> _Scorer:
    scorer = _Scorer(runner)
    monkeypatch.setattr(attempts, "runner", runner)
    monkeypatch.setattr(attempts, "scorer", scorer)
    return scorer


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _lineage(context: object) -> dict:
    return {
        "parent_attempt_id": context.parent_attempt_id,
        "retry_index": context.retry_index,
        "retry_reason": context.retry_reason,
    }


def _rewrite_attempt_receipt_hashes(root: Path, attempt_id: str) -> None:
    attempt_path = root / attempt_id / "attempt.json"
    receipt = json.loads(attempt_path.read_text(encoding="utf-8"))
    receipt["outcome_sha256"] = _canonical_sha256(receipt["outcome"])
    attempt_sha256 = _canonical_sha256(receipt)
    attempt_path.chmod(0o644)
    attempt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    selection_path = root / "selection.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    for row in selection["attempt_receipts"]:
        if row["attempt_id"] == attempt_id:
            row["receipt_sha256"] = attempt_sha256
            row["outcome_sha256"] = receipt["outcome_sha256"]
    if selection["selected_attempt_id"] == attempt_id:
        selection["selected_attempt_receipt_sha256"] = attempt_sha256
    selection_path.chmod(0o644)
    selection_path.write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_attempt_source_hashes(root: Path, attempt_id: str) -> None:
    attempt_path = root / attempt_id / "attempt.json"
    receipt = json.loads(attempt_path.read_text(encoding="utf-8"))
    cell_runtime = root / receipt["runtime_path"] / _cell()["cell_id"]
    receipt["outcome"]["evidence"]["source_hashes"] = attempts.source_hashes(cell_runtime)
    attempt_path.chmod(0o644)
    attempt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_attempt_receipt_hashes(root, attempt_id)


def test_native_attempt_sequence_retries_provider_transport_with_fresh_runtime_and_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["provider_transport", "pass"])
    scorer = _install(monkeypatch, runner)
    client_names = iter(["client-1", "client-2"])

    result = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client(next(client_names)),
        retry_policy=_policy(),
    )

    assert result["status"] == "passed"
    assert result["attempt_id"] == "cell-001-attempt-0001-retry-0001"
    assert result["attempt_count"] == 2
    assert [call["client"].name for call in runner.calls] == ["client-1", "client-2"]
    assert [call["context"].retry_index for call in runner.calls] == [0, 1]
    assert runner.calls[0]["runtime"] != runner.calls[1]["runtime"]
    assert runner.calls[0]["runtime"].relative_to(tmp_path / "campaign" / "cell-001")
    assert scorer.calls[:2] == [call["runtime"] for call in runner.calls]
    reread = attempts.read_native_attempt_sequence(
        tmp_path / "campaign" / "cell-001",
        _cell(),
        campaign_file_sha256=CAMPAIGN_SHA,
        expected_retry_policy=_policy(),
    )
    assert reread == result
    assert len(runner.calls) == 2


def test_native_attempt_sequence_resume_reuses_completed_selection_without_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    first = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("first"),
        retry_policy=_policy(),
    )
    assert len(runner.calls) == 1

    reread_runner = _Runner([])
    _install(monkeypatch, reread_runner)
    resumed = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: pytest.fail("completed native resume must not create a client"),
        retry_policy=_policy(),
        resume=True,
    )

    assert resumed == first
    assert reread_runner.calls == []


def test_native_attempt_resume_preflight_validates_existing_prefix_without_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("first"),
        retry_policy=_policy(),
    )

    root = tmp_path / "campaign" / "cell-001"
    validation = attempts.validate_native_attempt_resume(
        root,
        _cell(),
        campaign_file_sha256=CAMPAIGN_SHA,
        expected_retry_policy=_policy(),
    )

    assert validation["complete"] is True
    assert validation["resumable"] is False
    assert validation["attempt_count"] == 1
    assert validation["attempts"][0]["attempt_id"] == "cell-001-attempt-0001"


def test_native_attempt_sequence_resume_continues_after_retryable_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _interrupted_native_prefix(tmp_path, monkeypatch)
    policy = _policy(max_attempts=2)

    validation = attempts.validate_native_attempt_resume(
        root,
        _cell(),
        campaign_file_sha256=CAMPAIGN_SHA,
        expected_retry_policy=policy,
    )
    assert validation["complete"] is False
    assert validation["next_attempt_id"] == "cell-001-attempt-0001-retry-0001"

    resumed_runner = _Runner(["pass"])
    _install(monkeypatch, resumed_runner)
    resumed = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("second"),
        retry_policy=policy,
        resume=True,
    )

    assert resumed["status"] == "passed"
    assert resumed["attempt_count"] == 2
    assert [call["context"].attempt_id for call in resumed_runner.calls] == [
        "cell-001-attempt-0001-retry-0001"
    ]


def _interrupted_native_prefix(tmp_path, monkeypatch):
    from runners.agent_harness import attempt_sequence as sequence
    original_reserve = sequence._reserve_attempt_runtime

    def interrupt_before_next(root, attempt_id):
        if "-retry-" in attempt_id:
            raise KeyboardInterrupt("process stopped after sealed first receipt")
        return original_reserve(root, attempt_id)

    _install(monkeypatch, _Runner(["provider_transport"]))
    with monkeypatch.context() as patch:
        patch.setattr(sequence, "_reserve_attempt_runtime", interrupt_before_next)
        with pytest.raises(KeyboardInterrupt):
            attempts.run_native_attempt_sequence(
                cell=_cell(), args=_args(tmp_path), client_factory=lambda: _Client("first"),
                retry_policy=_policy())
    return tmp_path / "campaign" / "cell-001"


def test_native_resume_validates_prior_source_before_creating_next_client(tmp_path, monkeypatch):
    root = _interrupted_native_prefix(tmp_path, monkeypatch)
    marker = root / "cell-001-attempt-0001/runtime/cell-001/marker.txt"
    marker.write_text(marker.read_text() + "\nchanged")
    clients = []
    _install(monkeypatch, _Runner(["pass"]))

    def client():
        clients.append(True)
        return _Client("second")

    with pytest.raises(ValueError, match="source hash"):
        attempts.run_native_attempt_sequence(
            cell=_cell(), args=_args(tmp_path), client_factory=client,
            retry_policy=_policy(), resume=True)
    assert clients == []


def test_native_attempt_sequence_retries_typed_sandbox_startup_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["sandbox_startup", "pass"])
    _install(monkeypatch, runner)

    result = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    assert result["status"] == "passed"
    assert result["attempt_count"] == 2
    assert result["attempt_sequence"]["attempts"][0]["failure_category"] == "sandbox_startup"


def test_native_attempt_sequence_does_not_retry_cleanup_or_unknown_infrastructure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["cleanup_failed", "pass"])
    _install(monkeypatch, runner)

    result = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("only"),
        retry_policy=_policy(),
    )

    assert result["status"] == "infrastructure_failure"
    assert result["attempt_count"] == 1
    assert len(runner.calls) == 1
    assert result["attempt_sequence"]["attempts"][0]["failure_category"] == "unknown"


@pytest.mark.parametrize(
    "status",
    [
        "provider_transport_cleanup",
        "provider_transport_sandbox_cleanup_failure",
        "provider_transport_after_freeze",
        "provider_transport_after_final",
        "provider_transport_trusted_marker",
    ],
)
def test_native_attempt_sequence_does_not_retry_after_cleanup_freeze_or_final_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    runner = _Runner([status, "pass"])
    _install(monkeypatch, runner)

    result = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("only"),
        retry_policy=_policy(),
    )

    assert result["status"] == "infrastructure_failure"
    assert result["attempt_count"] == 1
    assert len(runner.calls) == 1
    assert result["attempt_sequence"]["attempts"][0]["failure_category"] == "unknown"


def test_native_attempt_reader_rejects_source_tamper_and_selection_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["provider_transport", "pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    root = tmp_path / "campaign" / "cell-001"
    marker = root / "cell-001-attempt-0001-retry-0001/runtime/cell-001/marker.txt"
    marker.write_text(marker.read_text(encoding="utf-8") + "\ntamper", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )

    fresh = tmp_path / "fresh"
    runner = _Runner(["provider_transport", "pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(fresh),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )
    root = fresh / "campaign" / "cell-001"
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    selection["selected_attempt_id"] = "cell-001-attempt-0001"
    path = root / "selection.json"
    path.chmod(0o644)
    path.write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="attempt sequence"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )


def test_native_attempt_reader_uses_verified_runtime_path_not_outcome_evidence_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    scorer = _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    root = tmp_path / "campaign" / "cell-001"
    attempt_id = "cell-001-attempt-0001"
    receipt_path = root / attempt_id / "attempt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["outcome"]["evidence"]["cell_runtime"] = "attacker-controlled/cell-001"
    receipt_path.chmod(0o644)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_attempt_receipt_hashes(root, attempt_id)

    with pytest.raises(ValueError, match="cell runtime"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )
    assert not any("attacker-controlled" in str(call) for call in scorer.calls)


def test_native_attempt_reader_rejects_manifest_or_trajectory_lineage_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    root = tmp_path / "campaign" / "cell-001"
    attempt_id = "cell-001-attempt-0001"
    runtime = root / attempt_id / "runtime/cell-001"
    manifest_path = runtime / "evidence/native-launcher/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["attempt_lineage"]["retry_index"] = 9
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_attempt_source_hashes(root, attempt_id)

    with pytest.raises(ValueError, match="attempt lineage"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )

    fresh = tmp_path / "fresh-lineage"
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(fresh),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )
    root = fresh / "campaign" / "cell-001"
    runtime = root / attempt_id / "runtime/cell-001"
    trajectory_path = runtime / "evidence/native-episode/trajectory.jsonl"
    event = json.loads(trajectory_path.read_text(encoding="utf-8").splitlines()[0])
    event["payload"]["attempt_lineage"]["retry_reason"] = "wrong-reason"
    trajectory_path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_attempt_source_hashes(root, attempt_id)

    with pytest.raises(ValueError, match="attempt lineage"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )


def test_native_attempt_reader_rejects_native_row_sidecar_or_identity_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    root = tmp_path / "campaign" / "cell-001"
    native_row_path = root / "cell-001-attempt-0001/native-row.json"
    native_row = json.loads(native_row_path.read_text(encoding="utf-8"))
    native_row["row"]["attempt_id"] = "wrong-attempt"
    native_row["row_sha256"] = _canonical_sha256(native_row["row"])
    native_row_path.chmod(0o644)
    native_row_path.write_text(json.dumps(native_row, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="native row"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )

    fresh = tmp_path / "fresh-row"
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(fresh),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )
    root = fresh / "campaign" / "cell-001"
    native_row_path = root / "cell-001-attempt-0001/native-row.json"
    native_row = json.loads(native_row_path.read_text(encoding="utf-8"))
    native_row["row"]["score"] = 999
    native_row_path.chmod(0o644)
    native_row_path.write_text(json.dumps(native_row, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="native row"):
        attempts.read_native_attempt_sequence(
            root,
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=_policy(),
        )


def test_native_attempt_reader_rejects_retry_policy_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["pass"])
    _install(monkeypatch, runner)
    attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    with pytest.raises(ValueError, match="retry policy"):
        attempts.read_native_attempt_sequence(
            tmp_path / "campaign" / "cell-001",
            _cell(),
            campaign_file_sha256=CAMPAIGN_SHA,
            expected_retry_policy=RetryPolicy(
                max_attempts=1,
                retry_categories=frozenset({"provider_transport"}),
            ),
        )


def test_source_hash_helper_changes_when_runtime_file_changes(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "a.txt").write_text("a", encoding="utf-8")
    before = attempts.source_hashes(runtime)
    (runtime / "a.txt").write_text("b", encoding="utf-8")
    after = attempts.source_hashes(runtime)
    assert before != after
    assert before["files"]["a.txt"] == hashlib.sha256(b"a").hexdigest()


def test_attempt_costs_use_evas_calls_executed_and_preserve_all_attempt_unknowns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner(["provider_transport", "pass"])
    _install(monkeypatch, runner)

    result = attempts.run_native_attempt_sequence(
        cell=_cell(),
        args=_args(tmp_path),
        client_factory=lambda: _Client("fresh"),
        retry_policy=_policy(),
    )

    costs = [attempt["costs"] for attempt in result["attempt_sequence"]["attempts"]]
    assert len(costs) == 2
    expected_unknown_costs = {
        "provider_requests": None,
        "tool_requests": None,
        "output_tokens": None,
        "evas_invocations": None,
    }
    assert costs == [
        expected_unknown_costs,
        expected_unknown_costs,
    ]
    assert result["selected_costs"] == expected_unknown_costs
    assert result["attempt_costs"] == {
        "schema_version": "vaevas-native-attempt-costs-v1",
        "selected_attempt_id": "cell-001-attempt-0001-retry-0001",
        "selected_costs": expected_unknown_costs,
        "summary": {
            "provider_requests": {
                "total": None,
                "reported_subtotal": 0,
                "unknown_attempts": 2,
            },
            "tool_requests": {
                "total": None,
                "reported_subtotal": 0,
                "unknown_attempts": 2,
            },
            "output_tokens": {
                "total": None,
                "reported_subtotal": 0,
                "unknown_attempts": 2,
            },
            "evas_invocations": {
                "total": None,
                "reported_subtotal": 0,
                "unknown_attempts": 2,
            },
        },
        "attempts": [
            {"attempt_id": "cell-001-attempt-0001", "costs": expected_unknown_costs},
            {"attempt_id": "cell-001-attempt-0001-retry-0001", "costs": expected_unknown_costs},
        ],
    }
