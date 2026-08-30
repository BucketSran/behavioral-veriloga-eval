from __future__ import annotations

import json
import os

from runners.agent_harness.tools.waveform_summary import (
    MAX_BYTES,
    MAX_COLUMNS,
    MAX_DATA_ROWS,
    MAX_RETURNED_SIGNALS,
    summarize_waveform,
    waveform_policy,
    waveform_policy_sha256,
)


def test_missing_tran_csv_returns_diagnostic_without_verdict(tmp_path) -> None:
    summary = summarize_waveform(tmp_path)

    assert summary["schema_version"] == "vaevas-waveform-summary-v1"
    assert summary["status"] == "missing"
    assert summary["relative_path"] == "tran.csv"
    assert summary["signals"] == []
    assert "passed" not in summary
    assert "score" not in summary
    assert waveform_policy()["relative_path"] == "tran.csv"
    assert len(waveform_policy_sha256()) == 64


def test_available_summary_counts_finite_nonfinite_and_empty_cells(tmp_path) -> None:
    (tmp_path / "tran.csv").write_text(
        "time,vout,iout\n"
        "0,1.0,NaN\n"
        "1,2.0,\n"
        "2,Inf,-3.0\n",
        encoding="utf-8",
    )

    summary = summarize_waveform(tmp_path)

    assert summary["status"] == "available"
    assert summary["scanned_rows"] == 3
    assert summary["returned_signals"] == 3
    assert len(summary["source_sha256"]) == 64
    assert summary["signals"][1] == {
        "name": "vout",
        "unit": None,
        "finite_count": 2,
        "nonfinite_count": 1,
        "empty_count": 0,
        "min": 1.0,
        "max": 2.0,
        "mean": 1.5,
        "first": 1.0,
        "last": 2.0,
    }
    assert summary["signals"][2]["finite_count"] == 1
    assert summary["signals"][2]["nonfinite_count"] == 1
    assert summary["signals"][2]["empty_count"] == 1
    json.dumps(summary, allow_nan=False)


def test_finite_extreme_values_do_not_emit_json_infinity(tmp_path) -> None:
    (tmp_path / "tran.csv").write_text(
        "time,vout\n"
        "0,1e308\n"
        "1,1e308\n",
        encoding="utf-8",
    )

    summary = summarize_waveform(tmp_path)

    assert summary["status"] == "available"
    assert summary["signals"][1]["mean"] == 1e308
    json.dumps(summary, allow_nan=False)


def test_opposite_extreme_values_do_not_emit_json_infinity(tmp_path) -> None:
    (tmp_path / "tran.csv").write_text(
        "time,vout\n"
        "0,1e308\n"
        "1,-1e308\n",
        encoding="utf-8",
    )

    summary = summarize_waveform(tmp_path)

    assert summary["status"] == "available"
    assert summary["signals"][1]["mean"] == 0.0
    json.dumps(summary, allow_nan=False)


def test_invalid_csv_rejects_duplicate_ragged_nonnumeric_and_bad_utf8(tmp_path) -> None:
    (tmp_path / "tran.csv").write_text("time,time\n0,1\n", encoding="utf-8")
    assert summarize_waveform(tmp_path)["invalid_reason"] == "duplicate_header"

    (tmp_path / "tran.csv").write_text("time,vout\n0\n", encoding="utf-8")
    assert summarize_waveform(tmp_path)["invalid_reason"] == "ragged_row"

    (tmp_path / "tran.csv").write_text("time,vout\n0,abc\n", encoding="utf-8")
    nonnumeric = summarize_waveform(tmp_path)
    assert nonnumeric["status"] == "invalid"
    assert nonnumeric["invalid_reason"] == "nonnumeric_cell"

    (tmp_path / "tran.csv").write_bytes(b"time,vout\n0,\xff\n")
    assert summarize_waveform(tmp_path)["invalid_reason"] == "invalid_utf8"


def test_invalid_details_do_not_echo_long_header_or_cell_content(tmp_path) -> None:
    long_name = "v" * 129
    (tmp_path / "tran.csv").write_text(f"time,{long_name}\n0,1\n", encoding="utf-8")
    long_header = summarize_waveform(tmp_path)
    assert long_header["invalid_reason"] == "invalid_header"
    assert "invalid_detail" not in long_header

    long_cell = "9" * 1024
    (tmp_path / "tran.csv").write_text(f"time,vout\n0,{long_cell}x\n", encoding="utf-8")
    long_bad_cell = summarize_waveform(tmp_path)
    assert long_bad_cell["invalid_reason"] == "nonnumeric_cell"
    assert "invalid_detail" not in long_bad_cell


def test_malformed_quoted_csv_rejects_instead_of_guessing(tmp_path) -> None:
    (tmp_path / "tran.csv").write_text('time,"vout\n0,1\n', encoding="utf-8")

    malformed = summarize_waveform(tmp_path)

    assert malformed["status"] == "invalid"
    assert malformed["invalid_reason"] == "csv_parse_error"


def test_invalid_cells_beyond_column_cap_are_not_ignored(tmp_path) -> None:
    rows = ["c" + str(index) for index in range(MAX_COLUMNS + 1)]
    values = ["1" for _ in range(MAX_COLUMNS)] + ["not-a-number"]
    (tmp_path / "tran.csv").write_text(
        ",".join(rows) + "\n" + ",".join(values) + "\n",
        encoding="utf-8",
    )

    capped = summarize_waveform(tmp_path)

    assert capped["status"] == "invalid"
    assert capped["invalid_reason"] == "too_many_columns"


def test_limits_are_diagnostic_not_verdicts(tmp_path) -> None:
    (tmp_path / "tran.csv").write_bytes(b"t,v\n" + (b"0,1\n" * ((MAX_BYTES // 4) + 1)))
    too_large = summarize_waveform(tmp_path)
    assert too_large["status"] == "too_large"
    assert too_large["source_sha256"] is None
    assert "passed" not in too_large
    assert "score" not in too_large

    rows = ["c" + str(index) for index in range(MAX_COLUMNS + 2)]
    (tmp_path / "tran.csv").write_text(
        ",".join(rows) + "\n" + ",".join("1" for _ in rows) + "\n",
        encoding="utf-8",
    )
    column_limited = summarize_waveform(tmp_path)
    assert column_limited["status"] == "invalid"
    assert column_limited["invalid_reason"] == "too_many_columns"

    (tmp_path / "tran.csv").write_text(
        "time,vout\n" + ("0,1\n" * (MAX_DATA_ROWS + 1)),
        encoding="utf-8",
    )
    row_limited = summarize_waveform(tmp_path)
    assert row_limited["status"] == "truncated"
    assert row_limited["scanned_rows"] == MAX_DATA_ROWS
    assert row_limited["total_data_rows_seen"] == MAX_DATA_ROWS + 1
    assert row_limited["incomplete_scan"] is True


def test_more_than_returned_signal_cap_is_truncated_even_within_column_cap(tmp_path) -> None:
    rows = ["c" + str(index) for index in range(MAX_RETURNED_SIGNALS + 1)]
    (tmp_path / "tran.csv").write_text(
        ",".join(rows) + "\n" + ",".join("1" for _ in rows) + "\n",
        encoding="utf-8",
    )

    signal_limited = summarize_waveform(tmp_path)

    assert signal_limited["status"] == "truncated"
    assert signal_limited["returned_signals"] == MAX_RETURNED_SIGNALS
    assert signal_limited["omitted_signals"] == 1


def test_path_safety_rejects_symlink_roots_ancestors_and_nonregular_file(tmp_path) -> None:
    outside = tmp_path / "outside.csv"
    outside.write_text("time,vout\n0,1\n", encoding="utf-8")
    os.symlink(outside, tmp_path / "tran.csv")

    symlink = summarize_waveform(tmp_path)

    assert symlink["status"] == "invalid"
    assert symlink["invalid_reason"] == "path_is_symlink"
    assert symlink["source_sha256"] is None

    (tmp_path / "tran.csv").unlink()
    real_root = tmp_path / "real-root"
    real_root.mkdir()
    (real_root / "tran.csv").write_text("time,vout\n0,1\n", encoding="utf-8")
    linked_root = tmp_path / "linked-root"
    os.symlink(real_root, linked_root)
    root_symlink = summarize_waveform(linked_root)
    assert root_symlink["invalid_reason"] == "root_path_is_symlink"

    linked_parent = tmp_path / "linked-parent"
    os.symlink(tmp_path, linked_parent)
    ancestor_symlink = summarize_waveform(linked_parent / "real-root")
    assert ancestor_symlink["invalid_reason"] == "root_parent_is_symlink"

    directory_root = tmp_path / "directory-root"
    directory_root.mkdir()
    (directory_root / "tran.csv").mkdir()
    directory = summarize_waveform(directory_root)
    assert directory["invalid_reason"] == "path_is_not_regular_file"


def test_nonregular_fifo_is_rejected_without_blocking(tmp_path) -> None:
    os.mkfifo(tmp_path / "tran.csv")

    fifo = summarize_waveform(tmp_path)

    assert fifo["status"] == "invalid"
    assert fifo["invalid_reason"] == "path_is_not_regular_file"
