from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "runners" / "feedback_oracle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("v4_feedback_oracle", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_oracle_timeout_uses_runner_override(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    monkeypatch.setenv("VABENCH_ORACLE_TIMEOUT_S", "180")

    assert module._oracle_timeout(60) == 180


def test_oracle_timeout_rejects_invalid_override(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_module()
    monkeypatch.setenv("VABENCH_ORACLE_TIMEOUT_S", "0")

    with pytest.raises(SystemExit, match="positive integer"):
        module._oracle_timeout(60)


def test_task_wrapper_python_default_does_not_override_runner_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    monkeypatch.setenv("EVAS_ENGINE", "evas-rust")

    assert not module._task_wrapper_may_select_python(True)


def test_task_wrapper_python_default_applies_without_runner_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_module()
    monkeypatch.delenv("EVAS_ENGINE", raising=False)

    assert module._task_wrapper_may_select_python(True)


def test_standalone_rust_frontend_requires_and_verifies_binary_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = load_module()
    binary = tmp_path / "evas_rust_frontend"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    monkeypatch.setenv("VABENCH_EVAS_IMPLEMENTATION", "standalone-rust")
    monkeypatch.setenv("VABENCH_EVAS_RUST_FRONTEND", str(binary))
    monkeypatch.setenv("VABENCH_EVAS_RUST_FRONTEND_SHA256", digest)

    assert module._standalone_rust_frontend() == (binary.resolve(), digest)


def test_standalone_rust_frontend_rejects_binary_hash_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = load_module()
    binary = tmp_path / "evas_rust_frontend"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    monkeypatch.setenv("VABENCH_EVAS_IMPLEMENTATION", "standalone-rust")
    monkeypatch.setenv("VABENCH_EVAS_RUST_FRONTEND", str(binary))
    monkeypatch.setenv("VABENCH_EVAS_RUST_FRONTEND_SHA256", "0" * 64)

    with pytest.raises(SystemExit, match="hash mismatch"):
        module._standalone_rust_frontend()


def test_standalone_rust_frontend_runs_without_python_simulator(tmp_path: Path) -> None:
    module = load_module()
    binary = tmp_path / "evas_rust_frontend"
    binary.write_text(
        "#!/bin/sh\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output\" ]; then shift; out=$1; fi\n"
        "  shift\n"
        "done\n"
        "printf 'time,out\\n0,0\\n' > \"$out\"\n"
        "printf 'PASS points=1 output=%s\\n' \"$out\"\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    tb = run_dir / "tb.scs"
    tb.write_text("simulator lang=spectre\n", encoding="utf-8")

    result = module._run_standalone_rust_frontend(
        binary, run_dir, tb, run_dir / "out", timeout_s=5
    )

    assert result.returncode == 0
    assert result.stdout.startswith("PASS ")
    assert (run_dir / "out" / "tran.csv").read_text(encoding="utf-8") == "time,out\n0,0\n"


def test_copy_candidate_sources_preserves_declared_artifact_paths(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "candidate"
    run_dir = tmp_path / "run"
    (source / "blocks").mkdir(parents=True)
    (source / "top.va").write_text("module top; endmodule\n", encoding="utf-8")
    (source / "blocks" / "leaf.va").write_text("module leaf; endmodule\n", encoding="utf-8")
    (source / "unrequested.va").write_text("module unused; endmodule\n", encoding="utf-8")

    module._copy_candidate_sources(
        source,
        run_dir,
        ["top.va", "blocks/leaf.va"],
        generated_harness=True,
    )

    assert (run_dir / "dut" / "top.va").is_file()
    assert (run_dir / "dut" / "blocks" / "leaf.va").is_file()
    assert not (run_dir / "dut" / "unrequested.va").exists()


def test_copy_candidate_sources_rejects_missing_declared_artifact(tmp_path: Path) -> None:
    module = load_module()
    source = tmp_path / "candidate"
    source.mkdir()

    with pytest.raises(SystemExit, match="missing target artifact"):
        module._copy_candidate_sources(
            source,
            tmp_path / "run",
            ["missing.va"],
            generated_harness=True,
        )


def test_copy_public_support_enforces_hash_modules_and_separate_mount(tmp_path: Path) -> None:
    module = load_module()
    task = tmp_path / "001-demo"
    candidate = tmp_path / "candidate"
    run = tmp_path / "run"
    candidate.mkdir()
    (candidate / "dut.va").write_text("module dut; endmodule\n", encoding="utf-8")
    support = task / "public_support" / "helper.va"
    support.parent.mkdir(parents=True)
    support.write_text("module helper; endmodule\n", encoding="utf-8")
    support_hash = hashlib.sha256(support.read_bytes()).hexdigest()
    (task / "evaluator").mkdir()
    (task / "family_spec.json").write_text(
        json.dumps(
            {
                "support_contract": {
                    "visibility": "public_readonly",
                    "source_root": "public_support",
                    "mount_root": "support",
                    "files": [
                        {"path": "helper.va", "sha256": support_hash, "modules": ["helper"]}
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    (task / "evaluator" / "harness_spec.json").write_text(
        json.dumps(
            {"support": {"source_root": "./support", "artifact_paths": ["helper.va"]}}
        ),
        encoding="utf-8",
    )

    module._copy_public_support(task, candidate, run, ["dut.va"])

    assert (run / "support" / "helper.va").read_bytes() == support.read_bytes()


def test_copy_public_support_rejects_candidate_module_collision(tmp_path: Path) -> None:
    module = load_module()
    task = tmp_path / "001-demo"
    candidate = tmp_path / "candidate"
    run = tmp_path / "run"
    candidate.mkdir()
    (candidate / "dut.va").write_text("module helper; endmodule\n", encoding="utf-8")
    support = task / "public_support" / "helper.va"
    support.parent.mkdir(parents=True)
    support.write_text("module helper; endmodule\n", encoding="utf-8")
    (task / "evaluator").mkdir()
    (task / "family_spec.json").write_text(
        json.dumps(
            {
                "support_contract": {
                    "visibility": "public_readonly",
                    "source_root": "public_support",
                    "mount_root": "support",
                    "files": [
                        {
                            "path": "helper.va",
                            "sha256": hashlib.sha256(support.read_bytes()).hexdigest(),
                            "modules": ["helper"],
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    (task / "evaluator" / "harness_spec.json").write_text(
        json.dumps(
            {"support": {"source_root": "./support", "artifact_paths": ["helper.va"]}}
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="collides"):
        module._copy_public_support(task, candidate, run, ["dut.va"])


def test_side_effect_crossing_time_is_checked_against_trace(tmp_path: Path) -> None:
    module = load_module()
    output = tmp_path / "out"
    output.mkdir()
    trace = output / "tran.csv"
    trace.write_text("time,vin\n0,0\n1e-9,0\n2e-9,0.9\n3e-9,0.9\n", encoding="utf-8")
    (output / "metric.out").write_text("cross 1.5e-9\n", encoding="utf-8")
    profile = {
        "side_effect_contract": {
            "exclusive_suffix": ".out",
            "files": [
                {
                    "path": "metric.out",
                    "validator": "first_rising_crossing_time",
                    "record_pattern": r"cross (?P<time>[0-9.eE+-]+)\n",
                    "signal": "vin",
                    "threshold": 0.45,
                    "tolerance_s": 1e-15,
                }
            ],
        }
    }

    ok, notes = module._validate_side_effect_contract(profile, trace, output)

    assert ok
    assert "expected=1.5e-09" in notes[0]


def test_side_effect_count_metric_reports_observed_gap(tmp_path: Path) -> None:
    module = load_module()
    output = tmp_path / "out"
    output.mkdir()
    trace = output / "tran.csv"
    trace.write_text(
        "time,ref\n0,0\n1e-9,0.9\n2e-9,0\n3e-9,0.9\n4e-9,0\n",
        encoding="utf-8",
    )
    (output / "candidate.out").write_text("count=1 metric=0.250", encoding="utf-8")
    profile = {
        "side_effect_contract": {
            "files": [
                {
                    "path": "candidate.out",
                    "validator": "rising_edge_count_metric",
                    "record_pattern": r"count=(?P<count>[0-9]+) metric=(?P<metric>[0-9.]+)",
                    "signal": "ref",
                    "threshold": 0.45,
                    "metric_divisor": 4.0,
                    "metric_tolerance": 0.0005,
                }
            ]
        }
    }

    ok, notes = module._validate_side_effect_contract(profile, trace, output)

    assert not ok
    assert "expected_count=2 observed_count=1" in notes[0]
