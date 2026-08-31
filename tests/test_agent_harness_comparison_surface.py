from __future__ import annotations

import json
from copy import deepcopy
import math
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))

import comparison_surface as surface  # noqa: E402


def test_tool_result_parent_id_changes_request_fingerprint():
    payload = {"model": "deepseek-v4-flash", "max_tokens": 4096, "configured_watchdog_s": 1800,
               "messages": [{"role": "tool", "content": "same result", "tool_call_id": "first"}]}
    before = surface.snapshot_request(payload, timeout_s=1800)
    changed = deepcopy(payload)
    changed["messages"][0]["tool_call_id"] = "second"
    after = surface.snapshot_request(changed, timeout_s=1800)
    assert before["request_sha256"] != after["request_sha256"]
    assert before["full_payload_sha256"] != after["full_payload_sha256"]


def test_present_empty_submission_is_hashed_not_confused_with_missing_evidence(tmp_path):
    task = tmp_path / "public/task"
    task.mkdir(parents=True)
    (task / "instruction.md").write_text("public")
    (tmp_path / "public/submission").mkdir()
    snapshot = surface.snapshot_public_runtime(tmp_path)
    assert snapshot["initial_submission_files"] == {}
    assert snapshot["initial_submission_tree_sha256"] == surface.canonical_sha256({})


def test_public_runtime_snapshot_hashes_model_visible_files_without_following_public_alias(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    skills = runtime / "public" / "skills"
    task.mkdir(parents=True)
    submission.mkdir()
    skills.mkdir()
    (runtime / "agent_prompt.txt").write_text("private-ish but model-visible prompt\n", encoding="utf-8")
    (runtime / "MODEL_ACCESS_POLICY.json").write_text('{"tools":["bash"]}\n', encoding="utf-8")
    (task / "instruction.md").write_text("public instruction\n", encoding="utf-8")
    (task / "reference_dut.va").write_text("module reference; endmodule\n", encoding="utf-8")
    (submission / "seed.va").write_text("module seed; endmodule\n", encoding="utf-8")
    (skills / "SNAPSHOT_MANIFEST.json").write_text("{}\n", encoding="utf-8")
    (runtime / "public" / "public").symlink_to(".", target_is_directory=True)

    snapshot = surface.snapshot_public_runtime(runtime)

    assert snapshot["schema_version"] == "vaevas-comparison-public-runtime-v1"
    assert snapshot["counts"]["public_task_files"] == 2
    assert snapshot["counts"]["initial_submission_files"] == 1
    assert set(snapshot["public_task_files"]) == {"instruction.md", "reference_dut.va"}
    assert snapshot["public_aliases"] == {"public/public": "."}
    assert snapshot["model_visible_files"]["public/task/instruction.md"]["bytes"] == len("public instruction\n")
    assert snapshot["model_visible_files"]["public/submission/seed.va"]["sha256"] == surface.file_sha256(
        submission / "seed.va"
    )
    assert snapshot["tree_sha256"] == surface.canonical_sha256(
        {
            "files": snapshot["model_visible_files"],
            "symlinks": snapshot["public_aliases"],
        }
    )
    assert "public/public/task/instruction.md" not in snapshot["model_visible_files"]


def test_public_runtime_snapshot_rejects_private_looking_model_visible_entries(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    hidden = runtime / "public" / "task" / "hidden"
    hidden.mkdir(parents=True)
    (hidden / "checker.txt").write_text("do not hash this content\n", encoding="utf-8")

    with pytest.raises(ValueError, match="private-looking"):
        surface.snapshot_public_runtime(runtime)


@pytest.mark.parametrize("name", ["evaluator", "solution", "trusted_replay_fixtures"])
def test_public_runtime_snapshot_rejects_sensitive_model_visible_directories(
    tmp_path: Path, name: str,
) -> None:
    runtime = tmp_path / "runtime"
    sensitive = runtime / "public" / name
    sensitive.mkdir(parents=True)
    (sensitive / "fixture.txt").write_text("sealed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="private-looking"):
        surface.snapshot_public_runtime(runtime)


def test_public_runtime_snapshot_rejects_symlinked_public_root(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    target = tmp_path / "target-public"
    target.mkdir(parents=True)
    runtime.mkdir()
    (runtime / "public").symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="public/ must not be a symlink"):
        surface.snapshot_public_runtime(runtime)


def test_request_snapshot_fingerprints_payload_without_raw_content() -> None:
    payload = {
        "model": "deepseek-v4-flash",
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 4096,
        "stream": True,
        "stream_options": {"include_usage": True},
        "thinking": {"type": "disabled"},
        "tool_choice": "auto",
        "configured_watchdog_s": 1800,
        "messages": [
            {"role": "system", "content": "SECRET SYSTEM PROMPT"},
            {"role": "user", "content": [{"type": "text", "text": "PRIVATE TASK"}]},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "bash", "arguments": '{"command":"secret command"}'},
                    }
                ],
            },
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Run a command",
                    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}},
                },
            }
        ],
    }

    fingerprint = surface.snapshot_request(payload, timeout_s=1800)
    encoded = json.dumps(fingerprint, sort_keys=True)

    assert fingerprint["schema_version"] == "vaevas-comparison-request-v1"
    assert fingerprint["model"] == "deepseek-v4-flash"
    assert fingerprint["effective_timeout_s"] == 1800
    assert fingerprint["configured_watchdog_s"] == 1800
    assert fingerprint["decoding"] == {"temperature": 0, "top_p": 1}
    assert fingerprint["provider_options"] == {
        "stream": True,
        "stream_options_sha256": surface.canonical_sha256({"include_usage": True}),
        "thinking_sha256": surface.canonical_sha256({"type": "disabled"}),
        "tool_choice_sha256": surface.canonical_sha256("auto"),
    }
    assert fingerprint["messages"][0] == {
        "index": 0, "role": "system", "content_sha256": surface.canonical_sha256("SECRET SYSTEM PROMPT"),
        "tool_calls_sha256": surface.canonical_sha256([]), "tool_call_ids": [],
    }
    assert fingerprint["messages"][1]["content_sha256"] == surface.canonical_sha256(payload["messages"][1]["content"])
    assert fingerprint["messages"][2]["tool_calls_sha256"] == surface.canonical_sha256(
        payload["messages"][2]["tool_calls"]
    )
    assert fingerprint["tools"][0]["name"] == "bash"
    assert "SECRET" not in encoded
    assert "PRIVATE TASK" not in encoded
    assert "Run a command" not in encoded
    assert "secret command" not in encoded


def test_request_snapshot_hash_changes_for_tool_choice_and_thinking() -> None:
    base = {"model": "m", "messages": [], "tools": [], "thinking": {"type": "disabled"}, "max_tokens": 1}
    changed = {**base, "thinking": {"type": "enabled"}, "tool_choice": {"type": "function", "name": "bash"}}

    assert surface.snapshot_request(base, timeout_s=5)["request_sha256"] != surface.snapshot_request(
        changed, timeout_s=5,
    )["request_sha256"]


@pytest.mark.parametrize("timeout_s", [0, -1, True, math.inf])
def test_request_snapshot_rejects_non_finite_positive_timeout(timeout_s) -> None:
    with pytest.raises(ValueError, match="timeout_s"):
        surface.snapshot_request({"model": "m", "messages": [], "tools": [], "max_tokens": 1}, timeout_s=timeout_s)


@pytest.mark.parametrize("max_tokens", [0, -1, True, math.inf])
def test_request_snapshot_rejects_non_finite_positive_max_tokens(max_tokens) -> None:
    with pytest.raises(ValueError, match="max_tokens"):
        surface.snapshot_request({"model": "m", "messages": [], "tools": [], "max_tokens": max_tokens}, timeout_s=1)


def test_observe_environment_uses_safe_docker_inspect_fields(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    task = runtime / "public" / "task"
    submission = runtime / "public" / "submission"
    work = runtime / "public" / "work"
    task.mkdir(parents=True)
    submission.mkdir()
    work.mkdir()
    env = SimpleNamespace(
        config=SimpleNamespace(sandbox_backend="docker"),
        _docker_container="container-id",
        docker_command="docker",
        runtime=runtime,
        workspace=runtime / "public",
        work_dir=work,
        docker_image_id="sha256:" + "a" * 64,
    )
    commands = []

    def fake_check_output(argv, **kwargs):
        commands.append(argv)
        assert "--format" in argv
        assert "Config.Env" not in argv[argv.index("--format") + 1]
        return "\n".join(
            [
                json.dumps(
                    [
                        {"Type": "bind", "Destination": "/workspace/public/task", "Source": str(task), "RW": False},
                        {
                            "Type": "bind",
                            "Destination": "/workspace/public/submission",
                            "Source": str(submission),
                            "RW": True,
                        },
                        {"Type": "bind", "Destination": "/workspace/work", "Source": str(work), "RW": True},
                    ]
                ),
                json.dumps("none"),
                json.dumps(True),
                json.dumps(["ALL"]),
                json.dumps("sha256:" + "a" * 64),
            ]
        )

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    observed = surface.observe_environment(env)

    assert observed["schema_version"] == "vaevas-comparison-environment-v1"
    assert observed["checks"] == {
        "no_duplicate_mount_destinations": True,
        "no_unexpected_mounts": True,
        "expected_binds": True,
        "network_none": True,
        "read_only_rootfs": True,
        "capdrop_all": True,
        "image_id_matches_environment": True,
    }
    assert observed["mounts"] == {
        "/workspace/public/task": {"source": str(task.resolve()), "rw": False},
        "/workspace/public/submission": {"source": str(submission.resolve()), "rw": True},
        "/workspace/work": {"source": str(work.resolve()), "rw": True},
    }
    assert commands == [["docker", "inspect", "--format", surface.DOCKER_INSPECT_FORMAT, "container-id"]]


def test_observe_environment_rejects_duplicate_bind_and_unexpected_volume(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    for relative in ("public/task", "public/submission", "public/work"):
        (runtime / relative).mkdir(parents=True)
    env = SimpleNamespace(
        config=SimpleNamespace(sandbox_backend="docker"),
        _docker_container="container-id",
        docker_command="docker --context fixture",
        runtime=runtime,
        workspace=runtime / "public",
        work_dir=runtime / "public" / "work",
        docker_image_id="sha256:" + "a" * 64,
    )

    def fake_check_output(argv, **kwargs):
        assert argv[:5] == ["docker", "--context", "fixture", "inspect", "--format"]
        return "\n".join(
            [
                json.dumps(
                    [
                        {
                            "Type": "bind",
                            "Destination": "/workspace/public/task",
                            "Source": str(runtime / "public/task"),
                            "RW": False,
                        },
                        {
                            "Type": "bind",
                            "Destination": "/workspace/public/task",
                            "Source": str(runtime / "public/task"),
                            "RW": False,
                        },
                        {"Type": "volume", "Destination": "/workspace/extra", "RW": True},
                    ]
                ),
                json.dumps("bridge"),
                json.dumps(False),
                json.dumps([]),
                json.dumps(None),
            ]
        )

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    observed = surface.observe_environment(env)

    assert observed["checks"]["no_duplicate_mount_destinations"] is False
    assert observed["checks"]["no_unexpected_mounts"] is False
    assert observed["checks"]["expected_binds"] is False
    assert observed["checks"]["network_none"] is False
    assert observed["checks"]["read_only_rootfs"] is False
    assert observed["checks"]["capdrop_all"] is False
    assert observed["checks"]["image_id_matches_environment"] is False
    assert observed["trusted_common_checks"] is False


def test_observe_environment_allows_only_exact_tmpfs_destinations(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    for relative in ("public/task", "public/submission", "public/work"):
        (runtime / relative).mkdir(parents=True)
    env = SimpleNamespace(
        config=SimpleNamespace(sandbox_backend="docker"),
        _docker_container="container-id",
        docker_command="docker",
        runtime=runtime,
        workspace=runtime / "public",
        work_dir=runtime / "public" / "work",
        docker_image_id="sha256:" + "a" * 64,
    )

    def fake_check_output(argv, **kwargs):
        return "\n".join(
            [
                json.dumps(
                    [
                        {
                            "Type": "bind",
                            "Destination": "/workspace/public/task",
                            "Source": str(runtime / "public/task"),
                            "RW": False,
                        },
                        {
                            "Type": "bind",
                            "Destination": "/workspace/public/submission",
                            "Source": str(runtime / "public/submission"),
                            "RW": True,
                        },
                        {
                            "Type": "bind",
                            "Destination": "/workspace/work",
                            "Source": str(runtime / "public/work"),
                            "RW": True,
                        },
                        {"Type": "tmpfs", "Destination": "/tmp", "RW": True},
                        {"Type": "tmpfs", "Destination": "/tmp/escape", "RW": True},
                    ]
                ),
                json.dumps("none"),
                json.dumps(True),
                json.dumps(["ALL"]),
                json.dumps("sha256:" + "a" * 64),
            ]
        )

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    observed = surface.observe_environment(env)

    assert observed["checks"]["no_unexpected_mounts"] is False
    assert {"type": "tmpfs", "destination": "/tmp/escape"} in observed["unexpected_mounts"]


def test_observe_environment_accepts_real_default_docker_environment(tmp_path: Path) -> None:
    if os.environ.get("VABENCH_TEST_DOCKER_RUNTIME") != "1":
        pytest.skip("opt-in Docker environment audit")
    from test_mini_swe_vabench import load_module

    mini = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public/task").mkdir(parents=True)
    (runtime / "public/task/instruction.md").write_text("Synthetic public task.\n", encoding="utf-8")
    (runtime / "public/submission").mkdir()
    env = mini.VaBenchBashEnvironment(
        runtime,
        timeout_s=30,
        sandbox_backend="docker",
        evas_command="",
        docker_image=os.environ.get("VABENCH_TEST_DOCKER_IMAGE", mini.DEFAULT_DOCKER_IMAGE),
        submission_gate=lambda _: {"passed": False},
    )
    try:
        env.preflight()
        observed = surface.observe_environment(env)
        assert observed["trusted_common_checks"] is True
        assert all(observed["checks"].values())
        assert observed["mounts"]["/workspace/public/task"]["rw"] is False
        assert observed["mounts"]["/workspace/public/submission"]["rw"] is True
        assert observed["image_id"] == env.docker_image_id
    finally:
        env.close()


def test_compare_surfaces_matches_common_fields_and_names_allowed_differences() -> None:
    left_request = surface.snapshot_request(
        {
            "model": "fixture-model",
            "temperature": 0,
            "max_tokens": 4096,
            "messages": [{"role": "system", "content": "legacy"}],
            "tools": [{"type": "function", "function": {"name": "legacy_bash"}}],
            "thinking": {"type": "disabled"},
            "stream_options": {"include_usage": True},
            "tool_choice": "auto",
            "configured_watchdog_s": 1800,
        },
        timeout_s=1799.5,
    )
    right_request = surface.snapshot_request(
        {
            "model": "fixture-model",
            "temperature": 0,
            "max_tokens": 4096,
            "messages": [{"role": "system", "content": "native"}],
            "tools": [{"type": "function", "function": {"name": "native_bash"}}],
            "thinking": {"type": "disabled"},
            "stream_options": {"include_usage": True},
            "tool_choice": "auto",
            "configured_watchdog_s": 1800,
        },
        timeout_s=1700,
    )
    left = {
        "public_runtime": _public_runtime_snapshot(),
        "environment": _environment_snapshot(),
        "request": left_request,
    }
    right = {
        "public_runtime": _public_runtime_snapshot(),
        "environment": _environment_snapshot(),
        "request": right_request,
    }

    comparison = surface.compare_surfaces(left, right)

    assert comparison["schema_version"] == "vaevas-comparison-surface-pair-v1"
    assert comparison["matches"]["public_runtime_tree"] is True
    assert comparison["matches"]["public_task_tree"] is True
    assert comparison["matches"]["initial_submission_tree"] is True
    assert comparison["matches"]["trusted_environment"] is True
    assert comparison["matches"]["image_id"] is True
    assert comparison["matches"]["model"] is True
    assert comparison["matches"]["decoding"] is True
    assert comparison["matches"]["provider_options"] is True
    assert comparison["matches"]["configured_watchdog_s"] is True
    assert comparison["matches"]["effective_timeout_within_watchdog"] is True
    assert comparison["permitted_differences"] == ["request", "system_messages", "tools"]
    assert comparison["claim"] == "surface_comparison_not_pure_parity"


def test_compare_surfaces_does_not_treat_matching_bad_or_missing_values_as_trusted() -> None:
    left = {
        "public_runtime": {"tree_sha256": None, "public_task_tree_sha256": None},
        "environment": {"trusted_common_checks": False, "image_id": None},
        "request": {"model": None, "decoding": {}, "configured_watchdog_s": 1800, "effective_timeout_s": 1801},
    }
    right = {
        "public_runtime": {"tree_sha256": None, "public_task_tree_sha256": None},
        "environment": {"trusted_common_checks": False, "image_id": None},
        "request": {"model": None, "decoding": {}, "configured_watchdog_s": 1800, "effective_timeout_s": 1801},
    }

    comparison = surface.compare_surfaces(left, right)

    assert comparison["matches"]["public_runtime_tree"] is False
    assert comparison["matches"]["trusted_environment"] is False
    assert comparison["matches"]["image_id"] is False
    assert comparison["matches"]["model"] is False
    assert comparison["matches"]["effective_timeout_within_watchdog"] is False
    assert comparison["all_common_checks_match"] is False


def test_compare_surfaces_treats_provider_option_mismatch_as_common_failure() -> None:
    left = {"public_runtime": _public_runtime_snapshot(), "environment": _environment_snapshot(),
            "request": _request_snapshot(thinking={"type": "disabled"})}
    right = {"public_runtime": _public_runtime_snapshot(), "environment": _environment_snapshot(),
             "request": _request_snapshot(thinking={"type": "enabled"})}

    comparison = surface.compare_surfaces(left, right)

    assert comparison["matches"]["provider_options"] is False
    assert comparison["all_common_checks_match"] is False


def test_compare_surfaces_fails_closed_on_inconsistent_supplied_snapshots() -> None:
    bad_public = _public_runtime_snapshot()
    bad_public["public_task_tree_sha256"] = "0" * 64
    bad_request = _request_snapshot()
    bad_request["request_sha256"] = "0" * 64
    bad_environment = _environment_snapshot()
    bad_environment["checks"]["network_none"] = False

    left = {"public_runtime": bad_public, "environment": bad_environment, "request": bad_request}
    right = {"public_runtime": _public_runtime_snapshot(), "environment": _environment_snapshot(),
             "request": _request_snapshot()}

    comparison = surface.compare_surfaces(left, right)

    assert comparison["matches"]["public_snapshot_self_consistent"] is False
    assert comparison["matches"]["request_snapshot_self_consistent"] is False
    assert comparison["matches"]["trusted_environment"] is False
    assert comparison["all_common_checks_match"] is False


def _public_runtime_snapshot() -> dict:
    public_task = {"instruction.md": {"bytes": 6, "sha256": "b" * 64}}
    submission = {}
    files = {"public/task/instruction.md": public_task["instruction.md"]}
    return {
        "schema_version": "vaevas-comparison-public-runtime-v1",
        "model_visible_files": files,
        "public_task_files": public_task,
        "initial_submission_files": submission,
        "public_aliases": {},
        "tree_sha256": surface.canonical_sha256({"files": files, "symlinks": {}}),
        "public_task_tree_sha256": surface.canonical_sha256(public_task),
        "initial_submission_tree_sha256": surface.canonical_sha256(submission),
    }


def _environment_snapshot() -> dict:
    checks = {
        "no_duplicate_mount_destinations": True,
        "no_unexpected_mounts": True,
        "expected_binds": True,
        "network_none": True,
        "read_only_rootfs": True,
        "capdrop_all": True,
        "image_id_matches_environment": True,
    }
    return {"trusted_common_checks": True, "checks": checks, "image_id": "sha256:" + "1" * 64}


def _request_snapshot(**overrides) -> dict:
    payload = {
        "model": "fixture-model",
        "temperature": 0,
        "max_tokens": 4096,
        "messages": [{"role": "system", "content": "same"}],
        "tools": [{"type": "function", "function": {"name": "bash"}}],
        "thinking": {"type": "disabled"},
        "stream_options": {"include_usage": True},
        "tool_choice": "auto",
        "configured_watchdog_s": 1800,
        **overrides,
    }
    return surface.snapshot_request(payload, timeout_s=1799)
