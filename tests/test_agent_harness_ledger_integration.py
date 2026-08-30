"""The report CLI creates safe ledgers only from verified native score rows."""

import json
import sys

import pytest

from test_agent_harness_result_ledger import _campaign, _row
from run_native_attempts import retry_policy
import score_campaign as scorer


def test_score_cli_exports_separate_safe_ledger(tmp_path, monkeypatch):
    campaign = _campaign()
    campaign["execution_config"]["native_retry_policy"] = retry_policy(1).to_document()
    campaign_path = tmp_path / "campaign.json"
    campaign_path.write_text(json.dumps(campaign))
    run_root = tmp_path / "run"
    run_root.mkdir()
    rows = {cell["cell_id"]: _row(cell, score=1, status="passed") for cell in campaign["cells"]}
    reads = []

    def read(runtime, cell, **kwargs):
        reads.append(cell["cell_id"])
        return rows[cell["cell_id"]]

    monkeypatch.setattr(scorer, "read_native_cell", read)
    output = tmp_path / "report.json"
    ledger = tmp_path / "reviewer-ledger.json"
    monkeypatch.setattr(sys, "argv", [
        "score_campaign.py", "--campaign", str(campaign_path),
        "--campaign-output", str(run_root), "--episode-backend", "native-mini-swe",
        "--judge-kind", "final_trusted_replay", "--output", str(output),
        "--ledger-output", str(ledger),
    ])
    assert scorer.main() == 0
    result = json.loads(ledger.read_text())
    assert result["denominator"]["scheduled_cells"] == 3
    assert result["denominator"]["eligible_actual_score_cells"] == 3
    assert sorted(reads) == sorted(rows)
    assert "do not leak" not in ledger.read_text()
    assert json.loads(output.read_text())["result_ledger"]["ledger_sha256"] == result["ledger_sha256"]


@pytest.mark.parametrize("target", ["campaign", "runtime", "report"])
def test_ledger_output_cannot_overwrite_generation_or_report(tmp_path, monkeypatch, target):
    campaign = tmp_path / "campaign.json"
    campaign.write_text("untouched campaign")
    run_root = tmp_path / "run"
    run_root.mkdir()
    output = tmp_path / "report.json"
    ledger = {"campaign": campaign, "runtime": run_root / "evidence.json", "report": output}[target]
    monkeypatch.setattr(sys, "argv", [
        "score_campaign.py", "--campaign", str(campaign), "--campaign-output", str(run_root),
        "--episode-backend", "native-mini-swe", "--judge-kind", "final_trusted_replay",
        "--output", str(output), "--ledger-output", str(ledger),
    ])
    with pytest.raises(ValueError, match="ledger output"):
        scorer.main()
    assert campaign.read_text() == "untouched campaign"
