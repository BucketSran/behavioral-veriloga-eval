"""Native mini-swe campaign dispatch and strict native score accounting."""

from __future__ import annotations

import json
import hashlib
from argparse import Namespace
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
WRAPPER = ROOT / "benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py"
sys.path.insert(0, str(CALIBRATION))

import run_campaign as runner  # noqa: E402
import score_campaign as scorer  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("form,task_id", [("dut", "v4-001"), ("testbench", "v4-501")])
def test_wrapper_dry_run_records_native_episode_backend_without_legacy_fallback(
    tmp_path: Path, form: str, task_id: str,
) -> None:
    output = tmp_path / "native-campaign"
    completed = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--output-root",
            str(output),
            "--model",
            "fixture-model",
            "--task-id",
            task_id,
            "--form",
            form,
            "--comparison-profile",
            "executable-feedback-control",
            "--episode-backend",
            "native-mini-swe",
            "--native-max-attempts", "2",
            "--dry-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    campaign = read_json(output / "campaign.json")
    execution = campaign["execution_config"]
    assert execution["episode_backend"] == "native-mini-swe"
    assert execution["agent_scaffold"] == "mini-swe"
    assert execution["native_retry_policy"]["max_attempts"] == 2
    assert {cell["experimental_arm"] for cell in campaign["cells"]} == {
        "OneShot",
        "Agent-No-EVAS",
        "Agentic",
    }

    summary = read_json(output / "wrapper_summary.json")
    command = summary["command"]
    assert "--episode-backend" in command
    assert command[command.index("--episode-backend") + 1] == "native-mini-swe"
    assert command[command.index("--native-max-attempts") + 1] == "2"
    assert "--agent-scaffold" in command
    assert command[command.index("--agent-scaffold") + 1] == "mini-swe"


@pytest.mark.parametrize(
    ("extra_args", "message"),
    [
        (["--agent-scaffold", "native"], "agent-scaffold"),
        (["--limit", "1"], "limit"),
        (["--resume"], "resume"),
    ],
)
def test_wrapper_rejects_unfrozen_native_campaign_combinations(
    tmp_path: Path, extra_args: list[str], message: str
) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--output-root",
            str(tmp_path / "native-campaign"),
            "--model",
            "fixture-model",
            "--task-id",
            "v4-001",
            "--comparison-profile",
            "executable-feedback-control",
            "--episode-backend",
            "native-mini-swe",
            "--dry-run",
            *extra_args,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    assert completed.returncode != 0
    assert message in completed.stderr or message in completed.stdout


@pytest.mark.parametrize(
    ("arm", "mode", "process", "feedback", "expected_image"),
    [
        ("OneShot", "G0", "direct", False, None),
        ("Agent-No-EVAS", "G2", "agentic", False, "image:no-evas"),
        ("Agentic", "G2", "agentic", True, "image:evas"),
    ],
)
def test_run_campaign_native_backend_dispatches_prepared_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arm: str,
    mode: str,
    process: str,
    feedback: bool,
    expected_image: str | None,
) -> None:
    cell = {
        "cell_id": f"v4-001-{mode}-r00-{arm.lower().replace('-', '')}",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": mode,
        "process": process,
        "experimental_arm": arm,
        "base_mode": mode,
        "executable_feedback": feedback,
        "per_turn_max_tokens": 128,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
        allow_insecure_test_sandbox=True,
    )
    client = SimpleNamespace(model="fixture-model")
    calls: list[dict] = []

    def fake_export(observed_cell, release, runtime, *, timeout_s):
        assert observed_cell == cell
        assert release == runner.DEFAULT_RELEASE
        assert runtime == tmp_path / cell["cell_id"]
        assert timeout_s == 10
        (runtime / "evidence").mkdir(parents=True)

    def fake_launch(**kwargs):
        calls.append(kwargs)
        (kwargs["runtime"] / "evidence/native-launcher").mkdir(parents=True)
        return SimpleNamespace(
            result=SimpleNamespace(
                primary_outcome="behavior_failure",
                terminal_reason="submitted",
            ),
            artifact_path=kwargs["runtime"] / "evidence/native-episode/scored-results/a.json",
            score_sidecar_receipt={"sha256": "a" * 64},
        )

    monkeypatch.setattr(runner, "export_runtime", fake_export)
    monkeypatch.setattr(runner, "run_prepared_native_mini_swe", fake_launch)

    result = runner.run_cell(cell, args, client)

    assert result["backend"] == "native-mini-swe"
    assert result["status"] == "behavior_failure"
    assert result["termination_reason"] == "submitted"
    assert result["cell"] == cell
    assert len(calls) == 1
    call = calls[0]
    assert call["runtime"] == tmp_path / cell["cell_id"]
    assert call["cell"] == cell
    assert call["client"] is client
    assert call["attempt_id"] == f"{cell['cell_id']}-attempt-0001"
    assert call["campaign_file_sha256"] is None
    assert call["evas_command"] == "/usr/bin/evas-fixture"
    assert call["final_judge_command"] == "/usr/bin/final-fixture"
    assert call["docker_image"] == expected_image
    assert not (tmp_path / cell["cell_id"] / "evidence/campaign_result.json").exists()


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"form": "unsupported"}, "DUT/bugfix/Testbench"),
        ({"experimental_arm": None}, "experimental arm"),
        ({"experimental_arm": "Agentic", "mode": "G3"}, "experimental arm"),
    ],
)
def test_run_campaign_native_backend_rejects_unsupported_cells_before_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict,
    message: str,
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
        "per_turn_max_tokens": 128,
        **override,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
    )
    exported = False

    def fake_export(*args, **kwargs):
        nonlocal exported
        exported = True

    monkeypatch.setattr(runner, "export_runtime", fake_export)

    with pytest.raises(ValueError, match=message):
        runner.run_cell(cell, args, SimpleNamespace(model="fixture-model"))
    assert exported is False


def test_score_campaign_native_backend_reads_frozen_schedule_without_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
    }
    campaign = {"schema_version": "fixture", "cells": [cell]}
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps(campaign, sort_keys=True), encoding="utf-8")
    run_root = tmp_path / "run"
    run_root.mkdir()
    output = tmp_path / "score.json"
    calls: list[tuple[Path, dict, str]] = []

    def fake_read_native_cell(runtime, scheduled_cell, *, campaign_file_sha256):
        calls.append((runtime, scheduled_cell, campaign_file_sha256))
        return {
            **scheduled_cell,
            "backend": "native-mini-swe",
            "submission_status": "submitted",
            "judge_status": "passed",
            "outcome": "passed",
            "score": 1,
            "trusted_replay": {
                "final_test_profile": {
                    "score_sidecar_contract": {
                        "score_authority": "development_only",
                    },
                },
                "derived_score_sidecar_reference": {
                    "path": "evidence/score-sidecars/a.json",
                    "sha256": "a" * 64,
                },
            },
        }

    monkeypatch.setattr(scorer, "read_native_cell", fake_read_native_cell)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_campaign.py",
            "--campaign-output",
            str(run_root),
            "--campaign",
            str(campaign_path),
            "--judge-kind",
            "final_trusted_replay",
            "--episode-backend",
            "native-mini-swe",
            "--output",
            str(output),
        ],
    )

    assert scorer.main() == 0
    report = read_json(output)
    assert report["cell_count"] == 1
    assert report["rows"][0]["backend"] == "native-mini-swe"
    assert calls == [
        (
            run_root / cell["cell_id"],
            cell,
            hashlib.sha256(campaign_path.read_bytes()).hexdigest(),
        )
    ]


def test_score_campaign_native_backend_rejects_non_evas_judge_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps({"cells": []}), encoding="utf-8")
    run_root = tmp_path / "run"
    run_root.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_campaign.py",
            "--campaign-output",
            str(run_root),
            "--campaign",
            str(campaign_path),
            "--judge-kind",
            "final_spectre",
            "--episode-backend",
            "native-mini-swe",
        ],
    )

    with pytest.raises(SystemExit, match="final_trusted_replay"):
        scorer.main()


def test_native_dispatch_infrastructure_failure_is_counted_without_legacy_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cell = {
        "cell_id": "v4-001-G2-r00-agentic",
        "task_id": "v4-001",
        "family_id": "001",
        "form": "dut",
        "mode": "G2",
        "process": "agentic",
        "experimental_arm": "Agentic",
        "base_mode": "G2",
        "executable_feedback": True,
        "per_turn_max_tokens": 128,
    }
    args = Namespace(
        output=tmp_path,
        release=runner.DEFAULT_RELEASE,
        setup_timeout_s=10,
        request_timeout_s=11,
        tool_timeout_s=12,
        judge_timeout_s=13,
        agent_timeout_s=14,
        episode_backend="native-mini-swe",
        agent_scaffold="mini-swe",
        dry_run=False,
        resume=False,
        evas_command="/usr/bin/evas-fixture",
        final_judge_command="/usr/bin/final-fixture",
        mini_swe_image="image:evas",
        mini_swe_no_evas_image="image:no-evas",
        campaign_file_sha256="b" * 64,
    )

    def fail_export(*args, **kwargs):
        raise runner.RuntimeExportError("fixture exporter failed")

    monkeypatch.setattr(runner, "export_runtime", fail_export)

    result = runner.run_cell_preserving_failure(
        cell, args, SimpleNamespace(model="fixture-model")
    )
    runtime = tmp_path / cell["cell_id"]
    assert result["backend"] == "native-mini-swe"
    assert result["status"] == "infrastructure_failure"
    assert result["termination_reason"] == "runtime_export_failure"
    assert not (runtime / "evidence/campaign_result.json").exists()

    row = scorer.read_native_cell(
        runtime,
        cell,
        campaign_file_sha256="b" * 64,
    )
    assert row["backend"] == "native-mini-swe"
    assert row["judge_status"] == "infrastructure_failure"
    assert row["score"] is None
    assert row["failure_class"] == "infrastructure"
    assert "trusted_replay" not in row
    scorer.summarize([row], "final_trusted_replay", scheduled_cells=[cell])


def test_native_existing_dispatch_is_not_exported_or_overwritten(tmp_path, monkeypatch):
    cell = {"cell_id": "v4-reserved"}
    runtime = tmp_path / cell["cell_id"]
    receipt = runtime / "evidence/native-dispatch/result.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("preserve previous attempt")
    args = Namespace(output=tmp_path, episode_backend="native-mini-swe", resume=False)
    monkeypatch.setattr(runner, "validate_native_mini_swe_cell", lambda _: None)
    with pytest.raises(runner.FinalReplayReservedError):
        runner.run_cell_preserving_failure(cell, args, None)
    assert receipt.read_text() == "preserve previous attempt"


def test_native_wrapper_preserves_existing_campaign_before_dispatch(tmp_path):
    output = tmp_path / "existing-campaign"
    output.mkdir()
    manifest = output / "campaign.json"
    manifest.write_text("frozen original manifest")
    completed = subprocess.run([
        sys.executable, str(WRAPPER), "--output-root", str(output),
        "--model", "fixture-model", "--task-id", "v4-001", "--form", "dut",
        "--comparison-profile", "executable-feedback-control",
        "--episode-backend", "native-mini-swe", "--dry-run",
    ], text=True, capture_output=True, timeout=60, check=False)
    assert completed.returncode != 0
    assert manifest.read_text() == "frozen original manifest"
    assert not (output / "run").exists()


def test_native_wrapper_resume_reuses_prepared_cells_in_another_process(tmp_path):
    output = tmp_path / "durable"
    command = [sys.executable, str(WRAPPER), "--output-root", str(output),
               "--model", "fixture-model", "--task-id", "v4-001", "--form", "dut",
               "--comparison-profile", "executable-feedback-control",
               "--episode-backend", "native-mini-swe", "--dry-run"]
    first = subprocess.run(command, text=True, capture_output=True, timeout=60)
    assert first.returncode == 0, first.stderr
    campaign_bytes = (output / "campaign.json").read_bytes()
    paths = [path for path in (output / "run").glob("v4-*/**/*") if path.is_file()]
    before = {path: path.read_bytes() for path in paths}
    second = subprocess.run([*command, "--resume"], text=True, capture_output=True, timeout=60)
    assert second.returncode == 0, second.stderr
    assert (output / "campaign.json").read_bytes() == campaign_bytes
    assert all(path.read_bytes() == value for path, value in before.items())
    index = read_json(sorted((output / "run/.batch").glob("index-*.json"))[-1])
    assert len(index["rows"]) == 3
    assert all(row["disposition"] == "reused" for row in index["rows"])


@pytest.mark.parametrize("interrupt_inside_cell", [False, True])
def test_native_batch_missing_only_and_interrupted_cell_fail_closed(tmp_path, monkeypatch, interrupt_inside_cell):
    from run_native_batch import run_native_batch, runner as batch_runner
    from scripts import run_v4_r53_clean_room_smoke as smoke
    campaign = smoke.campaign_builder.build_campaign(
        runner.DEFAULT_RELEASE, family_ids=["001"], model_provider="fixture",
        model="fixture", per_turn_max_tokens=64, repetitions=1, three_arm_g0_g2=True)
    campaign["cells"] = [cell for cell in campaign["cells"] if cell["form"] == "dut"]
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(campaign))
    args = Namespace(output=tmp_path / "run", dry_run=True, resume=False, workers=1,
                     native_max_attempts=1, campaign_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     release=runner.DEFAULT_RELEASE, setup_timeout_s=30,
                     episode_backend="native-mini-swe", agent_timeout_s=1800)
    def no_client():
        pytest.fail("dry-run/reuse must not create a provider")
    # Real export completes the first cell, then interruption happens before
    # the second cell has any side effect. Keep the first terminal receipt.
    # Other integration fixtures reload the runner module. Patch the actual
    # dependency held by this batch instance, not an earlier imported alias.
    original_export = batch_runner.export_runtime
    exported = []
    def export(cell, *a, **kw):
        if exported:
            if interrupt_inside_cell:
                runtime = args.output / cell["cell_id"]
                runtime.mkdir()
                (runtime / "partial-export.json").write_text("{}")
            raise KeyboardInterrupt("fixture process interruption between cells")
        exported.append(cell["cell_id"])
        return original_export(cell, *a, **kw)
    monkeypatch.setattr(batch_runner, "export_runtime", export)
    with pytest.raises(KeyboardInterrupt):
        run_native_batch(campaign, args, no_client)
    assert len(exported) == 1
    first = args.output / exported[0]
    before = {p: p.read_bytes() for p in first.rglob("*") if p.is_file()}
    args.resume = True
    monkeypatch.setattr(batch_runner, "export_runtime", original_export)
    if interrupt_inside_cell:
        with pytest.raises(ValueError, match="interrupted dry-run"):
            run_native_batch(campaign, args, no_client)
        index = read_json(sorted((args.output / ".batch").glob("index-*.json"))[-1])
        assert [r["disposition"] for r in index["rows"]] == ["reused", "blocked", "not_started"]
        assert not (args.output / campaign["cells"][2]["cell_id"]).exists()
        assert all(p.read_bytes() == content for p, content in before.items())
        return
    rows = run_native_batch(campaign, args, no_client)
    assert len(rows) == 3
    assert all(p.read_bytes() == content for p, content in before.items())
    indexes = sorted((args.output / ".batch").glob("index-*.json"))
    dispositions = [r["disposition"] for r in read_json(indexes[-1])["rows"]]
    assert dispositions == ["reused", "executed", "executed"]


@pytest.mark.parametrize("workers", [1, 3])
def test_native_batch_missing_cells_execute_once_in_roster_order(tmp_path, monkeypatch, workers):
    from run_native_batch import run_native_batch, runner as batch_runner
    campaign = {"cells": [{"cell_id": f"c-{i}"} for i in range(3)]}
    args = Namespace(output=tmp_path / "run", dry_run=True, resume=False, workers=workers,
                     native_max_attempts=1, campaign_file_sha256="a" * 64)
    called = []

    def execute(cell, args, _client, **kwargs):
        called.append(cell["cell_id"])
        runtime = args.output / cell["cell_id"]
        runtime.mkdir()
        (runtime / "evidence").write_text("fixture")
        return {"cell_id": cell["cell_id"], "status": "prepared"}

    monkeypatch.setattr(batch_runner, "run_cell_preserving_failure", execute)
    first = run_native_batch(campaign, args, lambda: pytest.fail("no provider"))
    assert sorted(called) == ["c-0", "c-1", "c-2"]
    assert [row["cell_id"] for row in first] == ["c-0", "c-1", "c-2"]
    args.resume = True
    assert run_native_batch(campaign, args, lambda: pytest.fail("no provider")) == first
    assert len(called) == 3


@pytest.mark.parametrize("backend", ["native-mini-swe", "native-reasoning"])
def test_r53_docker_native_batch_reuses_scored_cell_without_provider(tmp_path, backend):
    import os
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real Docker/EVAS batch resume")
    from run_native_batch import run_native_batch
    from scripts import run_v4_r53_clean_room_smoke as smoke
    campaign = smoke.campaign_builder.build_campaign(
        runner.DEFAULT_RELEASE, family_ids=["001"], model_provider="fixture",
        model=smoke.DEFAULT_MODEL, per_turn_max_tokens=4096, repetitions=1, three_arm_g0_g2=True)
    cell = next(c for c in campaign["cells"]
                if c["form"] == "dut" and c["experimental_arm"] == "Agentic")
    campaign["cells"] = [cell]
    path = tmp_path / "campaign.json"
    path.write_text(json.dumps(campaign))
    args = smoke.parse_args(["--output-root", str(tmp_path),
                            "--evas-command", str(ROOT / ".venv/bin/evas")])
    args.evas_command, identity = smoke.resolve_evas_command(args.evas_command)
    smoke.configure_runner_args(args, tmp_path / "run", identity)
    args.episode_backend = backend
    args.native_max_attempts = 1
    args.workers = 1
    args.campaign_file_sha256 = smoke.sha256_file(path)
    contract = smoke.public_contract(runner.DEFAULT_RELEASE, cell["task_id"])
    from public_validation import public_execution_contract
    task_root = runner.DEFAULT_RELEASE / smoke.task_index_row(
        runner.DEFAULT_RELEASE, cell["task_id"])["public_contract"]
    public_command, _ = public_execution_contract(read_json(task_root.parent / "public/evas_runtime.json"))
    calls = []
    def factory():
        calls.append(1)
        return smoke.client_for_arm("Agentic", smoke.public_stub_artifacts(contract),
                                    smoke.DEFAULT_MODEL, public_command)
    first = run_native_batch(campaign, args, factory)
    assert first[0]["score"] == 0
    assert len(calls) == 1
    runtime = args.output / cell["cell_id"]
    before = {p: p.read_bytes() for p in runtime.rglob("*") if p.is_file()}
    args.resume = True
    # A new interpreter has no client, runner object or completion cache from
    # the first invocation. Only the on-disk batch/terminal evidence survives.
    code = """
import json, sys
from pathlib import Path
from argparse import Namespace
sys.path.insert(0, sys.argv[1])
import run_native_batch as batch
payload = json.loads(sys.stdin.read())
args = Namespace(**payload['args'])
args.output = Path(args.output)
args.release = Path(args.release)
def forbidden(*a, **kw):
    raise AssertionError('completed batch reentered provider, cell or judge')
batch.runner.load_key = forbidden
batch.runner.run_cell_preserving_failure = forbidden
batch.runner.run_trusted_replay = forbidden
print(json.dumps(batch.run_native_batch(payload['campaign'], args, forbidden)))
"""
    payload = {"campaign": campaign, "args": {k: v for k, v in vars(args).items()
                                              if not k.startswith("_")}}
    completed = subprocess.run([sys.executable, "-c", code, str(CALIBRATION)],
                               input=json.dumps(payload, default=str), text=True,
                               capture_output=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    second = json.loads(completed.stdout)
    assert first == second
    assert all(p.read_bytes() == content for p, content in before.items())
