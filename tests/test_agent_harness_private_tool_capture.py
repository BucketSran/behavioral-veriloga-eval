from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "mini_swe_vabench.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "mini_swe_vabench_private_capture_test", MODULE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def artifact_gate(runtime: Path) -> dict:
    artifact = runtime / "public" / "submission" / "model.va"
    return {
        "passed": artifact.is_file() and not artifact.is_symlink(),
        "diagnostics": [],
        "artifact_sha256": {},
    }


def test_bash_environment_can_emit_private_pre_model_output_capture(
    tmp_path: Path,
) -> None:
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    (runtime / "public" / "submission").mkdir(parents=True)
    captures: list[dict] = []
    environment = module.VaBenchBashEnvironment(
        runtime,
        timeout_s=5,
        sandbox_backend="none",
        evas_command="/usr/bin/true",
        submission_gate=artifact_gate,
        private_output_sink=captures.append,
    )

    result = environment.execute({"command": "printf 'fixture-private-output'"})

    assert result["returncode"] == 0
    assert result["output"] == "fixture-private-output"
    assert captures == [
        {
            "schema_version": "vabench-private-tool-output-capture-v1",
            "tool_name": "bash",
            "returncode": 0,
            "elapsed_s": captures[0]["elapsed_s"],
            "output_sha256": hashlib.sha256(b"fixture-private-output").hexdigest(),
            "output_total_bytes": len(b"fixture-private-output"),
            "output_captured_bytes": len(b"fixture-private-output"),
            "output_truncated_bytes": 0,
            "output_capture_complete": True,
            "output_capture_eof": True,
            "output_capture_read_error": False,
            "retained_output_scope": "bounded_head_tail_pre_model_capture",
            "output": "fixture-private-output",
            "resources": captures[0]["resources"],
        }
    ]
    assert captures[0]["elapsed_s"] >= 0
    assert captures[0]["resources"]["exceeded"] == []


def test_private_capture_keeps_model_visible_output_clipped(
    tmp_path: Path,
) -> None:
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    (runtime / "public" / "submission").mkdir(parents=True)
    captures: list[dict] = []
    environment = module.VaBenchBashEnvironment(
        runtime,
        timeout_s=5,
        sandbox_backend="none",
        evas_command="/usr/bin/true",
        submission_gate=artifact_gate,
        private_output_sink=captures.append,
    )
    payload = "x" * (module.MODEL_OUTPUT_BYTES + 100)

    result = environment.execute({
        "command": f"head -c {len(payload)} /dev/zero | tr '\\0' x"
    })

    assert len(result["output"].encode("utf-8")) < len(payload)
    assert result["output"] != captures[0]["output"]
    assert captures[0]["output"] == payload
    assert captures[0]["output_sha256"] == hashlib.sha256(payload.encode()).hexdigest()
    assert captures[0]["output_capture_complete"] is True


def test_private_capture_retains_bounded_text_but_hashes_full_stream(
    tmp_path: Path,
) -> None:
    module = load_module()
    runtime = tmp_path / "runtime"
    (runtime / "public" / "task").mkdir(parents=True)
    (runtime / "public" / "submission").mkdir(parents=True)
    captures: list[dict] = []
    environment = module.VaBenchBashEnvironment(
        runtime,
        timeout_s=5,
        sandbox_backend="none",
        evas_command="/usr/bin/true",
        submission_gate=artifact_gate,
        private_output_sink=captures.append,
    )
    payload = (
        "a" * module.COMMAND_OUTPUT_HEAD_BYTES
        + "b" * 257
        + "c" * (module.COMMAND_OUTPUT_CAPTURE_BYTES - module.COMMAND_OUTPUT_HEAD_BYTES)
    )

    environment.execute({
        "command": (
            "python3 - <<'PY'\n"
            f"import sys\nsys.stdout.write('a' * {module.COMMAND_OUTPUT_HEAD_BYTES})\n"
            "sys.stdout.write('b' * 257)\n"
            "sys.stdout.write('c' * "
            f"{module.COMMAND_OUTPUT_CAPTURE_BYTES - module.COMMAND_OUTPUT_HEAD_BYTES})\n"
            "PY"
        )
    })

    capture = captures[0]
    assert capture["output_sha256"] == hashlib.sha256(payload.encode()).hexdigest()
    assert capture["output_total_bytes"] == len(payload)
    assert capture["output_captured_bytes"] == module.COMMAND_OUTPUT_CAPTURE_BYTES
    assert capture["output_truncated_bytes"] == 257
    assert "vaBench truncated 257 command-output bytes" in capture["output"]
    assert "b" * 257 not in capture["output"]
    assert capture["output_capture_complete"] is True
    assert capture["retained_output_scope"] == "bounded_head_tail_pre_model_capture"
