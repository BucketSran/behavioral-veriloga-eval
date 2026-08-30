from __future__ import annotations

import csv
import errno
import hashlib
import io
import json
import math
import os
import stat
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "vaevas-waveform-summary-v1"
RELATIVE_PATH = "tran.csv"
MAX_BYTES = 1_048_576
MAX_DATA_ROWS = 10_000
MAX_COLUMNS = 32
MAX_RETURNED_SIGNALS = 8
MAX_IDENTIFIER_CHARS = 128


def waveform_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "relative_path": RELATIVE_PATH,
        "max_bytes": MAX_BYTES,
        "max_data_rows": MAX_DATA_ROWS,
        "max_columns": MAX_COLUMNS,
        "max_returned_signals": MAX_RETURNED_SIGNALS,
        "max_identifier_chars": MAX_IDENTIFIER_CHARS,
        "arbitrary_model_path_allowed": False,
        "establishes_invocation_provenance": False,
        "includes_verdict": False,
    }


def waveform_policy_sha256() -> str:
    payload = json.dumps(waveform_policy(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summarize_waveform(output_root: Path) -> dict[str, Any]:
    base = _base_summary()

    root_problem = _validate_output_root(output_root)
    if root_problem is not None:
        return _invalid(base, root_problem)

    root_fd: int | None = None
    file_fd: int | None = None
    try:
        root_fd = _open_root_directory(output_root)
        file_fd = _open_tran_csv(root_fd)
        if file_fd is None:
            base["status"] = "missing"
            return base
        stat_result = os.fstat(file_fd)
        if not stat.S_ISREG(stat_result.st_mode):
            return _invalid(base, "path_is_not_regular_file")
        base["file_size_bytes"] = stat_result.st_size
        raw_bytes = _read_bounded(file_fd)
    except _TooLarge:
        base["status"] = "too_large"
        return base
    except _PathSymlink:
        return _invalid(base, "path_is_symlink")
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            base["status"] = "missing"
            return base
        return _invalid(base, "path_unreadable")
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if root_fd is not None:
            os.close(root_fd)

    base["accepted_bytes"] = len(raw_bytes)
    base["source_sha256"] = hashlib.sha256(raw_bytes).hexdigest()

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _invalid(base, "invalid_utf8")

    return _summarize_csv_text(base, text)


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_sha256": waveform_policy_sha256(),
        "relative_path": RELATIVE_PATH,
        "status": "invalid",
        "file_size_bytes": None,
        "accepted_bytes": 0,
        "source_sha256": None,
        "scanned_rows": 0,
        "total_data_rows_seen": 0,
        "returned_signals": 0,
        "omitted_signals": 0,
        "omitted_columns": 0,
        "incomplete_scan": False,
        "invalid_reason": None,
        "signals": [],
    }


def _invalid(summary: dict[str, Any], reason: str) -> dict[str, Any]:
    summary["status"] = "invalid"
    summary["invalid_reason"] = reason
    return summary


def _summarize_csv_text(summary: dict[str, Any], text: str) -> dict[str, Any]:
    try:
        rows = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(rows)
    except StopIteration:
        return _invalid(summary, "empty_csv")
    except csv.Error:
        return _invalid(summary, "csv_parse_error")

    if len(header) > MAX_COLUMNS:
        return _invalid(summary, "too_many_columns")
    if not header or any(not _valid_identifier(cell) for cell in header):
        return _invalid(summary, "invalid_header")
    if len(set(header)) != len(header):
        return _invalid(summary, "duplicate_header")

    stats = [_new_signal_stats(name) for name in header]

    try:
        for row_number, row in enumerate(rows, start=1):
            if len(row) != len(header):
                return _invalid(summary, "ragged_row")
            summary["total_data_rows_seen"] += 1
            if row_number > MAX_DATA_ROWS:
                summary["incomplete_scan"] = True
                break
            summary["scanned_rows"] += 1
            for index, cell in enumerate(row):
                try:
                    parsed = _parse_cell(cell)
                except ValueError:
                    return _invalid(summary, "nonnumeric_cell")
                _update_signal_stats(stats[index], parsed)
    except csv.Error:
        return _invalid(summary, "csv_parse_error")

    summary["returned_signals"] = min(len(stats), MAX_RETURNED_SIGNALS)
    summary["omitted_signals"] = max(0, len(stats) - MAX_RETURNED_SIGNALS)
    summary["signals"] = [_finalize_signal(signal) for signal in stats[:MAX_RETURNED_SIGNALS]]
    summary["status"] = (
        "truncated"
        if summary["incomplete_scan"] or summary["omitted_signals"] or summary["omitted_columns"]
        else "available"
    )
    return summary


def _new_signal_stats(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "finite_count": 0,
        "nonfinite_count": 0,
        "empty_count": 0,
        "finite_values": [],
        "min": None,
        "max": None,
        "first": None,
        "last": None,
    }


def _parse_cell(cell: str) -> tuple[str, float | None]:
    stripped = cell.strip()
    if stripped == "":
        return ("empty", None)
    try:
        value = float(stripped)
    except ValueError as exc:
        raise ValueError(f"nonnumeric cell: {stripped!r}") from exc
    if not math.isfinite(value):
        return ("nonfinite", None)
    return ("finite", value)


def _update_signal_stats(signal: dict[str, Any], parsed: tuple[str, float | None]) -> None:
    kind, value = parsed
    if kind == "empty":
        signal["empty_count"] += 1
        return
    if kind == "nonfinite":
        signal["nonfinite_count"] += 1
        return
    assert value is not None
    signal["finite_count"] += 1
    signal["finite_values"].append(value)
    signal["first"] = value if signal["first"] is None else signal["first"]
    signal["last"] = value
    signal["min"] = value if signal["min"] is None else min(signal["min"], value)
    signal["max"] = value if signal["max"] is None else max(signal["max"], value)


def _finalize_signal(signal: dict[str, Any]) -> dict[str, Any]:
    finite_count = signal["finite_count"]
    mean = (
        math.fsum(value / finite_count for value in signal["finite_values"])
        if finite_count
        else None
    )
    return {
        "name": signal["name"],
        "unit": None,
        "finite_count": finite_count,
        "nonfinite_count": signal["nonfinite_count"],
        "empty_count": signal["empty_count"],
        "min": signal["min"],
        "max": signal["max"],
        "mean": mean,
        "first": signal["first"],
        "last": signal["last"],
    }


def _valid_identifier(value: str) -> bool:
    stripped = value.strip()
    return stripped == value and 0 < len(value) <= MAX_IDENTIFIER_CHARS


class _TooLarge(Exception):
    pass


class _PathSymlink(Exception):
    pass


def _validate_output_root(output_root: Path) -> str | None:
    try:
        root_stat = output_root.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        return "root_path_unreadable"
    if stat.S_ISLNK(root_stat.st_mode):
        return "root_path_is_symlink"
    if not stat.S_ISDIR(root_stat.st_mode):
        return "root_path_is_not_directory"
    for parent in output_root.parents:
        try:
            parent_stat = parent.lstat()
        except OSError:
            return "root_parent_unreadable"
        if stat.S_ISLNK(parent_stat.st_mode):
            return "root_parent_is_symlink"
    return None


def _open_root_directory(output_root: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    return os.open(output_root, flags | nofollow)


def _open_tran_csv(root_fd: int) -> int | None:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(RELATIVE_PATH, flags | nofollow, dir_fd=root_fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise _PathSymlink from exc
        raise


def _read_bounded(file_fd: int) -> bytes:
    chunks: list[bytes] = []
    remaining = MAX_BYTES + 1
    while remaining:
        chunk = os.read(file_fd, min(65_536, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    raw_bytes = b"".join(chunks)
    if len(raw_bytes) > MAX_BYTES:
        raise _TooLarge
    return raw_bytes
