#!/usr/bin/env python3
"""Run task-local behavior contracts against a transient CSV.

The contract format is JSON to avoid adding a YAML dependency:

{
  "task_id": "example",
  "contracts": [
    {"name": "out_edges", "type": "edge_count", "signal": "out", "threshold": 0.45, "min_edges": 2}
  ]
}
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_rows(csv_path: Path) -> tuple[list[str], list[dict[str, float]]]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return [], []
    rows: list[dict[str, float]] = []
    with csv_path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        for raw in reader:
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None:
                    continue
                try:
                    row[key] = float(value)
                except (TypeError, ValueError):
                    pass
            rows.append(row)
    return fieldnames, rows


def _window_rows(rows: list[dict[str, float]], contract: dict) -> list[dict[str, float]]:
    window = contract.get("window")
    if not window:
        return rows
    if not isinstance(window, (list, tuple)) or len(window) != 2:
        return rows
    start, end = float(window[0]), float(window[1])
    return [row for row in rows if start <= row.get("time", 0.0) <= end]


def _span(rows: list[dict[str, float]], signal: str) -> float | None:
    values = [row[signal] for row in rows if signal in row]
    if not values:
        return None
    return max(values) - min(values)


def _value_span(values: list[float]) -> float | None:
    if not values:
        return None
    return max(values) - min(values)


def _edge_count(rows: list[dict[str, float]], signal: str, threshold: float) -> int | None:
    values = [row[signal] for row in rows if signal in row]
    if len(values) < 2:
        return None
    states = [value >= threshold for value in values]
    return sum(1 for prev, cur in zip(states, states[1:]) if prev != cur)


def _rising_edge_times(rows: list[dict[str, float]], signal: str, threshold: float) -> list[float] | None:
    samples = [(row.get("time", 0.0), row[signal]) for row in rows if signal in row]
    if len(samples) < 2:
        return None
    edges: list[float] = []
    for (prev_time, prev_value), (cur_time, cur_value) in zip(samples, samples[1:]):
        if prev_value < threshold <= cur_value:
            edges.append(cur_time)
    return edges


def _rising_edge_indices(rows: list[dict[str, float]], signal: str, threshold: float) -> list[int] | None:
    samples = [(idx, row[signal]) for idx, row in enumerate(rows) if signal in row]
    if len(samples) < 2:
        return None
    edges: list[int] = []
    for (_prev_idx, prev_value), (cur_idx, cur_value) in zip(samples, samples[1:]):
        if prev_value < threshold <= cur_value:
            edges.append(cur_idx)
    return edges


def _rising_edges(rows: list[dict[str, float]], signal: str, threshold: float) -> list[tuple[int, float]] | None:
    samples = [
        (idx, row.get("time", 0.0), row[signal])
        for idx, row in enumerate(rows)
        if signal in row
    ]
    if len(samples) < 2:
        return None
    edges: list[tuple[int, float]] = []
    for (_prev_idx, _prev_time, prev_value), (cur_idx, cur_time, cur_value) in zip(samples, samples[1:]):
        if prev_value < threshold <= cur_value:
            edges.append((cur_idx, cur_time))
    return edges


def _paired_edge_windows(
    rows: list[dict[str, float]],
    reference: str,
    feedback: str,
    threshold: float,
    max_pair_gap_s: float,
    response_tail_s: float,
) -> tuple[list[dict], dict]:
    ref_edges = _rising_edges(rows, reference, threshold)
    fb_edges = _rising_edges(rows, feedback, threshold)
    stats = {
        "reference_edges": None if ref_edges is None else len(ref_edges),
        "feedback_edges": None if fb_edges is None else len(fb_edges),
    }
    if ref_edges is None or fb_edges is None:
        return [], stats

    pairs: list[dict] = []
    i = 0
    j = 0
    while i < len(ref_edges) and j < len(fb_edges):
        ref_idx, ref_time = ref_edges[i]
        fb_idx, fb_time = fb_edges[j]
        gap = abs(ref_time - fb_time)
        if gap <= max_pair_gap_s:
            lead = "reference" if ref_time <= fb_time else "feedback"
            start = min(ref_time, fb_time)
            end = max(ref_time, fb_time) + response_tail_s
            pairs.append(
                {
                    "reference_idx": ref_idx,
                    "feedback_idx": fb_idx,
                    "reference_time": ref_time,
                    "feedback_time": fb_time,
                    "lead": lead,
                    "gap_s": gap,
                    "start": start,
                    "end": end,
                }
            )
            i += 1
            j += 1
        elif ref_time < fb_time:
            i += 1
        else:
            j += 1
    return pairs, stats


def _edge_in_window(edges: list[tuple[int, float]] | None, start: float, end: float) -> bool:
    if not edges:
        return False
    return any(start <= edge_time <= end for _idx, edge_time in edges)


def _high_time_in_windows(
    rows: list[dict[str, float]],
    signal: str,
    threshold: float,
    windows: list[tuple[float, float]],
) -> tuple[float | None, float, float]:
    if not windows:
        return None, 0.0, 0.0
    total_dt = 0.0
    high_dt = 0.0
    for prev, cur in zip(rows, rows[1:]):
        if signal not in prev or signal not in cur:
            continue
        prev_time = prev.get("time", 0.0)
        cur_time = cur.get("time", 0.0)
        dt = cur_time - prev_time
        if dt <= 0.0:
            continue
        mid_time = 0.5 * (prev_time + cur_time)
        if not any(start <= mid_time <= end for start, end in windows):
            continue
        total_dt += dt
        if 0.5 * (prev[signal] + cur[signal]) >= threshold:
            high_dt += dt
    if total_dt <= 0.0:
        return None, total_dt, high_dt
    return high_dt / total_dt, total_dt, high_dt


def _decode_code(row: dict[str, float], bits: list[str], threshold: float) -> int | None:
    if not bits or not all(bit in row for bit in bits):
        return None
    code = 0
    for bit in bits:
        code = (code << 1) | int(row[bit] >= threshold)
    return code


def _code_values(rows: list[dict[str, float]], bits: list[str], threshold: float) -> list[int] | None:
    if not bits:
        return None
    values: list[int] = []
    for row in rows:
        if not all(bit in row for bit in bits):
            continue
        code = 0
        for bit in bits:
            code = (code << 1) | int(row[bit] >= threshold)
        values.append(code)
    return values


def _hamming_distance(lhs: int, rhs: int) -> int:
    return bin(lhs ^ rhs).count("1")


def _severity(contract: dict) -> str:
    raw = str(contract.get("severity", "hard")).strip().lower()
    return "advisory" if raw == "advisory" else "hard"


def _check_contract(contract: dict, fieldnames: list[str], rows: list[dict[str, float]]) -> dict:
    ctype = contract.get("type")
    name = contract.get("name", ctype)
    scoped_rows = _window_rows(rows, contract)
    result = {
        "name": name,
        "type": ctype,
        "severity": _severity(contract),
        "passed": False,
        "diagnostic_hint": contract.get("diagnostic_hint", ""),
        "repair_family": contract.get("repair_family", ""),
    }

    if ctype == "csv_exists":
        min_rows = int(contract.get("min_rows", 1))
        observed = len(rows)
        result.update(observed_rows=observed, expected_min_rows=min_rows, passed=observed >= min_rows)
        return result

    if ctype == "signal_present":
        signals = contract.get("signals", [])
        missing = [signal for signal in signals if signal not in fieldnames]
        result.update(missing=missing, passed=not missing)
        return result

    if ctype == "signal_role_integrity":
        roles = dict(contract.get("roles", {}))
        missing = [signal for signal in roles if signal not in fieldnames]
        input_signals = [signal for signal, role in roles.items() if str(role).startswith("input")]
        output_signals = [signal for signal, role in roles.items() if str(role).startswith("output")]
        result.update(
            roles=roles,
            missing=missing,
            input_signals=input_signals,
            output_signals=output_signals,
            constant_input_ok=bool(contract.get("constant_input_ok", True)),
        )
        result["passed"] = not missing
        return result

    if ctype in {"input_span", "output_span"}:
        signal = contract["signal"]
        observed = _span(scoped_rows, signal)
        min_span = float(contract.get("min_span", 0.0))
        result.update(signal=signal, observed_span=observed, expected_min_span=min_span)
        result["passed"] = observed is not None and observed >= min_span
        return result

    if ctype == "any_output_span":
        signals = list(contract.get("signals", []))
        spans = {signal: _span(scoped_rows, signal) for signal in signals}
        min_span = float(contract.get("min_span", 0.0))
        best_span = max((value for value in spans.values() if value is not None), default=None)
        result.update(signals=signals, observed_spans=spans, observed_best_span=best_span, expected_min_span=min_span)
        result["passed"] = best_span is not None and best_span >= min_span
        return result

    if ctype == "differential_range":
        positive = contract["positive"]
        negative = contract["negative"]
        values = [
            (row[positive], row[negative])
            for row in scoped_rows
            if positive in row and negative in row
        ]
        diffs = [pos - neg for pos, neg in values]
        common = [(pos + neg) / 2.0 for pos, neg in values]
        min_diff_span = float(contract.get("min_diff_span", 0.0))
        diff_span = _value_span(diffs)
        result.update(
            positive=positive,
            negative=negative,
            comparable_rows=len(values),
            observed_diff_span=diff_span,
            observed_positive_span=_value_span([pos for pos, _neg in values]),
            observed_negative_span=_value_span([neg for _pos, neg in values]),
            observed_common_mode_span=_value_span(common),
            expected_min_diff_span=min_diff_span,
        )
        result["passed"] = diff_span is not None and diff_span >= min_diff_span
        return result

    if ctype == "differential_sign_or_polarity":
        positive = contract["positive"]
        negative = contract["negative"]
        values = [
            (row[positive], row[negative])
            for row in scoped_rows
            if positive in row and negative in row
        ]
        diffs = [pos - neg for pos, neg in values]
        common = [(pos + neg) / 2.0 for pos, neg in values]
        diff_span = _value_span(diffs)
        common_span = _value_span(common)
        min_diff_span = float(contract.get("min_diff_span", 0.0))
        max_common_to_diff_ratio = float(contract.get("max_common_to_diff_ratio", 1.5))
        ratio = None
        if diff_span and diff_span > 0:
            ratio = (common_span or 0.0) / diff_span

        delta_pairs = [
            (cur_pos - prev_pos, cur_neg - prev_neg)
            for (prev_pos, prev_neg), (cur_pos, cur_neg) in zip(values, values[1:])
        ]
        active_delta_pairs = [
            (dpos, dneg)
            for dpos, dneg in delta_pairs
            if abs(dpos) > 1e-12 or abs(dneg) > 1e-12
        ]
        opposite_delta_fraction = None
        if active_delta_pairs:
            opposite_delta_fraction = sum(
                1
                for dpos, dneg in active_delta_pairs
                if dpos * dneg < 0 or abs(dpos) < 1e-12 or abs(dneg) < 1e-12
            ) / len(active_delta_pairs)

        result.update(
            positive=positive,
            negative=negative,
            comparable_rows=len(values),
            observed_diff_span=diff_span,
            observed_common_mode_span=common_span,
            observed_common_to_diff_ratio=ratio,
            observed_opposite_delta_fraction=opposite_delta_fraction,
            expected_min_diff_span=min_diff_span,
            expected_max_common_to_diff_ratio=max_common_to_diff_ratio,
        )
        result["passed"] = (
            diff_span is not None
            and diff_span >= min_diff_span
            and ratio is not None
            and ratio <= max_common_to_diff_ratio
        )
        return result

    if ctype == "edge_count":
        signal = contract["signal"]
        threshold = float(contract.get("threshold", 0.5))
        observed = _edge_count(scoped_rows, signal, threshold)
        min_edges = int(contract.get("min_edges", 1))
        result.update(signal=signal, threshold=threshold, observed_edges=observed, expected_min_edges=min_edges)
        result["passed"] = observed is not None and observed >= min_edges
        return result

    if ctype == "pulse_count":
        signal = contract["signal"]
        threshold = float(contract.get("threshold", 0.5))
        edges = _rising_edge_times(scoped_rows, signal, threshold)
        min_pulses = int(contract.get("min_pulses", 1))
        result.update(signal=signal, observed_pulses=None if edges is None else len(edges), expected_min_pulses=min_pulses)
        result["passed"] = edges is not None and len(edges) >= min_pulses
        return result

    if ctype == "non_overlap":
        signals = list(contract.get("signals", []))
        threshold = float(contract.get("threshold", 0.5))
        max_overlap_fraction = float(contract.get("max_overlap_fraction", 0.02))
        comparable_rows = [row for row in scoped_rows if all(signal in row for signal in signals)]
        overlap_rows = [
            row
            for row in comparable_rows
            if sum(1 for signal in signals if row[signal] >= threshold) >= 2
        ]
        fraction = None if not comparable_rows else len(overlap_rows) / len(comparable_rows)
        result.update(
            signals=signals,
            observed_overlap_fraction=fraction,
            expected_max_overlap_fraction=max_overlap_fraction,
            comparable_rows=len(comparable_rows),
            overlap_rows=len(overlap_rows),
        )
        result["passed"] = fraction is not None and fraction <= max_overlap_fraction
        return result

    if ctype in {"pulse_symmetry_window", "paired_edge_response"}:
        reference = contract["reference"]
        feedback = contract["feedback"]
        up = contract["up"]
        down = contract["down"]
        threshold = float(contract.get("threshold", 0.5))
        max_pair_gap_s = float(contract.get("max_pair_gap_s", 2e-9))
        response_tail_s = float(contract.get("response_tail_s", max_pair_gap_s))
        min_pairs_per_side = int(contract.get("min_pairs_per_side", 1))
        min_total_pairs = int(contract.get("min_total_pairs", 1))
        min_response_fraction = float(contract.get("min_response_fraction", 0.8))
        max_wrong_responses = int(contract.get("max_wrong_responses", 0))
        pairs, edge_stats = _paired_edge_windows(
            scoped_rows,
            reference,
            feedback,
            threshold,
            max_pair_gap_s,
            response_tail_s,
        )
        up_edges = _rising_edges(scoped_rows, up, threshold)
        down_edges = _rising_edges(scoped_rows, down, threshold)
        expected = {"reference": 0, "feedback": 0}
        observed = {"reference": 0, "feedback": 0}
        wrong = {"reference": 0, "feedback": 0}
        for pair in pairs:
            lead = pair["lead"]
            expected[lead] += 1
            if lead == "reference":
                if _edge_in_window(up_edges, pair["start"], pair["end"]):
                    observed["reference"] += 1
                if _edge_in_window(down_edges, pair["start"], pair["end"]):
                    wrong["reference"] += 1
            else:
                if _edge_in_window(down_edges, pair["start"], pair["end"]):
                    observed["feedback"] += 1
                if _edge_in_window(up_edges, pair["start"], pair["end"]):
                    wrong["feedback"] += 1

        total_expected = expected["reference"] + expected["feedback"]
        total_observed = observed["reference"] + observed["feedback"]
        response_fraction = None if total_expected == 0 else total_observed / total_expected
        result.update(
            reference=reference,
            feedback=feedback,
            up=up,
            down=down,
            threshold=threshold,
            max_pair_gap_s=max_pair_gap_s,
            response_tail_s=response_tail_s,
            paired_edges=len(pairs),
            expected_reference_leads=expected["reference"],
            expected_feedback_leads=expected["feedback"],
            observed_up_responses_for_reference_leads=observed["reference"],
            observed_down_responses_for_feedback_leads=observed["feedback"],
            wrong_down_responses_for_reference_leads=wrong["reference"],
            wrong_up_responses_for_feedback_leads=wrong["feedback"],
            observed_response_fraction=response_fraction,
            expected_min_pairs_per_side=min_pairs_per_side,
            expected_min_total_pairs=min_total_pairs,
            expected_min_response_fraction=min_response_fraction,
            expected_max_wrong_responses=max_wrong_responses,
            **edge_stats,
        )
        if ctype == "pulse_symmetry_window":
            result["passed"] = (
                expected["reference"] >= min_pairs_per_side
                and expected["feedback"] >= min_pairs_per_side
                and observed["reference"] >= min_pairs_per_side
                and observed["feedback"] >= min_pairs_per_side
                and wrong["reference"] <= max_wrong_responses
                and wrong["feedback"] <= max_wrong_responses
            )
        else:
            result["passed"] = (
                total_expected >= min_total_pairs
                and response_fraction is not None
                and response_fraction >= min_response_fraction
                and wrong["reference"] <= max_wrong_responses
                and wrong["feedback"] <= max_wrong_responses
            )
        return result

    if ctype == "pulse_width_fraction_window":
        reference = contract["reference"]
        feedback = contract["feedback"]
        up = contract["up"]
        down = contract["down"]
        threshold = float(contract.get("threshold", 0.5))
        max_pair_gap_s = float(contract.get("max_pair_gap_s", 2e-9))
        response_tail_s = float(contract.get("response_tail_s", max_pair_gap_s))
        min_expected_fraction = float(contract.get("min_expected_fraction", 0.001))
        max_expected_fraction = float(contract.get("max_expected_fraction", 0.6))
        max_wrong_fraction = float(contract.get("max_wrong_fraction", 0.02))
        pairs, edge_stats = _paired_edge_windows(
            scoped_rows,
            reference,
            feedback,
            threshold,
            max_pair_gap_s,
            response_tail_s,
        )
        reference_windows = [
            (pair["start"], pair["end"])
            for pair in pairs
            if pair["lead"] == "reference"
        ]
        feedback_windows = [
            (pair["start"], pair["end"])
            for pair in pairs
            if pair["lead"] == "feedback"
        ]
        up_on_reference, up_reference_dt, _ = _high_time_in_windows(scoped_rows, up, threshold, reference_windows)
        down_on_reference, down_reference_dt, _ = _high_time_in_windows(scoped_rows, down, threshold, reference_windows)
        down_on_feedback, down_feedback_dt, _ = _high_time_in_windows(scoped_rows, down, threshold, feedback_windows)
        up_on_feedback, up_feedback_dt, _ = _high_time_in_windows(scoped_rows, up, threshold, feedback_windows)

        expected_checks: list[bool] = []
        wrong_checks: list[bool] = []
        if reference_windows:
            expected_checks.append(
                up_on_reference is not None
                and min_expected_fraction <= up_on_reference <= max_expected_fraction
            )
            wrong_checks.append(down_on_reference is not None and down_on_reference <= max_wrong_fraction)
        if feedback_windows:
            expected_checks.append(
                down_on_feedback is not None
                and min_expected_fraction <= down_on_feedback <= max_expected_fraction
            )
            wrong_checks.append(up_on_feedback is not None and up_on_feedback <= max_wrong_fraction)
        result.update(
            reference=reference,
            feedback=feedback,
            up=up,
            down=down,
            threshold=threshold,
            max_pair_gap_s=max_pair_gap_s,
            response_tail_s=response_tail_s,
            paired_edges=len(pairs),
            reference_lead_windows=len(reference_windows),
            feedback_lead_windows=len(feedback_windows),
            observed_up_fraction_on_reference_leads=up_on_reference,
            observed_down_fraction_on_reference_leads=down_on_reference,
            observed_down_fraction_on_feedback_leads=down_on_feedback,
            observed_up_fraction_on_feedback_leads=up_on_feedback,
            reference_window_dt=up_reference_dt or down_reference_dt,
            feedback_window_dt=down_feedback_dt or up_feedback_dt,
            expected_min_expected_fraction=min_expected_fraction,
            expected_max_expected_fraction=max_expected_fraction,
            expected_max_wrong_fraction=max_wrong_fraction,
            **edge_stats,
        )
        result["passed"] = bool(expected_checks) and all(expected_checks) and all(wrong_checks)
        return result

    if ctype == "frequency_ratio":
        reference = contract["reference"]
        feedback = contract["feedback"]
        threshold = float(contract.get("threshold", 0.5))
        ref_edges = _rising_edge_times(scoped_rows, reference, threshold)
        fb_edges = _rising_edge_times(scoped_rows, feedback, threshold)
        expected = float(contract.get("expected_ratio", 1.0))
        tolerance = float(contract.get("tolerance", 0.25))
        min_edges = int(contract.get("min_edges", 2))
        ratio = None
        if ref_edges is not None and fb_edges is not None and len(fb_edges) > 0:
            ratio = len(ref_edges) / len(fb_edges)
        result.update(
            reference=reference,
            feedback=feedback,
            reference_edges=None if ref_edges is None else len(ref_edges),
            feedback_edges=None if fb_edges is None else len(fb_edges),
            observed_ratio=ratio,
            expected_ratio=expected,
            tolerance=tolerance,
        )
        result["passed"] = (
            ref_edges is not None
            and fb_edges is not None
            and len(ref_edges) >= min_edges
            and len(fb_edges) >= min_edges
            and ratio is not None
            and abs(ratio - expected) <= tolerance
        )
        return result

    if ctype == "high_fraction":
        signal = contract["signal"]
        threshold = float(contract.get("threshold", 0.5))
        values = [row[signal] for row in scoped_rows if signal in row]
        min_fraction = contract.get("min_fraction")
        max_fraction = contract.get("max_fraction")
        min_fraction_f = float(min_fraction) if min_fraction is not None else None
        max_fraction_f = float(max_fraction) if max_fraction is not None else None
        fraction = None if not values else sum(1 for value in values if value >= threshold) / len(values)
        result.update(
            signal=signal,
            observed_high_fraction=fraction,
            expected_min_fraction=min_fraction_f,
            expected_max_fraction=max_fraction_f,
        )
        result["passed"] = (
            fraction is not None
            and (min_fraction_f is None or fraction >= min_fraction_f)
            and (max_fraction_f is None or fraction <= max_fraction_f)
        )
        return result

    if ctype == "active_count_range":
        bits = list(contract.get("bits", []))
        threshold = float(contract.get("threshold", 0.5))
        min_active = int(contract.get("min_active", 1))
        max_active = contract.get("max_active")
        max_active_i = int(max_active) if max_active is not None else None
        counts: list[int] = []
        for row in scoped_rows:
            if not all(bit in row for bit in bits):
                continue
            counts.append(sum(1 for bit in bits if row[bit] >= threshold))
        observed_max = max(counts) if counts else None
        observed_min = min(counts) if counts else None
        result.update(
            bits=bits,
            observed_min_active=observed_min,
            observed_max_active=observed_max,
            expected_min_active=min_active,
            expected_max_active=max_active_i,
        )
        result["passed"] = (
            observed_max is not None
            and observed_max >= min_active
            and (max_active_i is None or observed_max <= max_active_i)
        )
        return result

    if ctype == "code_coverage":
        bits = list(contract.get("bits", []))
        threshold = float(contract.get("threshold", 0.5))
        values = _code_values(scoped_rows, bits, threshold)
        min_unique = int(contract.get("min_unique", 2))
        unique_count = len(set(values or []))
        result.update(bits=bits, threshold=threshold, unique_codes=unique_count, expected_min_unique=min_unique)
        result["passed"] = values is not None and unique_count >= min_unique
        return result

    if ctype == "settled_flag_after_stable_cycles":
        clock = contract["clock"]
        flag = contract["flag"]
        bits = list(contract.get("state_bits", []))
        threshold = float(contract.get("threshold", 0.5))
        min_stable_cycles = int(contract.get("min_stable_cycles", 1))
        sample_offset = int(contract.get("sample_offset_rows", 1))
        edge_indices = _rising_edge_indices(scoped_rows, clock, threshold)
        codes: list[tuple[int, float, int]] = []
        if edge_indices is not None:
            for edge_idx in edge_indices:
                sample_idx = min(edge_idx + sample_offset, len(scoped_rows) - 1)
                code = _decode_code(scoped_rows[sample_idx], bits, threshold)
                if code is not None:
                    codes.append((sample_idx, scoped_rows[sample_idx].get("time", 0.0), code))

        stable_run = 0
        max_stable_run = 0
        first_stable_idx = None
        previous_code = None
        for idx, _time, code in codes:
            stable_run = stable_run + 1 if previous_code == code else 1
            previous_code = code
            max_stable_run = max(max_stable_run, stable_run)
            if first_stable_idx is None and stable_run >= min_stable_cycles:
                first_stable_idx = idx

        flag_values_after_stable = []
        if first_stable_idx is not None:
            flag_values_after_stable = [
                row[flag] for row in scoped_rows[first_stable_idx:] if flag in row
            ]
        flag_high_after_stable = any(value >= threshold for value in flag_values_after_stable)
        result.update(
            clock=clock,
            flag=flag,
            bits=bits,
            threshold=threshold,
            observed_edges=None if edge_indices is None else len(edge_indices),
            observed_code_samples=len(codes),
            observed_max_stable_cycles=max_stable_run,
            expected_min_stable_cycles=min_stable_cycles,
            flag_high_after_stable=flag_high_after_stable,
        )
        result["passed"] = (
            edge_indices is not None
            and len(codes) >= min_stable_cycles
            and first_stable_idx is not None
            and flag_high_after_stable
        )
        return result

    if ctype == "code_hamming_distance":
        bits = list(contract.get("bits", []))
        threshold = float(contract.get("threshold", 0.5))
        values = _code_values(scoped_rows, bits, threshold)
        max_hamming = int(contract.get("max_hamming", 1))
        min_transitions = int(contract.get("min_transitions", 1))
        compact_values: list[int] = []
        for value in values or []:
            if not compact_values or compact_values[-1] != value:
                compact_values.append(value)
        distances = [
            _hamming_distance(prev, cur)
            for prev, cur in zip(compact_values, compact_values[1:])
        ]
        bad_transitions = sum(1 for distance in distances if distance > max_hamming)
        result.update(
            bits=bits,
            threshold=threshold,
            observed_transitions=len(distances),
            bad_transitions=bad_transitions,
            expected_min_transitions=min_transitions,
            expected_max_hamming=max_hamming,
        )
        result["passed"] = values is not None and len(distances) >= min_transitions and bad_transitions == 0
        return result

    result.update(error=f"unsupported contract type: {ctype}")
    return result


def run_contracts(contract_path: Path, csv_path: Path) -> dict:
    spec = json.loads(contract_path.read_text(encoding="utf-8"))
    source = spec.get("source", {}) if isinstance(spec.get("source", {}), dict) else {}
    functional_ir = source.get("prompt_functional_ir", {}) if isinstance(source.get("prompt_functional_ir", {}), dict) else {}
    functional_claims = source.get("prompt_functional_claims", [])
    if not functional_claims:
        functional_claims = [
            str(item.get("type", ""))
            for item in functional_ir.get("claims", [])
            if isinstance(item, dict) and item.get("type")
        ]
    fieldnames, rows = _load_rows(csv_path)
    contract_results = [_check_contract(contract, fieldnames, rows) for contract in spec.get("contracts", [])]
    passed = [item["name"] for item in contract_results if item.get("passed")]
    failed = [item["name"] for item in contract_results if not item.get("passed")]
    passed_hard = [
        item["name"]
        for item in contract_results
        if item.get("passed") and item.get("severity") == "hard"
    ]
    passed_advisory = [
        item["name"]
        for item in contract_results
        if item.get("passed") and item.get("severity") == "advisory"
    ]
    failed_hard = [
        item["name"]
        for item in contract_results
        if not item.get("passed") and item.get("severity") == "hard"
    ]
    failed_advisory = [
        item["name"]
        for item in contract_results
        if not item.get("passed") and item.get("severity") == "advisory"
    ]
    summaries = []
    for item in contract_results:
        status = "passed" if item.get("passed") else "failed"
        hint = item.get("diagnostic_hint") or item.get("type")
        severity = item.get("severity", "hard")
        summaries.append(f"{status} [{severity}]: {item['name']} - {hint}")
    return {
        "task_id": spec.get("task_id", contract_path.parent.name),
        "contract_path": str(contract_path),
        "csv_path": str(csv_path),
        "source": source,
        "prompt_functional_ir": functional_ir,
        "prompt_functional_claims": functional_claims,
        "prompt_checker_templates": source.get("prompt_checker_templates", []),
        "prompt_checker_signal_sources": source.get("prompt_checker_signal_sources", {}),
        "status": "PASS" if not failed_hard else "FAIL_CONTRACT",
        "advisory_status": "WARN_CONTRACT" if failed_advisory and not failed_hard else "PASS",
        "passed_contracts": passed,
        "failed_contracts": failed,
        "passed_hard_contracts": passed_hard,
        "passed_advisory_contracts": passed_advisory,
        "failed_hard_contracts": failed_hard,
        "failed_advisory_contracts": failed_advisory,
        "contract_results": contract_results,
        "diagnostic_summary": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_contracts(args.contracts, args.csv)
    if args.out:
        _json_write(args.out, report)
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
