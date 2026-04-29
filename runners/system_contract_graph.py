#!/usr/bin/env python3
"""Evaluate system-level relation graphs against generated waveform artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPHS = ROOT / "docs" / "SYSTEM_CONTRACT_GRAPHS.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, allow_nan=True) + "\n", encoding="utf-8")


def _load_graphs(path: Path) -> dict[str, dict]:
    payload = _read_json(path)
    return {graph["id"]: graph for graph in payload.get("graphs", [])}


def _load_rows(csv_path: Path | None) -> tuple[list[str], list[dict[str, float]]]:
    if csv_path is None or not csv_path.exists() or csv_path.stat().st_size == 0:
        return [], []
    rows: list[dict[str, float]] = []
    with csv_path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
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


def _resolve_node_signal(graph: dict, node: str, fieldnames: list[str]) -> str | None:
    info = graph.get("nodes", {}).get(node, {})
    for signal in info.get("signals", []):
        if signal in fieldnames:
            return signal
    return None


def _resolve_any_signal(candidates: list[str], fieldnames: list[str]) -> str | None:
    for signal in candidates:
        if signal in fieldnames:
            return signal
    return None


def _indexed_signal_map(fieldnames: list[str], prefix: str) -> dict[int, str]:
    pattern = re.compile(rf"^{re.escape(prefix)}(?:_)?(\d+)$", re.IGNORECASE)
    indexed: dict[int, str] = {}
    for name in fieldnames:
        match = pattern.match(name)
        if match:
            indexed[int(match.group(1))] = name
    return indexed


def _resolve_code_series(
    rows: list[dict[str, float]],
    fieldnames: list[str],
    *,
    code_signals: list[str],
    bit_prefixes: list[str],
    min_width: int,
    threshold: float,
) -> tuple[list[int], dict]:
    code_signal = _resolve_any_signal(code_signals, fieldnames)
    if code_signal is not None:
        codes = [int(round(row[code_signal])) for row in rows if code_signal in row]
        return codes, {"mode": "code_signal", "code_signal": code_signal}

    best: tuple[str, dict[int, str]] | None = None
    for prefix in bit_prefixes:
        bits = _indexed_signal_map(fieldnames, prefix)
        if best is None or len(bits) > len(best[1]):
            best = (prefix, bits)
    if best is None or len(best[1]) < min_width:
        return [], {"mode": "missing_bits", "available_width": 0 if best is None else len(best[1])}

    prefix, bits = best
    codes: list[int] = []
    for row in rows:
        code = 0
        for idx, signal in bits.items():
            if row.get(signal, 0.0) > threshold:
                code |= 1 << idx
        codes.append(code)
    return codes, {"mode": "bit_signals", "prefix": prefix, "bit_signals": bits}


def _rising_edges(rows: list[dict[str, float]], signal: str, threshold: float) -> list[float] | None:
    samples = [(row.get("time", 0.0), row[signal]) for row in rows if signal in row]
    if len(samples) < 2:
        return None
    edges: list[float] = []
    for (_prev_time, prev_value), (cur_time, cur_value) in zip(samples, samples[1:]):
        if prev_value < threshold <= cur_value:
            edges.append(cur_time)
    return edges


def _window_from_fraction(rows: list[dict[str, float]], window_fraction: list[float] | None) -> tuple[float, float] | None:
    if not rows or "time" not in rows[0]:
        return None
    start_time = rows[0].get("time", 0.0)
    end_time = rows[-1].get("time", 0.0)
    if end_time <= start_time:
        return None
    lo, hi = window_fraction or [0.0, 1.0]
    return start_time + (end_time - start_time) * float(lo), start_time + (end_time - start_time) * float(hi)


def _edges_in_window(edges: list[float] | None, window: tuple[float, float] | None) -> list[float] | None:
    if edges is None or window is None:
        return None
    start, end = window
    return [edge for edge in edges if start <= edge <= end]


def _edge_count_ratio(
    rows: list[dict[str, float]],
    numerator: str,
    denominator: str,
    threshold: float,
    window: tuple[float, float] | None,
) -> dict:
    num_edges = _edges_in_window(_rising_edges(rows, numerator, threshold), window)
    den_edges = _edges_in_window(_rising_edges(rows, denominator, threshold), window)
    ratio = None
    if num_edges is not None and den_edges is not None and den_edges:
        ratio = len(num_edges) / max(len(den_edges), 1)
    return {
        "numerator_signal": numerator,
        "denominator_signal": denominator,
        "numerator_edges": None if num_edges is None else len(num_edges),
        "denominator_edges": None if den_edges is None else len(den_edges),
        "observed_ratio": ratio,
    }


def _frequency_ratio(
    rows: list[dict[str, float]],
    numerator: str,
    denominator: str,
    threshold: float,
    start: float,
    end: float,
) -> tuple[float, dict]:
    window_rows = [row for row in rows if start <= row.get("time", 0.0) <= end]
    num_edges = _rising_edges(window_rows, numerator, threshold) or []
    den_edges = _rising_edges(window_rows, denominator, threshold) or []
    details = {
        "window": [start, end],
        "numerator_signal": numerator,
        "denominator_signal": denominator,
        "numerator_edges": len(num_edges),
        "denominator_edges": len(den_edges),
    }
    if len(num_edges) < 3 or len(den_edges) < 3:
        return float("nan"), details
    num_freq = (len(num_edges) - 1) / max(num_edges[-1] - num_edges[0], 1e-18)
    den_freq = (len(den_edges) - 1) / max(den_edges[-1] - den_edges[0], 1e-18)
    ratio = num_freq / max(den_freq, 1e-18)
    details.update(numerator_frequency=num_freq, denominator_frequency=den_freq, observed_ratio=ratio)
    return ratio, details


def _signal_span(rows: list[dict[str, float]], signal: str) -> float | None:
    values = [row[signal] for row in rows if signal in row]
    if not values:
        return None
    return max(values) - min(values)


def _signal_range_ok(rows: list[dict[str, float]], signal: str, lower: float, upper: float) -> bool | None:
    values = [row[signal] for row in rows if signal in row]
    if not values:
        return None
    return all(lower <= value <= upper for value in values)


def _weighted_high_fraction(rows: list[dict[str, float]], signal: str, threshold: float, start: float, end: float) -> float | None:
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
        if not start <= mid_time <= end:
            continue
        total_dt += dt
        if 0.5 * (prev[signal] + cur[signal]) >= threshold:
            high_dt += dt
    if total_dt <= 0.0:
        return None
    return high_dt / total_dt


def _first_threshold_crossing(rows: list[dict[str, float]], signal: str, threshold: float) -> float | None:
    samples = [(row.get("time", 0.0), row[signal]) for row in rows if signal in row]
    if len(samples) < 2:
        return None
    prev_value = samples[0][1]
    for time, value in samples[1:]:
        if prev_value < threshold <= value:
            return time
        prev_value = value
    return None


def _declared_parameters(dut_path: Path | None) -> set[str]:
    if dut_path is None or not dut_path.exists():
        return set()
    text = dut_path.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"\bparameter\s+(?:real|integer|string)?\s*([A-Za-z_][A-Za-z0-9_]*)\b", text))


def _passed_instance_parameters(tb_path: Path | None) -> set[str]:
    if tb_path is None or not tb_path.exists():
        return set()
    text = tb_path.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", text))


def _base_relation_result(relation: dict) -> dict:
    return {
        "id": relation["id"],
        "type": relation["type"],
        "severity": relation.get("severity", "hard"),
        "passed": False,
        "status": "FAIL",
        "repair_hint": relation.get("repair_hint", ""),
    }


def _set_no_data(result: dict, reason: str) -> dict:
    result.update(status="NO_DATA", passed=(result.get("severity") == "advisory"), no_data_reason=reason)
    return result


def _set_skipped(result: dict, reason: str) -> dict:
    result.update(status="SKIP", passed=True, no_data_reason=reason)
    return result


def _evaluate_relation(
    graph: dict,
    relation: dict,
    fieldnames: list[str],
    rows: list[dict[str, float]],
    dut_path: Path | None,
    tb_path: Path | None,
) -> dict:
    result = _base_relation_result(relation)
    rtype = relation["type"]

    if rtype == "source_declares_parameters":
        declared = _declared_parameters(dut_path)
        passed_params = _passed_instance_parameters(tb_path)
        any_params = set(relation.get("parameters_any", []))
        recommended = set(relation.get("parameters_recommended", []))
        required_from_tb = passed_params & (any_params | recommended)
        missing_from_tb = sorted(required_from_tb - declared)
        missing_recommended = sorted((any_params | recommended) - declared)
        has_any = bool(any_params & declared)
        if dut_path is None or not dut_path.exists():
            return _set_no_data(result, "missing_dut_source")
        result.update(
            declared_parameters=sorted(declared),
            passed_instance_parameters=sorted(passed_params),
            missing_passed_parameters=missing_from_tb,
            missing_recommended_parameters=missing_recommended,
            has_any_ratio_parameter=has_any,
        )
        result["passed"] = not missing_from_tb and has_any
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "edge_liveness":
        signal = _resolve_node_signal(graph, relation["node"], fieldnames)
        if signal is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, f"node_signal_missing:{relation['node']}")
            return _set_no_data(result, f"node_signal_missing:{relation['node']}")
        threshold = float(relation.get("threshold", 0.45))
        edges = _rising_edges(rows, signal, threshold)
        min_edges = int(relation.get("min_rising_edges", 1))
        observed = None if edges is None else len(edges)
        result.update(signal=signal, observed_rising_edges=observed, expected_min_rising_edges=min_edges)
        result["passed"] = observed is not None and observed >= min_edges
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "edge_count_ratio_window":
        numerator = _resolve_node_signal(graph, relation["numerator_node"], fieldnames)
        denominator = _resolve_node_signal(graph, relation["denominator_node"], fieldnames)
        if numerator is None or denominator is None:
            return _set_no_data(result, "ratio_signal_missing")
        threshold = float(relation.get("threshold", 0.45))
        window = _window_from_fraction(rows, relation.get("window_fraction"))
        details = _edge_count_ratio(rows, numerator, denominator, threshold, window)
        expected = float(relation.get("expected_ratio", 1.0))
        tolerance = float(relation.get("tolerance", 0.05))
        min_edges = int(relation.get("min_edges", 1))
        ratio = details.get("observed_ratio")
        result.update(details, window=None if window is None else list(window), expected_ratio=expected, tolerance=tolerance)
        result["passed"] = (
            ratio is not None
            and details.get("numerator_edges", 0) >= min_edges
            and details.get("denominator_edges", 0) >= min_edges
            and abs(float(ratio) - expected) <= tolerance
        )
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "optional_frequency_ratio_window":
        numerator = _resolve_node_signal(graph, relation["numerator_node"], fieldnames)
        denominator = _resolve_node_signal(graph, relation["denominator_node"], fieldnames)
        if numerator is None or denominator is None:
            return _set_no_data(result, "optional_ratio_signal_missing")
        threshold = float(relation.get("threshold", 0.45))
        window = _window_from_fraction(rows, relation.get("window_fraction"))
        if window is None:
            return _set_no_data(result, "missing_time_window")
        ratio, details = _frequency_ratio(rows, numerator, denominator, threshold, window[0], window[1])
        result.update(details)
        result["passed"] = math.isfinite(ratio)
        result["status"] = "PASS" if result["passed"] else "NO_DATA"
        return result

    if rtype == "signal_span":
        signal = _resolve_node_signal(graph, relation["node"], fieldnames)
        if signal is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, f"node_signal_missing:{relation['node']}")
            return _set_no_data(result, f"node_signal_missing:{relation['node']}")
        span = _signal_span(rows, signal)
        min_span = float(relation.get("min_span", 0.0))
        result.update(signal=signal, observed_span=span, expected_min_span=min_span)
        result["passed"] = span is not None and span >= min_span
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "code_coverage":
        threshold = float(relation.get("threshold", 0.45))
        codes, details = _resolve_code_series(
            rows,
            fieldnames,
            code_signals=relation.get("code_signals", []),
            bit_prefixes=relation.get("bit_prefixes", []),
            min_width=int(relation.get("min_width", 1)),
            threshold=threshold,
        )
        if not codes:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, "code_observables_missing")
            return _set_no_data(result, "code_observables_missing")
        unique_codes = len(set(codes))
        min_unique = int(relation.get("min_unique_codes", 2))
        result.update(details, unique_codes=unique_codes, min_unique_codes=min_unique)
        result["passed"] = unique_codes >= min_unique
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "analog_reconstruction":
        input_signal = _resolve_node_signal(graph, relation["input_node"], fieldnames)
        output_signal = _resolve_node_signal(graph, relation["output_node"], fieldnames)
        if input_signal is None or output_signal is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, "reconstruction_signals_missing")
            return _set_no_data(result, "reconstruction_signals_missing")
        reset_signal = _resolve_node_signal(graph, relation.get("reset_node", ""), fieldnames)
        reset_threshold = float(relation.get("reset_threshold", 0.45))
        errors: list[float] = []
        input_values: list[float] = []
        output_values: list[float] = []
        for row in rows:
            if input_signal not in row or output_signal not in row:
                continue
            if reset_signal is not None and row.get(reset_signal, 0.0) <= reset_threshold:
                continue
            input_values.append(row[input_signal])
            output_values.append(row[output_signal])
            errors.append(abs(row[input_signal] - row[output_signal]))
        if not errors:
            return _set_no_data(result, "no_reconstruction_samples")
        input_span = max(input_values) - min(input_values)
        output_span = max(output_values) - min(output_values)
        avg_abs_error = sum(errors) / len(errors)
        max_avg_abs_error = float(relation.get("max_avg_abs_error", 0.05))
        min_input_span = float(relation.get("min_input_span", 0.1))
        min_output_span = float(relation.get("min_output_span", 0.1))
        result.update(
            input_signal=input_signal,
            output_signal=output_signal,
            reset_signal=reset_signal,
            input_span=input_span,
            output_span=output_span,
            avg_abs_error=avg_abs_error,
            max_avg_abs_error=max_avg_abs_error,
        )
        result["passed"] = (
            input_span >= min_input_span
            and output_span >= min_output_span
            and avg_abs_error <= max_avg_abs_error
        )
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "differential_span":
        positive = _resolve_node_signal(graph, relation["positive_node"], fieldnames)
        negative = _resolve_node_signal(graph, relation["negative_node"], fieldnames)
        if positive is None or negative is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, "differential_signals_missing")
            return _set_no_data(result, "differential_signals_missing")
        diff_values = [row[positive] - row[negative] for row in rows if positive in row and negative in row]
        if not diff_values:
            return _set_no_data(result, "no_differential_samples")
        diff_span = max(diff_values) - min(diff_values)
        min_span = float(relation.get("min_span", 0.1))
        result.update(positive_signal=positive, negative_signal=negative, observed_diff_span=diff_span, expected_min_span=min_span)
        result["passed"] = diff_span >= min_span
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "flag_high":
        signal = _resolve_node_signal(graph, relation["node"], fieldnames)
        if signal is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, f"node_signal_missing:{relation['node']}")
            return _set_no_data(result, f"node_signal_missing:{relation['node']}")
        threshold = float(relation.get("threshold", 0.45))
        high_seen = any(row.get(signal, 0.0) > threshold for row in rows)
        result.update(signal=signal, threshold=threshold, high_seen=high_seen)
        result["passed"] = high_seen
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "lock_after_ratio":
        ref = _resolve_node_signal(graph, relation["reference_node"], fieldnames)
        fb = _resolve_node_signal(graph, relation["feedback_node"], fieldnames)
        lock = _resolve_node_signal(graph, relation["lock_node"], fieldnames)
        if ref is None or fb is None or lock is None:
            return _set_no_data(result, "lock_relation_signal_missing")
        threshold = float(relation.get("threshold", 0.45))
        window = _window_from_fraction(rows, relation.get("window_fraction"))
        details = _edge_count_ratio(rows, fb, ref, threshold, window)
        lock_edges = _rising_edges(rows, lock, threshold)
        first_lock = None if not lock_edges else lock_edges[0]
        expected = float(relation.get("expected_ratio", 1.0))
        tolerance = float(relation.get("ratio_tolerance", 0.05))
        max_lock = float(relation.get("max_first_lock_time_s", 1e-6))
        ratio = details.get("observed_ratio")
        ratio_ok = ratio is not None and abs(float(ratio) - expected) <= tolerance
        lock_ok = first_lock is not None and first_lock <= max_lock
        result.update(
            details,
            lock_signal=lock,
            first_lock_time_s=first_lock,
            expected_max_first_lock_time_s=max_lock,
            expected_ratio=expected,
            tolerance=tolerance,
            ratio_ok=ratio_ok,
            lock_ok=lock_ok,
        )
        result["passed"] = ratio_ok and lock_ok
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    if rtype == "ratio_hop_tracking":
        ref = _resolve_node_signal(graph, relation["reference_node"], fieldnames)
        dco = _resolve_node_signal(graph, relation["dco_node"], fieldnames)
        ratio_ctrl = _resolve_node_signal(graph, relation["ratio_control_node"], fieldnames)
        lock = _resolve_node_signal(graph, relation["lock_node"], fieldnames)
        control = _resolve_node_signal(graph, relation["control_node"], fieldnames)
        if ref is None or dco is None or ratio_ctrl is None:
            if relation.get("skip_if_missing"):
                return _set_skipped(result, "ratio_hop_nodes_absent")
            return _set_no_data(result, "ratio_hop_required_signal_missing")
        hop_t = _first_threshold_crossing(rows, ratio_ctrl, float(relation.get("hop_threshold", 5.0)))
        if hop_t is None:
            result.update(ratio_control_signal=ratio_ctrl)
            result["status"] = "FAIL"
            result["passed"] = False
            result["failure_reason"] = "ratio_hop_not_detected"
            return result
        threshold = float(relation.get("threshold", 0.45))
        pre_window = [hop_t + float(x) for x in relation.get("pre_window_s", [-1e-6, -2e-7])]
        post_window = [hop_t + float(x) for x in relation.get("post_window_s", [1.2e-6, 2.5e-6])]
        pre_ratio, pre_details = _frequency_ratio(rows, dco, ref, threshold, pre_window[0], pre_window[1])
        post_ratio, post_details = _frequency_ratio(rows, dco, ref, threshold, post_window[0], post_window[1])
        pre_expected = float(relation.get("pre_expected_ratio", 4.0))
        post_expected = float(relation.get("post_expected_ratio", 6.0))
        pre_tol = float(relation.get("pre_tolerance", 0.25))
        post_tol = float(relation.get("post_tolerance", 0.35))
        pre_ok = math.isfinite(pre_ratio) and abs(pre_ratio - pre_expected) <= pre_tol
        post_ok = math.isfinite(post_ratio) and abs(post_ratio - post_expected) <= post_tol
        min_lock_fraction = float(relation.get("min_lock_fraction", 0.8))
        pre_lock_fraction = None
        post_lock_fraction = None
        if lock is not None:
            pre_lock_window = [hop_t + float(x) for x in relation.get("pre_lock_window_s", [-4e-7, -5e-8])]
            post_lock_window = [hop_t + float(x) for x in relation.get("post_lock_window_s", [1.8e-6, 2.8e-6])]
            max_lock = max((row.get(lock, 0.0) for row in rows), default=0.9)
            lock_threshold = max_lock * 0.5
            pre_lock_fraction = _weighted_high_fraction(rows, lock, lock_threshold, pre_lock_window[0], pre_lock_window[1])
            post_lock_fraction = _weighted_high_fraction(rows, lock, lock_threshold, post_lock_window[0], post_lock_window[1])
        vctrl_range_ok = None
        if control is not None:
            vctrl_range_ok = _signal_range_ok(rows, control, -1e-6, 1.2)
        lock_ok = (
            pre_lock_fraction is not None
            and post_lock_fraction is not None
            and pre_lock_fraction >= min_lock_fraction
            and post_lock_fraction >= min_lock_fraction
        )
        control_ok = vctrl_range_ok is not False
        result.update(
            reference_signal=ref,
            dco_signal=dco,
            ratio_control_signal=ratio_ctrl,
            lock_signal=lock,
            control_signal=control,
            hop_time_s=hop_t,
            pre_ratio=pre_ratio,
            post_ratio=post_ratio,
            pre_expected_ratio=pre_expected,
            post_expected_ratio=post_expected,
            pre_ratio_ok=pre_ok,
            post_ratio_ok=post_ok,
            pre_lock_fraction=pre_lock_fraction,
            post_lock_fraction=post_lock_fraction,
            lock_ok=lock_ok,
            vctrl_range_ok=vctrl_range_ok,
            pre_details=pre_details,
            post_details=post_details,
        )
        result["passed"] = pre_ok and post_ok and lock_ok and control_ok
        result["status"] = "PASS" if result["passed"] else "FAIL"
        return result

    result.update(status="NO_DATA", no_data_reason=f"unsupported_relation_type:{rtype}")
    return result


def evaluate_graph(
    graph: dict,
    *,
    case_label: str,
    csv_path: Path | None,
    dut_path: Path | None,
    tb_path: Path | None,
) -> dict:
    fieldnames, rows = _load_rows(csv_path)
    relations = [
        _evaluate_relation(graph, relation, fieldnames, rows, dut_path, tb_path)
        for relation in graph.get("relations", [])
    ]
    failed_hard = [
        relation["id"]
        for relation in relations
        if relation.get("severity") == "hard" and not relation.get("passed")
    ]
    passed = [relation["id"] for relation in relations if relation.get("passed")]
    no_data = [relation["id"] for relation in relations if relation.get("status") == "NO_DATA"]
    return {
        "case_label": case_label,
        "graph_id": graph["id"],
        "csv_path": "" if csv_path is None else str(csv_path),
        "dut_path": "" if dut_path is None else str(dut_path),
        "tb_path": "" if tb_path is None else str(tb_path),
        "fieldnames": fieldnames,
        "row_count": len(rows),
        "status": "PASS" if not failed_hard else "FAIL_GRAPH",
        "passed_relations": passed,
        "failed_hard_relations": failed_hard,
        "no_data_relations": no_data,
        "relations": relations,
    }


def _paths_from_result_json(path: Path) -> tuple[Path | None, Path | None, Path | None]:
    data = _read_json(path)
    artifacts = data.get("artifacts", {})
    csv_raw = artifacts.get("csv") or artifacts.get("csv_path")
    dut_raw = artifacts.get("dut") or artifacts.get("dut_path")
    tb_raw = artifacts.get("tb") or artifacts.get("tb_path")
    csv_path = Path(csv_raw) if csv_raw else path.parent / "tran.csv"
    dut_path = Path(dut_raw) if dut_raw else None
    tb_path = Path(tb_raw) if tb_raw else None
    return csv_path, dut_path, tb_path


def _write_markdown(path: Path, reports: list[dict]) -> None:
    lines = [
        "# System Contract Graph Report",
        "",
        "| Case | Status | Failed hard relations | No data | Key metrics |",
        "|---|---:|---|---|---|",
    ]
    for report in reports:
        metrics: list[str] = []
        for relation in report.get("relations", []):
            rid = relation["id"]
            if "observed_ratio" in relation and relation["observed_ratio"] is not None:
                metrics.append(f"{rid}:ratio={relation['observed_ratio']:.3g}")
            if "pre_ratio" in relation and relation.get("pre_ratio") is not None:
                metrics.append(f"{rid}:pre={relation['pre_ratio']:.3g},post={relation.get('post_ratio', float('nan')):.3g}")
            if "observed_rising_edges" in relation:
                metrics.append(f"{rid}:edges={relation.get('observed_rising_edges')}")
            if "first_lock_time_s" in relation and relation.get("first_lock_time_s") is not None:
                metrics.append(f"{rid}:lock={relation['first_lock_time_s']:.3g}")
            if "unique_codes" in relation:
                metrics.append(f"{rid}:codes={relation.get('unique_codes')}")
            if "avg_abs_error" in relation and relation.get("avg_abs_error") is not None:
                metrics.append(f"{rid}:err={relation['avg_abs_error']:.3g}")
            if "observed_span" in relation and relation.get("observed_span") is not None:
                metrics.append(f"{rid}:span={relation['observed_span']:.3g}")
            if "observed_diff_span" in relation and relation.get("observed_diff_span") is not None:
                metrics.append(f"{rid}:diffspan={relation['observed_diff_span']:.3g}")
            if "high_seen" in relation:
                metrics.append(f"{rid}:high={relation.get('high_seen')}")
        lines.append(
            f"| `{report['case_label']}` | {report['status']} | "
            f"{', '.join(f'`{item}`' for item in report.get('failed_hard_relations', [])) or '-'} | "
            f"{', '.join(f'`{item}`' for item in report.get('no_data_relations', [])) or '-'} | "
            f"{'; '.join(metrics[:6])} |"
        )
    lines.append("")
    for report in reports:
        lines.extend([f"## {report['case_label']}", ""])
        for relation in report.get("relations", []):
            status = relation.get("status")
            lines.append(f"- `{relation['id']}`: {status}")
            if relation.get("repair_hint") and status != "PASS":
                lines.append(f"  repair_hint: {relation['repair_hint']}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _parse_case_specs(args: argparse.Namespace) -> list[dict]:
    cases: list[dict] = []
    labels = args.case_label or []
    for idx, result_json in enumerate(args.result_json or []):
        path = Path(result_json)
        label = labels[idx] if idx < len(labels) else path.parent.name
        csv_path, dut_path, tb_path = _paths_from_result_json(path)
        cases.append({"label": label, "csv": csv_path, "dut": dut_path, "tb": tb_path})
    if args.csv:
        label = labels[len(cases)] if len(labels) > len(cases) else (args.case or Path(args.csv).parent.name)
        cases.append(
            {
                "label": label,
                "csv": Path(args.csv),
                "dut": Path(args.dut) if args.dut else None,
                "tb": Path(args.tb) if args.tb else None,
            }
        )
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graphs", default=str(DEFAULT_GRAPHS))
    parser.add_argument("--graph-id", default="pll_feedback_lock_v0")
    parser.add_argument("--result-json", action="append", default=[])
    parser.add_argument("--case-label", action="append", default=[])
    parser.add_argument("--case", default="")
    parser.add_argument("--csv", default="")
    parser.add_argument("--dut", default="")
    parser.add_argument("--tb", default="")
    parser.add_argument("--out-root", default="results/system-contract-graph-v0-2026-04-27")
    args = parser.parse_args()

    graphs = _load_graphs(Path(args.graphs))
    if args.graph_id not in graphs:
        raise SystemExit(f"unknown graph id: {args.graph_id}")
    graph = graphs[args.graph_id]
    cases = _parse_case_specs(args)
    if not cases:
        raise SystemExit("provide at least one --result-json or --csv")

    out_root = Path(args.out_root)
    reports = []
    for case in cases:
        report = evaluate_graph(
            graph,
            case_label=case["label"],
            csv_path=case["csv"],
            dut_path=case["dut"],
            tb_path=case["tb"],
        )
        reports.append(report)
        _write_json(out_root / f"{case['label']}.json", report)
        print(f"[{case['label']}] {report['status']} failed={','.join(report['failed_hard_relations']) or '-'}")
    summary = {
        "graph_id": args.graph_id,
        "total_cases": len(reports),
        "pass_count": sum(1 for report in reports if report["status"] == "PASS"),
        "cases": [
            {
                "case_label": report["case_label"],
                "status": report["status"],
                "failed_hard_relations": report["failed_hard_relations"],
                "no_data_relations": report["no_data_relations"],
            }
            for report in reports
        ],
    }
    _write_json(out_root / "summary.json", summary)
    _write_markdown(out_root / "summary.md", reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
