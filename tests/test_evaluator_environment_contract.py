from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify_evaluator_environment.py"
CONTRACT = ROOT / "environment" / "evaluator-contract.json"


def load_v3_runner():
    sys.path.insert(0, str(ROOT / "runners"))
    spec = importlib.util.spec_from_file_location(
        "run_vabench_v3_model_eval_contract_test",
        ROOT / "runners" / "run_vabench_v3_model_eval.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_environment_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_evaluator_environment_contract_test",
        VERIFIER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_verifier(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--json", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def live_pass_payload() -> dict:
    return {
        "schema_version": "vabench-evaluator-environment-verification-v1",
        "status": "pass",
        "source": {
            "repository": {
                "status": "available",
                "commit": "a" * 40,
                "dirty": False,
            }
        },
        "live_python": {"status": "pass", "observed_version": "3.11.13"},
        "live_evas": {
            "status": "pass",
            "command": "evas",
            "observed": {
                "package_name": "evas-sim",
                "package_version": "0.8.7",
                "engine": "evas-rust",
                "rust_core_present": True,
                "rust_core_loadable": True,
                "rust_core_abi_version": 20260718,
                "rust_core_version": "0.2.4",
            },
        },
    }


def test_static_environment_contract_verifier_passes_without_host_evas() -> None:
    completed = run_verifier()
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert payload["status"] == "pass"
    assert payload["live_python"]["status"] == "not_checked"
    assert payload["live_evas"]["status"] == "not_checked"
    assert payload["source"]["repository"]["commit"]
    assert payload["source"]["files"]["requirements_lock"]["exists"] is True
    assert payload["failures"] == []


def test_environment_contract_records_pinned_runtime_and_boundaries() -> None:
    contract = read_json(CONTRACT)

    assert contract["python"]["version"] == "3.11.13"
    assert contract["dependencies"]["packages"]["evas-sim"] == "0.8.7"
    assert contract["evaluator"]["evas"] == {
        "package_name": "evas-sim",
        "package_version": "0.8.7",
        "engine": "evas-rust",
        "rust_core_present": True,
        "rust_core_loadable": True,
        "rust_core_abi_version": 20260718,
        "rust_core_version": "0.2.4",
    }
    assert contract["runtime_boundary"]["network"] == "none"
    assert contract["runtime_boundary"]["root_filesystem"] == "read-only"
    assert "/workspace/evaluator" in contract["runtime_boundary"]["forbidden_model_paths"]
    assert "/opt/benchmark" in contract["runtime_boundary"]["forbidden_model_paths"]


def test_environment_contract_verifier_fails_closed_on_mismatch(tmp_path: Path) -> None:
    bad_contract = tmp_path / "evaluator-contract.json"
    payload = read_json(CONTRACT)
    payload["evaluator"]["evas"]["package_version"] = "0.8.6"
    bad_contract.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    completed = run_verifier("--contract", str(bad_contract))
    report = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert report["status"] == "fail"
    assert any(item["check"] == "evas_package_version" for item in report["failures"])


def test_environment_contract_verifier_accepts_live_evas_identity(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    fake_evas = tmp_path / "evas"
    fake_evas.write_text(
        "#!/bin/sh\n"
        "cat <<'JSON'\n"
        "{\n"
        '  "schema_version": 1,\n'
        '  "package_name": "evas-sim",\n'
        '  "package_version": "0.8.7",\n'
        '  "cli_version": "0.8.7",\n'
        '  "engine": "evas-rust",\n'
        '  "rust_core_present": true,\n'
        '  "rust_core_loadable": true,\n'
        '  "rust_core_abi_version": 20260718,\n'
        '  "rust_core_version": "0.2.4",\n'
        '  "build_revision": null\n'
        "}\n"
        "JSON\n",
        encoding="utf-8",
    )
    fake_evas.chmod(0o755)

    verifier = load_environment_verifier()
    monkeypatch.setattr(verifier.platform, "python_version", lambda: "3.11.13")
    monkeypatch.setattr(
        verifier,
        "repository_identity",
        lambda _root: {
            "status": "available",
            "commit": "a" * 40,
            "dirty": False,
            "tracked_changes": False,
            "untracked_file_count": 0,
        },
    )
    rc = verifier.main(["--run-evas", "--evas-command", str(fake_evas), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["live_evas"]["status"] == "pass"


def test_v3_claim_gate_requires_live_environment_evidence(tmp_path: Path) -> None:
    module = load_v3_runner()
    no_live = tmp_path / "no-live.json"
    no_live.write_text(
        json.dumps(
            {
                "schema_version": "vabench-evaluator-environment-verification-v1",
                "status": "pass",
                "live_python": {"status": "pass"},
                "live_evas": {"status": "not_checked"},
            }
        ),
        encoding="utf-8",
    )
    live = tmp_path / "live.json"
    live.write_text(json.dumps(live_pass_payload()), encoding="utf-8")

    no_live_args = module.parse_args(["--environment-evidence", str(no_live)])
    live_args = module.parse_args(["--environment-evidence", str(live)])

    _, no_live_problems = module.environment_evidence(no_live_args)
    _, live_problems = module.environment_evidence(live_args)

    assert "environment_live_evas_not_verified" in no_live_problems
    assert live_problems == []

    wrong_python = live_pass_payload()
    wrong_python["live_python"]["observed_version"] = "3.12.1"
    wrong_python_path = tmp_path / "wrong-python.json"
    wrong_python_path.write_text(json.dumps(wrong_python), encoding="utf-8")
    wrong_python_args = module.parse_args(
        ["--environment-evidence", str(wrong_python_path)]
    )
    _, wrong_python_problems = module.environment_evidence(wrong_python_args)
    assert "environment_live_python_version_mismatch" in wrong_python_problems


def test_single_task_hidden_scoring_smoke_binds_claim_boundary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = load_v3_runner()
    slug = "001-bang-bang-phase-detector"
    model = "smoke-model"
    generated_sample = tmp_path / "generated" / model / slug / "sample_0"
    generated_sample.mkdir(parents=True)
    shutil.copyfile(
        ROOT / "benchmark-vabench-release-v3" / "tasks" / slug / "solution" / "bbpd_ref.va",
        generated_sample / "bbpd_ref.va",
    )
    env_evidence = tmp_path / "live-environment.json"
    env_evidence.write_text(json.dumps(live_pass_payload()), encoding="utf-8")
    seen: dict[str, str] = {}

    def fake_run_case(directory, primary, tb_path, *, output_root, timeout_s, task_id_override):
        seen["directory"] = str(directory)
        seen["primary"] = str(primary)
        seen["tb_path"] = str(tb_path)
        output_root.mkdir(parents=True)
        (output_root / "tran.csv").write_text("time,up,down\n0,0,0\n", encoding="utf-8")
        (output_root / "evas_identity.json").write_text(
            json.dumps(live_pass_payload()["live_evas"]["observed"]),
            encoding="utf-8",
        )
        return {
            "status": "PASS",
            "checker_task_id": task_id_override,
            "scores": {
                "dut_compile": 1,
                "tb_compile": 1,
                "sim_correct": 1,
                "weighted_total": 1,
            },
            "notes": [],
            "timing": {"timeout_s": timeout_s},
        }

    monkeypatch.setattr(module, "run_case", fake_run_case)
    monkeypatch.setattr(
        module,
        "repository_identity",
        lambda _root: {
            "status": "available",
            "commit": "a" * 40,
            "dirty": False,
        },
    )
    monkeypatch.setattr(module.platform, "python_version", lambda: "3.11.13")
    rc = module.main(
        [
            "--stage",
            "score",
            "--selection-surface",
            "candidate",
            "--task",
            slug,
            "--model",
            model,
            "--generated-root",
            str(tmp_path / "generated"),
            "--output-root",
            str(tmp_path / "out"),
            "--score-workers",
            "1",
            "--environment-evidence",
            str(env_evidence),
            "--claim-scope",
            "formal_model_score",
            "--json",
        ]
    )

    summary = read_json(tmp_path / "out" / "summary.json")
    result = read_json(tmp_path / "out" / "evas_results" / slug / "result.json")

    assert rc == 2
    assert "/test_hidden/" in seen["tb_path"]
    assert seen["primary"].endswith("/public/submission") is False
    assert result["status"] == "PASS"
    assert result["claim_allowed"] is False
    assert summary["scored_rows"] == 1
    assert summary["claim_gate"]["environment_verified"] is True
    assert summary["claim_gate"]["allowed"] is False
    assert summary["claim_gate"]["blocking_reasons"] == [
        "selection_surface_is_not_counted",
        "selected_row_not_counted_in_score",
        "formal_denominator_is_filtered",
        "frozen_counted_denominator_is_empty",
    ]
