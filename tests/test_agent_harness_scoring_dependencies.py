"""Compatibility and one-way ownership of the scoring/launcher seam."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from test_agent_harness_native_episode import native_case as native_case  # noqa: F401
from test_agent_harness_production_public_validation import public_case as public_case  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"
sys.path.insert(0, str(CALIBRATION))


def test_old_imports_reexport_submission_and_evidence_owners(tmp_path):
    import campaign_telemetry
    import native_contracts
    import run_campaign as runner
    import run_native_mini_swe as launcher
    import submission_contract

    for name in (
        "safe_relative", "expected_candidate_artifacts", "submission_source_diagnostics",
        "submission_artifact_gate", "submit_artifacts_tool_schema",
    ):
        assert getattr(runner, name) is getattr(submission_contract, name)
    for name in ("model_event_hit_limit", "summarize_evas_invocations"):
        assert getattr(runner, name) is getattr(campaign_telemetry, name)
    assert runner.declared_information_surface is native_contracts.declared_information_surface
    assert launcher._backend_profile is native_contracts.backend_profile
    assert launcher._submit_artifacts_tool_descriptor is native_contracts.submit_artifacts_tool_descriptor

    # A fresh runtime goes through the same schema and gate via both imports.
    (tmp_path / "evaluator").mkdir()
    (tmp_path / "evaluator/score_policy.json").write_text(
        json.dumps({"candidate_artifacts": ["nested/model.va"]})
    )
    (tmp_path / "public/submission/nested").mkdir(parents=True)
    (tmp_path / "public/submission/nested/model.va").write_text("// candidate\n")
    assert runner.submission_artifact_gate(tmp_path)["passed"] is True
    descriptor = launcher._submit_artifacts_tool_descriptor(tmp_path)
    assert descriptor["argument_schema"]["properties"]["artifacts"]["required"] == ["nested/model.va"]
    (tmp_path / "public/submission/nested/model.va").write_text('include "../../secret.va"\n')
    assert runner.submission_artifact_gate(tmp_path)["passed"] is False


def test_scorer_cold_import_does_not_load_campaign_or_native_launcher(tmp_path):
    # A new interpreter catches both ordinary and spec_from_file_location imports.
    script = '''
import importlib.util
from pathlib import Path
import sys
path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("isolated_scorer", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.event_telemetry([])["model_calls"] == 0
for name in ("run_campaign", "v4_calibration_runner", "run_native_mini_swe"):
    assert name not in sys.modules, name
assert not hasattr(module, "RUNNER"), "scorer must import owners, not a launcher facade"
'''
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(CALIBRATION / "score_campaign.py")],
        cwd=tmp_path, text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_scorer_cli_remains_callable_outside_repository(tmp_path):
    result = subprocess.run(
        [sys.executable, str(CALIBRATION / "score_campaign.py"), "--help"],
        cwd=tmp_path, text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "--campaign" in result.stdout


def test_native_evidence_read_needs_no_launcher_import(native_case, tmp_path):  # noqa: F811
    import run_native_mini_swe as launcher
    import score_campaign
    from test_agent_harness_native_conditions import (
        Provider, _cell, _native_runtime, _submit_response,
    )

    arguments, _, _ = native_case
    runtime = _native_runtime(native_case, tmp_path, name="readonly-score-runtime")
    cell = {**_cell(arm="OneShot"), "family_id": "001"}
    launcher.run_prepared_native_mini_swe(
        runtime=runtime, cell=cell,
        client=Provider([_submit_response({"model.va": "module model; endmodule\n"})]),
        attempt_id="readonly", evas_command=arguments["evas_command"],
        campaign_file_sha256="c" * 64,
    )
    manifest = json.loads((runtime / "evidence/native-launcher/manifest.json").read_text())
    assert {"submission_contract.py", "campaign_telemetry.py", "native_contracts.py", "final_replay.py"} <= manifest["source_sha256"].keys()
    before = {str(path): path.read_bytes() for path in runtime.rglob("*") if path.is_file()}
    expected = score_campaign.read_native_cell(runtime, cell, campaign_file_sha256="c" * 64)
    script = '''
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import score_campaign
row = score_campaign.read_native_cell(Path(sys.argv[2]), json.loads(sys.argv[3]), campaign_file_sha256="c" * 64)
for name in ("run_campaign", "run_native_mini_swe", "v4_calibration_runner"):
    assert name not in sys.modules, name
print(json.dumps(row))
'''
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(CALIBRATION), str(runtime), json.dumps(cell)],
        cwd=tmp_path, text=True, capture_output=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected
    assert {str(path): path.read_bytes() for path in runtime.rglob("*") if path.is_file()} == before
