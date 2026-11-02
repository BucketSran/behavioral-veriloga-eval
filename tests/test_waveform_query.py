from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WAVEFORM_QUERY = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "waveform_query.py"
)


def load_waveform_query():
    spec = importlib.util.spec_from_file_location("waveform_query_test", WAVEFORM_QUERY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_trace(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "time,clk,out,analog",
                "0.0,0,0,0.0",
                "1.0,0,0,1.0",
                "2.0,1,0,2.0",
                "3.0,1,1,3.0",
                "4.0,0,1,4.0",
                "5.0,0,0,5.0",
                "6.0,1,0,6.0",
                "7.0,1,1,7.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_cli(trace: Path, allowed_root: Path, *args: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(WAVEFORM_QUERY),
            "--trace",
            str(trace),
            "--allowed-root",
            str(allowed_root),
            *args,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    if completed.returncode:
        raise AssertionError(payload)
    return payload


def test_summary_lists_signals_and_numeric_ranges(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)

    result = run_cli(trace, tmp_path, "summary")

    assert result["ok"] is True
    assert result["row_count"] == 8
    assert result["signals"] == ["clk", "out", "analog"]
    assert result["stats"]["analog"] == {"first": 0.0, "last": 7.0, "max": 7.0, "min": 0.0}


def test_crossings_use_linear_interpolation_and_direction(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)

    result = run_cli(
        trace,
        tmp_path,
        "crossings",
        "--signal",
        "clk",
        "--threshold",
        "0.5",
        "--direction",
        "rising",
    )

    assert [event["time"] for event in result["events"]] == [1.5, 5.5]
    assert {event["direction"] for event in result["events"]} == {"rising"}


def test_sample_supports_linear_previous_and_event_objects(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)

    linear = run_cli(
        trace,
        tmp_path,
        "sample",
        "--signal",
        "analog",
        "--times",
        "1.5,2.25",
        "--method",
        "linear",
    )
    previous = run_cli(
        trace,
        tmp_path,
        "sample",
        "--signal",
        "analog",
        "--event-times",
        '[{"label":"late","time":2.25}]',
        "--method",
        "previous",
    )

    assert [sample["value"] for sample in linear["samples"]] == [1.5, 2.25]
    assert previous["samples"] == [
        {"label": "late", "method": "previous", "source_time": 2.0, "time": 2.25, "value": 2.0}
    ]


def test_cycles_and_pair_events_are_task_agnostic(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)

    cycles = run_cli(
        trace,
        tmp_path,
        "cycles",
        "--signal",
        "clk",
        "--threshold",
        "0.5",
        "--direction",
        "rising",
    )
    pairs = run_cli(
        trace,
        tmp_path,
        "pair",
        "--request-signal",
        "clk",
        "--request-threshold",
        "0.5",
        "--response-signal",
        "out",
        "--response-threshold",
        "0.5",
    )

    assert cycles["periods"] == [4.0]
    assert cycles["period_mean"] == 4.0
    assert pairs["pairs"] == [
        {"latency": 1.0, "request_time": 1.5, "response_time": 2.5},
        {"latency": 1.0, "request_time": 5.5, "response_time": 6.5},
    ]


def test_compare_samples_baseline_times_with_bounded_output(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    baseline = tmp_path / "baseline.csv"
    write_trace(trace)
    baseline.write_text("time,analog\n1.5,1.0\n2.5,3.0\n", encoding="utf-8")

    result = run_cli(
        trace,
        tmp_path,
        "--max-results",
        "1",
        "compare",
        "--baseline-trace",
        str(baseline),
        "--signal",
        "analog",
    )

    assert result["sample_count"] == 1
    assert result["truncated"] is True
    assert result["samples"] == [
        {
            "baseline": 1.0,
            "candidate": 1.5,
            "difference": 0.5,
            "time": 1.5,
        }
    ]


def test_output_vocabulary_does_not_claim_or_reveal_judge_answers(
    tmp_path: Path,
) -> None:
    trace = tmp_path / "tran.csv"
    baseline = tmp_path / "baseline.csv"
    write_trace(trace)
    baseline.write_text("time,analog\n1.5,1.0\n", encoding="utf-8")

    payload = run_cli(
        trace,
        tmp_path,
        "compare",
        "--baseline-trace",
        str(baseline),
        "--signal",
        "analog",
    )
    serialized = json.dumps(payload).lower()

    for forbidden in ("pass", "fail", "checker", "property", "expected", "gold"):
        assert forbidden not in serialized


def test_rejects_trace_outside_allowed_root_and_symlink_escape(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    symlink = allowed / "escape.csv"
    symlink.symlink_to(trace)

    completed = subprocess.run(
        [
            sys.executable,
            str(WAVEFORM_QUERY),
            "--trace",
            str(symlink),
            "--allowed-root",
            str(allowed),
            "summary",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["ok"] is False


def test_cli_usage_errors_are_json_without_stderr() -> None:
    completed = subprocess.run(
        [sys.executable, str(WAVEFORM_QUERY), "summary"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False
    assert "--trace" in payload["error"]


def test_module_api_remains_stdlib_and_returns_jsonable_payload(tmp_path: Path) -> None:
    trace = tmp_path / "tran.csv"
    write_trace(trace)
    module = load_waveform_query()

    result = module.run(
        [
            "--trace",
            str(trace),
            "--allowed-root",
            str(tmp_path),
            "crossings",
            "--signal",
            "out",
            "--threshold",
            "0.5",
        ]
    )

    assert result["ok"] is True
    assert json.loads(json.dumps(result))["events"][0]["time"] == 2.5
