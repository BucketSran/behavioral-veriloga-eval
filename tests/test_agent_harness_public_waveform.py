"""Fresh public EVAS execution, not model-authored waveform provenance."""

import subprocess
import json
import base64
import os
import sys
from pathlib import Path

import pytest

from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401


@pytest.mark.parametrize("raw", [b"time,v(out)\n0,1\n1,3\n", b"bad\ntext\n", b"\xff"])
def test_waveform_bytes_reuse_exact_parser_policy(tmp_path, raw):
    from runners.agent_harness.tools.waveform_summary import (
        summarize_waveform, summarize_waveform_bytes,
    )
    (tmp_path / "tran.csv").write_bytes(raw)
    assert summarize_waveform_bytes(raw) == summarize_waveform(tmp_path)


def test_waveform_bytes_reject_oversize_without_content_hash():
    from runners.agent_harness.tools.waveform_summary import MAX_BYTES, summarize_waveform_bytes
    result = summarize_waveform_bytes(b"x" * (MAX_BYTES + 1))
    assert result["status"] == "too_large"
    assert result["accepted_bytes"] == 0
    assert result["source_sha256"] is None


@pytest.mark.parametrize("readonly", [False, True])
def test_docker_submission_readonly_is_explicit_and_legacy_default_unchanged(public_case, monkeypatch, readonly):  # noqa: F811
    import mini_swe_vabench as mini
    source, _, _ = public_case
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        value = "sha256:" + "a" * 64 if argv[1:3] == ["image", "inspect"] else "container"
        return subprocess.CompletedProcess(argv, 0, value, "")

    monkeypatch.setattr(mini.shutil, "which", lambda _: "/bin/true")
    monkeypatch.setattr(mini.subprocess, "run", run)
    options = {"submission_read_only": True} if readonly else {}
    environment = mini.VaBenchBashEnvironment(
        source.runtime, timeout_s=10, sandbox_backend="docker", evas_command="evas",
        docker_image="sha256:" + "a" * 64, candidate_artifacts=("model.va",),
        submission_gate=lambda _: {"passed": False}, **options,
    )
    environment._ensure_docker_container()
    create = next(argv for argv in calls if argv[1] == "create")
    mount = next(arg for arg in create if "dst=/workspace/public/submission" in arg)
    assert mount.endswith(",readonly") is readonly
    config = environment.serialize()["info"]["config"]["environment"]
    assert config.get("submission_read_only", False) is readonly
    if not readonly:
        assert "submission_read_only" not in config
    environment.close()


def make_executor(case, **overrides):
    from public_waveform import IsolatedPublicWaveformExecutor
    from test_agent_harness_production_public_validation import RELEASE
    source, context, _ = case
    return IsolatedPublicWaveformExecutor(**{
        "runtime": source.runtime, "context": context,
        "candidate_artifacts": ("model.va",), "release": RELEASE,
        "campaign_config_sha256": "a" * 64, "docker_image_id": "sha256:" + "b" * 64,
        **overrides,
    })


def test_readonly_submission_cannot_be_claimed_without_docker(public_case):  # noqa: F811
    import mini_swe_vabench as mini
    with pytest.raises(ValueError, match="read-only submission requires Docker"):
        mini.VaBenchBashEnvironment(
            public_case[0].runtime.parent / "non-docker-readonly", timeout_s=10,
            sandbox_backend="none", evas_command="evas",
            submission_read_only=True, candidate_artifacts=("model.va",),
            submission_gate=lambda _: {"passed": False},
        )


def test_waveform_profile_freezes_public_inputs_and_uses_canonical_candidate_hash(public_case):  # noqa: F811
    import hashlib
    from result_protocol import canonical_sha256
    from runners.agent_harness import public_validation_profile_sha256

    executor = make_executor(public_case)
    source, _, _ = public_case
    expected = canonical_sha256([{"path": "model.va", "sha256": hashlib.sha256(
        (source.workspace / "submission/model.va").read_bytes()).hexdigest()}])
    assert executor.candidate_tree_sha256() == expected
    assert executor.profile_sha256 == public_validation_profile_sha256(executor.profile)
    assert executor.profile["allowed_feedback"] == ["runtime", "waveform_summary"]
    assert "FINAL_PRIVATE_SENTINEL" not in json.dumps(executor.profile)
    profile = executor.profile
    profile["allowed_feedback"].append("final_score")
    assert "final_score" not in executor.profile["allowed_feedback"]


def test_partial_candidate_inspection_is_recoverable_and_binds_real_tree(public_case):  # noqa: F811
    from result_protocol import canonical_sha256
    executor = make_executor(public_case)
    candidate = public_case[0].workspace / "submission/model.va"
    saved = candidate.read_bytes()
    candidate.unlink()
    assert executor.inspect_candidate() == (canonical_sha256([]), ("model.va",))
    candidate.write_bytes(saved)
    assert executor.inspect_candidate() == (executor.candidate_tree_sha256(), ())


@pytest.mark.parametrize("kind", ["symlink", "fifo", "extra", "include", "terminal"])
def test_partial_candidate_inspection_does_not_hide_unsafe_inputs(public_case, kind):  # noqa: F811
    executor = make_executor(public_case)
    root = public_case[0].workspace / "submission"
    (root / "model.va").unlink()
    if kind == "symlink":
        (root / "bad.va").symlink_to(root / "absent")
    elif kind == "fifo":
        os.mkfifo(root / "bad.va")
    elif kind == "extra":
        (root / "extra.va").write_text("extra")
    elif kind == "include":
        (root / "model.va").write_text('`include "../private.va"')
    else:
        (public_case[0].runtime / "evidence/final_submission").mkdir(parents=True)
    with pytest.raises(ValueError):
        executor.inspect_candidate()


def test_expired_episode_deadline_starts_no_simulation(public_case, docker_processes):  # noqa: F811
    executor = make_executor(public_case, deadline_monotonic=0.0)
    with pytest.raises(RuntimeError, match="deadline"):
        executor.validate(candidate_tree_sha256=executor.candidate_tree_sha256())
    assert not docker_processes["simulations"]


@pytest.fixture
def docker_processes(monkeypatch):
    """Fake only Docker's process boundary; real executor/environment code runs."""
    import mini_swe_vabench as mini
    original_popen = subprocess.Popen
    state = {"calls": [], "creates": [], "simulations": [], "exitcode": 0,
             "raw": b"time,v(out)\n0,1\n1,3\n", "cleanup_rc": 0,
             "image_id": "sha256:" + "b" * 64}

    def run(argv, **kwargs):
        state["calls"].append(argv)
        output = ""
        rc = 0
        if argv[1:3] == ["image", "inspect"]:
            output = state["image_id"]
        elif argv[1] == "create":
            state["creates"].append(argv)
            output = f"container-{len(state['creates'])}"
        elif argv[1] == "rm":
            rc = state["cleanup_rc"]
        elif "-I" in argv:
            output = json.dumps({"status": "available", "data": base64.b64encode(state["raw"]).decode()})
        elif "--version" in argv[-1]:
            output = "evas-sim 0.8.7"
        return subprocess.CompletedProcess(argv, rc, output, "")

    def popen(argv, **kwargs):
        state["simulations"].append(argv)
        if state.get("on_simulation"):
            state["on_simulation"]()
        return original_popen([sys.executable, "-c", f"print('forged wrapper diagnostic');raise SystemExit({state['exitcode']})"], **kwargs)

    monkeypatch.setattr(mini.shutil, "which", lambda _: "/bin/true")
    monkeypatch.setattr(mini.subprocess, "run", run)
    monkeypatch.setattr(mini.subprocess, "Popen", popen)
    return state


def test_fresh_execution_binds_snapshot_not_markers_or_old_outputs(public_case, docker_processes):  # noqa: F811
    import hashlib
    from result_protocol import canonical_sha256
    executor = make_executor(public_case)
    source, context, _ = public_case
    (source.workspace / "evas-output/tran.csv").write_text("OLD_MODEL_OUTPUT")
    candidate = executor.candidate_tree_sha256()
    first = executor.validate(candidate_tree_sha256=candidate)
    second = executor.validate(candidate_tree_sha256=candidate)
    assert first["candidate_tree_sha256"] == candidate
    assert first["profile_sha256"] == executor.profile_sha256
    assert first["attempt_id"] == context.attempt_id
    assert first["waveform_summary"]["source_sha256"] == hashlib.sha256(docker_processes["raw"]).hexdigest()
    assert first["invocation_id"] != second["invocation_id"]
    assert first["receipt_sha256"] == canonical_sha256({k: v for k, v in first.items() if k != "receipt_sha256"})
    assert first["status"] == "succeeded"
    assert "OLD_MODEL_OUTPUT" not in json.dumps(first)
    assert len(docker_processes["creates"]) == 2
    for argv in docker_processes["creates"]:
        mounts = [arg for arg in argv if arg.startswith("type=bind")]
        assert all(str(source.runtime) not in mount for mount in mounts)
        assert len(mounts) == 3
        submission = next(mount for mount in mounts if "dst=/workspace/public/submission" in mount)
        assert submission.endswith(",readonly")
        assert not Path(submission.split("src=")[1].split(",")[0]).exists()
    assert all("/usr/local/bin/evas simulate" in argv[-1] for argv in docker_processes["simulations"])


@pytest.mark.parametrize("change", ["candidate", "task", "image", "command", "terminal"])
def test_waveform_drift_rejects_before_simulation(public_case, docker_processes, change):  # noqa: F811
    executor = make_executor(public_case)
    source, _, _ = public_case
    candidate = executor.candidate_tree_sha256()
    if change == "candidate":
        (source.workspace / "submission/model.va").write_text("different candidate")
    elif change == "task":
        (source.workspace / "task/instruction.md").write_text("different task")
    elif change == "image":
        docker_processes["image_id"] = "sha256:" + "c" * 64
    elif change == "command":
        executor.command = "echo forged"
    else:
        (source.runtime / "evidence/final_submission").mkdir(parents=True)
    with pytest.raises((ValueError, RuntimeError), match="drift|mismatch|terminal"):
        executor.validate(candidate_tree_sha256=candidate)
    assert not docker_processes["simulations"]
    with pytest.raises(ValueError, match="invalidated"):
        executor.validate(candidate_tree_sha256=candidate)


def test_concurrent_candidate_change_preserves_primary_and_cleanup_incident(public_case, docker_processes):  # noqa: F811
    from public_waveform import PublicWaveformError
    executor = make_executor(public_case)
    source, _, _ = public_case
    candidate = executor.candidate_tree_sha256()
    docker_processes["cleanup_rc"] = 1
    docker_processes["on_simulation"] = lambda: (source.workspace / "submission/model.va").write_text("changed during execution")
    with pytest.raises(PublicWaveformError, match="candidate drift") as caught:
        executor.validate(candidate_tree_sha256=candidate)
    assert caught.value.primary_type == "ValueError"
    assert caught.value.cleanup_incidents == [{"stage": "container_cleanup", "returncode": 1}]


@pytest.mark.parametrize("exitcode,cleanup_rc,status,usable", [
    (2, 0, "failed", True), (124, 0, "timed_out", False), (0, 1, "succeeded", False),
])
def test_failure_or_cleanup_never_reuses_waveform(public_case, docker_processes, exitcode, cleanup_rc, status, usable):  # noqa: F811
    executor = make_executor(public_case)
    docker_processes.update(exitcode=exitcode, cleanup_rc=cleanup_rc)
    receipt = executor.validate(candidate_tree_sha256=executor.candidate_tree_sha256())
    assert receipt["status"] == status
    assert receipt["usable_feedback"] is usable
    assert receipt["waveform_summary"] is None
    assert receipt["task_correctness"] == "not_evaluated"
    if exitcode:
        assert not any("-I" in argv for argv in docker_processes["calls"])


@pytest.mark.parametrize("kind", ["symlink", "fifo", "extra", "oversize"])
def test_candidate_snapshot_rejects_unsafe_inputs(public_case, docker_processes, kind):  # noqa: F811
    source, _, _ = public_case
    path = source.workspace / "submission/model.va"
    if kind in {"symlink", "fifo"}:
        path.unlink()
        if kind == "symlink":
            path.symlink_to(source.runtime / "evaluator/secret.txt")
        else:
            os.mkfifo(path)
    elif kind == "extra":
        (path.parent / "extra.va").write_text("extra")
    else:
        path.write_bytes(b"x" * 1_000_001)
    with pytest.raises(ValueError):
        make_executor(public_case).validate(candidate_tree_sha256="0" * 64)
    assert not docker_processes["creates"]


@pytest.mark.parametrize("condition", ["OneShot", "Agent-No-EVAS"])
def test_non_agentic_cannot_construct_public_waveform(public_case, condition):  # noqa: F811
    from dataclasses import replace
    with pytest.raises(ValueError, match="Agentic"):
        make_executor(public_case, context=replace(public_case[1], condition=condition))


@pytest.mark.parametrize("kind,status", [
    ("valid", "available"), ("missing", "missing"), ("fifo", "invalid"),
    ("symlink", "invalid"), ("root_link", "invalid"), ("oversize", "too_large"),
])
def test_fixed_docker_reader_is_bounded_and_rejects_links(tmp_path, kind, status):
    from public_waveform import OUTPUT_READER
    from runners.agent_harness.tools.waveform_summary import MAX_BYTES
    root = tmp_path / "output"
    root.mkdir()
    path = root / "tran.csv"
    if kind == "valid":
        path.write_bytes(b"time,v(out)\n0,1\n")
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "symlink":
        path.symlink_to(tmp_path / "missing-target")
    elif kind == "oversize":
        path.write_bytes(b"x" * (MAX_BYTES + 1))
    elif kind == "root_link":
        link = tmp_path / "linked-output"
        link.symlink_to(root, target_is_directory=True)
        root = link
    run = subprocess.run([sys.executable, "-I", "-c", OUTPUT_READER, str(root), str(MAX_BYTES)],
                         text=True, capture_output=True, timeout=3, check=True)
    result = json.loads(run.stdout)
    assert result["status"] == status
    assert len(run.stdout) < 200
    if status == "available":
        assert base64.b64decode(result["data"]) == path.read_bytes()


@pytest.mark.parametrize("task_id,form", [("v4-001", "dut"), ("v4-501", "testbench")])
def test_r53_docker_fresh_waveform_receipt(tmp_path, task_id, form, monkeypatch):
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in real isolated public EVAS waveform smoke")
    import importlib.util
    import mini_swe_vabench as mini
    import public_waveform as module
    from runners.agent_harness import EpisodeContext
    from test_agent_harness_production_public_validation import ROOT, RELEASE
    from scripts import run_v4_r53_clean_room_smoke as smoke

    path = ROOT / "benchmark-vabench-release-v4/operations/tri_form_derivation_prep/export_tri_form_runtime.py"
    spec = importlib.util.spec_from_file_location("waveform_public_exporter", path)
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    row = smoke.task_index_row(RELEASE, task_id)
    artifacts = smoke.public_stub_artifacts(smoke.public_contract(RELEASE, task_id))
    runtime = tmp_path / "runtime"
    exporter.install_public(RELEASE / row["task_dir"], runtime / "public", form, "G2")
    submission = runtime / "public/submission"
    submission.mkdir()
    for name, content in artifacts.items():
        (submission / name).write_text(content)
    # Poison only a fresh fixture's generation output; it must never be read.
    old_output = runtime / "public/work/evas-output"
    old_output.mkdir(parents=True)
    (old_output / "tran.csv").write_text("POISON_OLD_OUTPUT")
    image = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}",
                            os.environ.get("VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE)],
                           capture_output=True, text=True, check=True).stdout.strip()
    original_probe = module._FreshEnvironment.inspect_public_evas
    containers = []

    def probe(environment):
        identity = original_probe(environment)
        containers.append(environment._docker_container)
        inspected = json.loads(subprocess.run(["docker", "inspect", environment._docker_container],
                                              text=True, capture_output=True, check=True).stdout)[0]
        assert inspected["HostConfig"]["NetworkMode"] == "none"
        mounts = inspected["Mounts"]
        assert all(str(runtime) not in item["Source"] for item in mounts)
        for destination in ("/workspace/public/task", "/workspace/public/submission"):
            assert next(item for item in mounts if item["Destination"] == destination)["RW"] is False
        return identity

    monkeypatch.setattr(module._FreshEnvironment, "inspect_public_evas", probe)
    executor = module.IsolatedPublicWaveformExecutor(
        runtime=runtime, context=EpisodeContext("waveform", "waveform-1", task_id, "Agentic", 2),
        candidate_artifacts=tuple(sorted(artifacts)), release=RELEASE,
        campaign_config_sha256="d" * 64, docker_image_id=image,
    )
    first = executor.validate(candidate_tree_sha256=executor.candidate_tree_sha256())
    second = executor.validate(candidate_tree_sha256=executor.candidate_tree_sha256())
    for receipt in (first, second):
        assert receipt["status"] == "succeeded", receipt
        assert receipt["usable_feedback"] is True
        assert receipt["waveform_summary"]["status"] in {"available", "truncated"}, receipt
        assert receipt["waveform_summary"]["source_sha256"]
        assert receipt["waveform_summary"]["scanned_rows"] > 0
        assert receipt["feedback_scope"] == ("reference_dut_only" if form == "testbench" else "public_simulation_only")
        assert "POISON_OLD_OUTPUT" not in json.dumps(receipt)
    assert len(set(containers)) == 2
    assert first["invocation_id"] != second["invocation_id"]
    for container in containers:
        assert subprocess.run(["docker", "inspect", container], capture_output=True).returncode != 0
