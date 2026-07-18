"""Task-specific checker for canonical v4 DUT 089."""
from __future__ import annotations

from ..api import Checker
import csv

def _csv_header_indices(csv_path: Path) -> tuple[list[str], dict[str, int]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return header, {name: idx for idx, name in enumerate(header)}

def _csv_required_indices(csv_path: Path, required: set[str]) -> tuple[dict[str, int] | None, list[str]]:
    header, index = _csv_header_indices(csv_path)
    missing = sorted(required - set(header))
    if missing:
        return None, missing
    return {name: index[name] for name in required}, []

def _float_at(row: list[str], index: int, default: float = 0.0) -> float:
    try:
        return float(row[index])
    except (IndexError, TypeError, ValueError):
        return default

def _stream_cross_interval_163p333_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, _missing = _csv_required_indices(csv_path, {"time", "a", "b", "delay_out", "seen_out"})
    if indices is None:
        return 0.0, ["missing time/a/b/delay_out/seen_out"]
    assert indices is not None

    seen_hi = 0.0
    prev_a: float | None = None
    prev_b: float | None = None
    a_t: float | None = None
    b_t: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_value = _float_at(row, indices["time"])
            a = _float_at(row, indices["a"])
            b = _float_at(row, indices["b"])
            seen_hi = max(seen_hi, _float_at(row, indices["seen_out"]))
            if prev_a is not None and a_t is None and prev_a <= 0.45 < a:
                a_t = time_value
            if prev_b is not None and a_t is not None and b_t is None and time_value > a_t and prev_b <= 0.45 < b:
                b_t = time_value
            prev_a = a
            prev_b = b
    if a_t is None or b_t is None:
        return 0.0, [f"missing_input_edges a={a_t is not None} b={b_t is not None}"]
    if seen_hi < 0.3:
        return 0.0, [f"seen_out_never_high={seen_hi:.3f}"]

    seen_th = 0.5 * seen_hi
    first_seen_time: float | None = None
    seen_delay_values: list[float] = []
    settled_delay_values: list[float] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_value = _float_at(row, indices["time"])
            seen = _float_at(row, indices["seen_out"])
            if seen <= seen_th:
                continue
            if first_seen_time is None:
                first_seen_time = time_value
            delay = _float_at(row, indices["delay_out"])
            seen_delay_values.append(delay)
            if time_value >= first_seen_time + 0.2e-9:
                settled_delay_values.append(delay)

    if first_seen_time is None:
        return 0.0, ["seen_out_no_logic_high_samples"]
    if len(settled_delay_values) < 3:
        settled_delay_values = seen_delay_values
    tail_count = min(len(settled_delay_values), max(5, len(settled_delay_values) // 3))
    tail = sorted(settled_delay_values[-tail_count:])
    if not tail:
        return 0.0, ["no_post_seen_delay_samples"]
    delay_level = tail[len(tail) // 2]
    delay_ps = delay_level / max(seen_hi, 1e-6) * 200.0
    expected_ps = (b_t - a_t) * 1.0e12
    err_ps = abs(delay_ps - expected_ps)
    ok = 0.0 < expected_ps < 500.0 and err_ps <= 15.0
    return (1.0 if ok else 0.0), [
        f"delay_ps={delay_ps:.3f} expected_ps={expected_ps:.3f} "
        f"err_ps={err_ps:.3f} seen_hi={seen_hi:.3f} post_seen_samples={len(settled_delay_values)}"
    ]

def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges

def check_cross_interval_163p333(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "a", "b", "delay_out", "seen_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/a/b/delay_out/seen_out"
    times = [r["time"] for r in rows]
    a_edges = rising_edges([r["a"] for r in rows], times, threshold=0.45)
    b_edges = rising_edges([r["b"] for r in rows], times, threshold=0.45)
    if not a_edges or not b_edges:
        return False, f"missing_input_edges a={len(a_edges)} b={len(b_edges)}"
    a_t = a_edges[0]
    b_t = next((edge for edge in b_edges if edge > a_t), None)
    if b_t is None:
        return False, "missing_b_edge_after_a"

    seen_hi = max(r["seen_out"] for r in rows)
    if seen_hi < 0.3:
        return False, f"seen_out_never_high={seen_hi:.3f}"

    seen_th = 0.5 * seen_hi
    seen_rows = [r for r in rows if r["seen_out"] > seen_th]
    if not seen_rows:
        return False, "seen_out_no_logic_high_samples"
    # The event happens late in a short run. Averaging the final 30% of the
    # whole waveform incorrectly includes pre-event zeros, so measure the
    # settled delay level only after seen_out has asserted.
    settle_start = seen_rows[0]["time"] + 0.2e-9
    settled_rows = [r for r in seen_rows if r["time"] >= settle_start]
    if len(settled_rows) < 3:
        settled_rows = seen_rows
    tail_count = min(len(settled_rows), max(5, len(settled_rows) // 3))
    tail = sorted(r["delay_out"] for r in settled_rows[-tail_count:])
    if not tail:
        return False, "no_post_seen_delay_samples"
    delay_level = tail[len(tail) // 2]
    vdd_est = max(max(r["seen_out"] for r in rows), 1e-6)
    delay_ps = delay_level / vdd_est * 200.0
    expected_ps = (b_t - a_t) * 1.0e12
    err_ps = abs(delay_ps - expected_ps)
    ok = 0.0 < expected_ps < 500.0 and err_ps <= 15.0
    return ok, (
        f"delay_ps={delay_ps:.3f} expected_ps={expected_ps:.3f} "
        f"err_ps={err_ps:.3f} seen_hi={seen_hi:.3f} post_seen_samples={len(settled_rows)}"
    )

CHECKER_ID = "v4_089_edge_crossing_interval_timer"
CHECKER: Checker = check_cross_interval_163p333
STREAMING_CHECKER = _stream_cross_interval_163p333_csv
