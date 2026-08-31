"""Offline checks for a dated study blueprint, NOT a live launcher or authority gate.

Only the release index, manifest, public contracts and public task trees are read.
Existing differential tests separately exercise actual legacy/native requests.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "benchmark-vabench-release-v4"
RELEASE = PACKAGE / "release/benchmarkv4-r53"
PROTOCOL = ROOT / "docs/alphaapollo-migration/experiments/legacy-native-comparison-20260831.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_snapshot(task_id):
    """Hash source public files, not a full export or hidden binding validation."""
    index = json.loads((RELEASE / "TASK_INDEX.json").read_text())["tasks"]
    row, = [item for item in index if item["task_id"] == task_id]
    task = RELEASE / row["task_dir"]
    public = task / "public"
    files = {}
    for path in sorted(public.rglob("*")):
        assert not path.is_symlink(), path
        if path.is_file():
            files[path.relative_to(public).as_posix()] = sha256(path)
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {
        "task_id": task_id,
        "family_id": row["family_id"],
        "form": row["form"],
        "public_contract_sha256": sha256(task / "public_contract.json"),
        "public_files_sha256": hashlib.sha256(encoded).hexdigest(),
        "public_file_count": len(files),
    }


def test_blueprint_is_not_a_live_campaign_or_spending_authorization():
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["schema_version"] == "vaevas-comparison-blueprint-v1"
    assert protocol["status"] == "offline_protocol_only"
    assert protocol["live_authorized"] is False
    assert protocol["model_contract"] is None
    assert protocol["fee_cap"] is None
    assert set(protocol["live_blockers"]) == {
        "model_and_decoding_identity", "fresh_fee_authorization",
        "matched_spending_guard_integration", "complete_export_and_image_audit",
        "cross_backend_result_join",
    }


def test_blueprint_freezes_six_single_attempt_agentic_cells():
    protocol = json.loads(PROTOCOL.read_text())
    schedule = protocol["schedule"]
    assert len(schedule) == 6
    assert [row["order"] for row in schedule] == list(range(1, 7))
    assert len({row["cell_id"] for row in schedule}) == 6
    pairs = {(row["task_id"], row["episode_backend"]) for row in schedule}
    assert pairs == {(task, backend) for task in ("v4-001", "v4-1001", "v4-501")
                     for backend in ("legacy", "native-mini-swe")}
    assert all(row["state"] == "not_started" for row in schedule)
    assert [(row["task_id"], row["episode_backend"]) for row in schedule] == [
        ("v4-001", "legacy"), ("v4-001", "native-mini-swe"),
        ("v4-1001", "native-mini-swe"), ("v4-1001", "legacy"),
        ("v4-501", "legacy"), ("v4-501", "native-mini-swe"),
    ]
    controls = protocol["controls"]
    assert controls["agent_scaffold"] == "mini-swe"
    assert controls["experimental_arm"] == "Agentic"
    assert controls["mode"] == "G2"
    assert controls["max_attempts"] == controls["workers"] == 1
    assert controls["resume"] is False
    assert controls["model_call_limit"] is None
    assert controls["extensions"] == []
    assert controls["cross_cell_memory"] is controls["network"] is False
    assert controls["image_id_for_live_run"] is None


def test_blueprint_retains_r53_wall_time_and_evas_scope():
    protocol = json.loads(PROTOCOL.read_text())
    policy = json.loads((PACKAGE / "EXPERIMENT_POLICY.json").read_text())
    assert protocol["controls"]["agent_wall_time_seconds"] == policy["agent_wall_time_seconds"]
    assert protocol["release_manifest_sha256"] == sha256(RELEASE / "MANIFEST.json")
    assert protocol["judge"] == {"engine": "evas", "version": "0.8.7",
                                 "kind": "final_trusted_replay", "authority": "development_only"}
    assert protocol["claim_scope"] == "small_sample_workflow_comparison"


@pytest.mark.parametrize("task_id", ["v4-001", "v4-1001", "v4-501"])
def test_selected_public_source_bytes_match_dated_snapshot(task_id):
    protocol = json.loads(PROTOCOL.read_text())
    expected, = [row for row in protocol["public_source_snapshots"] if row["task_id"] == task_id]
    assert public_snapshot(task_id) == expected


@pytest.mark.parametrize("structured_feedback", [False, True], ids=["legacy-env", "native-env"])
def test_observed_docker_mounts_match_common_environment_contract(tmp_path, structured_feedback):
    """Observe the shared environment, not a complete exported/backend episode."""
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in cached Docker image audit; no provider or final judge")
    from test_mini_swe_vabench import load_module

    mini = load_module()
    runtime = tmp_path / "runtime"
    task = runtime / "public/task"
    task.mkdir(parents=True)
    (task / "instruction.md").write_text("Synthetic public task.\n")
    (runtime / "public/submission").mkdir()
    hidden = runtime / "evaluator"
    hidden.mkdir()
    (hidden / "sentinel.txt").write_text("SYNTHETIC_PRIVATE_SENTINEL\n")
    env = mini.VaBenchBashEnvironment(
        runtime, timeout_s=30, sandbox_backend="docker", evas_command="",
        docker_image=os.environ.get("VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE),
        submission_gate=lambda _: {"passed": False},
        structured_evas_feedback=structured_feedback,
    )
    try:
        env.preflight()
        # Select mount/security fields only; never dump Config.Env or credentials.
        inspected = subprocess.check_output([
            "docker", "inspect", "--format",
            '{{json .Mounts}}\n{{json .HostConfig.NetworkMode}}\n'
            '{{json .HostConfig.ReadonlyRootfs}}\n{{json .HostConfig.CapDrop}}\n{{json .Image}}',
            env._docker_container,
        ], text=True, timeout=30).splitlines()
        mounts, network, read_only, capabilities, image_id = map(json.loads, inspected)
        bindings = {row["Destination"]: row for row in mounts if row["Type"] == "bind"}
        assert set(bindings) == {"/workspace/public/task", "/workspace/public/submission", "/workspace/work"}
        for destination, source, writable in (
            ("/workspace/public/task", task, False),
            ("/workspace/public/submission", runtime / "public/submission", True),
            ("/workspace/work", env.work_dir, True),
        ):
            assert Path(bindings[destination]["Source"]).resolve() == source.resolve()
            assert bindings[destination]["RW"] is writable
        assert network == "none" and read_only is True
        assert "ALL" in capabilities
        assert image_id == env.docker_image_id
        result = env.execute({"command": (
            "test ! -e /workspace/evaluator/sentinel.txt && "
            "test ! -e /workspace/public/evaluator/sentinel.txt && "
            "test -r public/task/instruction.md && printf 'PUBLIC_ONLY_MOUNTS_OK\\n'"
        )})
        assert result["returncode"] == 0
        assert "PUBLIC_ONLY_MOUNTS_OK" in result["output"]
    finally:
        env.close()
