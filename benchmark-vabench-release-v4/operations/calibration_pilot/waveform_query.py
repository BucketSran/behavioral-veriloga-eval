#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_ALLOWED_ROOTS = (
    Path("/tmp/vabench-visible/evas-output"),
    Path("/workspace/work/evas-output"),
)
DEFAULT_MAX_RESULTS = 256
MAX_ROWS = 1_000_000


class QueryError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise QueryError(message)


def json_exit(payload: dict[str, Any], status: int = 0) -> int:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return status


def resolve_allowed(path: str, allowed_roots: list[str]) -> Path:
    candidate = Path(path).expanduser().resolve(strict=True)
    roots = [Path(root).expanduser().resolve(strict=True) for root in allowed_roots]
    if not any(candidate == root or root in candidate.parents for root in roots):
        raise QueryError(f"trace path resolves outside allowed roots: {candidate}")
    if not candidate.is_file():
        raise QueryError(f"trace path is not a file: {candidate}")
    return candidate


def load_trace(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise QueryError("CSV trace has no header")
        fields = [field.strip() for field in reader.fieldnames if field and field.strip()]
        if "time" not in fields:
            raise QueryError("CSV trace must include a time column")
        for index, raw_row in enumerate(reader, start=2):
            if len(rows) >= MAX_ROWS:
                raise QueryError(f"CSV trace exceeds row limit {MAX_ROWS}")
            parsed: dict[str, float] = {}
            for field in fields:
                value = raw_row.get(field, "")
                try:
                    parsed[field] = float(value)
                except (TypeError, ValueError) as exc:
                    raise QueryError(f"non-numeric value at line {index}, column {field}") from exc
            rows.append(parsed)
    if not rows:
        raise QueryError("CSV trace has no data rows")
    rows.sort(key=lambda row: row["time"])
    return fields, rows


def require_signal(fields: list[str], signal: str) -> None:
    if signal not in fields:
        raise QueryError(f"unknown signal {signal!r}; available={fields}")


def finite_values(rows: list[dict[str, float]], signal: str) -> list[tuple[float, float]]:
    values = [(row["time"], row[signal]) for row in rows]
    return [(time, value) for time, value in values if math.isfinite(time) and math.isfinite(value)]


def interpolate_time(
    t0: float, y0: float, t1: float, y1: float, threshold: float
) -> float:
    if y1 == y0:
        return t0
    return t0 + (threshold - y0) * (t1 - t0) / (y1 - y0)


def find_crossings(
    rows: list[dict[str, float]],
    signal: str,
    threshold: float,
    direction: str,
    max_results: int,
) -> list[dict[str, float | str]]:
    points = finite_values(rows, signal)
    events: list[dict[str, float | str]] = []
    for (t0, y0), (t1, y1) in zip(points, points[1:]):
        if t1 == t0 or y0 == y1:
            continue
        rising = y0 < threshold <= y1
        falling = y0 > threshold >= y1
        if not rising and not falling:
            continue
        event_direction = "rising" if rising else "falling"
        if direction != "either" and direction != event_direction:
            continue
        events.append(
            {
                "time": interpolate_time(t0, y0, t1, y1, threshold),
                "direction": event_direction,
                "before_time": t0,
                "after_time": t1,
            }
        )
        if len(events) >= max_results:
            break
    return events


def sample_signal(
    rows: list[dict[str, float]], signal: str, time: float, method: str
) -> dict[str, float | str | None]:
    points = finite_values(rows, signal)
    if time <= points[0][0]:
        return {
            "time": time,
            "value": points[0][1],
            "source_time": points[0][0],
            "method": method,
        }
    if time >= points[-1][0]:
        return {
            "time": time,
            "value": points[-1][1],
            "source_time": points[-1][0],
            "method": method,
        }
    previous = points[0]
    for current in points[1:]:
        if current[0] >= time:
            if method == "previous":
                return {
                    "time": time,
                    "value": previous[1],
                    "source_time": previous[0],
                    "method": method,
                }
            if method == "nearest":
                selected = (
                    previous
                    if abs(time - previous[0]) <= abs(current[0] - time)
                    else current
                )
                return {
                    "time": time,
                    "value": selected[1],
                    "source_time": selected[0],
                    "method": method,
                }
            value = previous[1] + (time - previous[0]) * (current[1] - previous[1]) / (
                current[0] - previous[0]
            )
            return {"time": time, "value": value, "source_time": None, "method": method}
        previous = current
    return {
        "time": time,
        "value": points[-1][1],
        "source_time": points[-1][0],
        "method": method,
    }


def parse_times(args: argparse.Namespace) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for time_value in args.time or []:
        events.append({"time": float(time_value)})
    if args.times:
        for item in args.times.split(","):
            if item.strip():
                events.append({"time": float(item)})
    if args.event_times:
        decoded = json.loads(args.event_times)
        if not isinstance(decoded, list):
            raise QueryError("--event-times must be a JSON list")
        for item in decoded:
            if isinstance(item, (int, float)):
                events.append({"time": float(item)})
            elif isinstance(item, dict) and isinstance(item.get("time"), (int, float)):
                events.append(dict(item, time=float(item["time"])))
            else:
                raise QueryError("event times must be numbers or objects with numeric time")
    if not events:
        raise QueryError("sample requires --time, --times, or --event-times")
    if len(events) > args.max_results:
        raise QueryError(f"requested sample count exceeds --max-results={args.max_results}")
    return events


def summarize(fields: list[str], rows: list[dict[str, float]], max_results: int) -> dict[str, Any]:
    signals = [field for field in fields if field != "time"]
    stats: dict[str, dict[str, float]] = {}
    for signal in signals[:max_results]:
        values = [value for _, value in finite_values(rows, signal)]
        stats[signal] = {
            "min": min(values),
            "max": max(values),
            "first": values[0],
            "last": values[-1],
        }
    return {
        "row_count": len(rows),
        "time_start": rows[0]["time"],
        "time_stop": rows[-1]["time"],
        "signals": signals[:max_results],
        "truncated": len(signals) > max_results,
        "stats": stats,
    }


def cycle_metrics(events: list[dict[str, Any]], max_results: int) -> dict[str, Any]:
    times = [float(event["time"]) for event in events]
    periods = [b - a for a, b in zip(times, times[1:]) if b >= a]
    payload: dict[str, Any] = {
        "event_count": len(times),
        "periods": periods[:max_results],
        "truncated": len(periods) > max_results,
    }
    if periods:
        payload.update(
            {
                "period_min": min(periods),
                "period_max": max(periods),
                "period_mean": mean(periods),
                "frequency_mean": 1.0 / mean(periods) if mean(periods) else None,
            }
        )
    return payload


def pair_next_response(
    request_events: list[dict[str, Any]],
    response_events: list[dict[str, Any]],
    max_results: int,
) -> list[dict[str, float]]:
    pairs: list[dict[str, float]] = []
    response_index = 0
    response_times = [float(event["time"]) for event in response_events]
    for request_event in request_events:
        request_time = float(request_event["time"])
        while response_index < len(response_times) and response_times[response_index] < request_time:
            response_index += 1
        if response_index >= len(response_times):
            break
        response_time = response_times[response_index]
        pairs.append(
            {
                "request_time": request_time,
                "response_time": response_time,
                "latency": response_time - request_time,
            }
        )
        response_index += 1
        if len(pairs) >= max_results:
            break
    return pairs


def compare_traces(
    rows: list[dict[str, float]],
    baseline_rows: list[dict[str, float]],
    signal: str,
    baseline_signal: str,
    method: str,
    max_results: int,
) -> dict[str, Any]:
    samples = []
    for row in baseline_rows[:max_results]:
        time = row["time"]
        candidate = sample_signal(rows, signal, time, method)["value"]
        baseline = row[baseline_signal]
        if not isinstance(candidate, (int, float)):
            continue
        samples.append(
            {
                "time": time,
                "candidate": candidate,
                "baseline": baseline,
                "difference": candidate - baseline,
            }
        )
    differences = [sample["difference"] for sample in samples]
    return {
        "sample_count": len(samples),
        "truncated": len(baseline_rows) > max_results,
        "max_abs_difference": max(
            (abs(difference) for difference in differences), default=None
        ),
        "mean_abs_difference": (
            mean(abs(difference) for difference in differences)
            if differences
            else None
        ),
        "rms_difference": (
            math.sqrt(mean(difference * difference for difference in differences))
            if differences
            else None
        ),
        "samples": samples,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="Read-only waveform CSV query helper")
    parser.add_argument("--trace", required=True, help="CSV trace path")
    parser.add_argument(
        "--allowed-root",
        action="append",
        default=[],
        help="Allowed trace root; may be repeated",
    )
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=JsonArgumentParser
    )

    subparsers.add_parser("list")
    subparsers.add_parser("summary")

    crossings = subparsers.add_parser("crossings")
    crossings.add_argument("--signal", required=True)
    crossings.add_argument("--threshold", type=float, required=True)
    crossings.add_argument("--direction", choices=("rising", "falling", "either"), default="either")

    sample = subparsers.add_parser("sample")
    sample.add_argument("--signal", required=True)
    sample.add_argument("--time", action="append")
    sample.add_argument("--times")
    sample.add_argument("--event-times")
    sample.add_argument("--method", choices=("nearest", "previous", "linear"), default="linear")

    cycles = subparsers.add_parser("cycles")
    cycles.add_argument("--signal", required=True)
    cycles.add_argument("--threshold", type=float, required=True)
    cycles.add_argument("--direction", choices=("rising", "falling", "either"), default="rising")

    pair = subparsers.add_parser("pair")
    pair.add_argument("--request-signal", required=True)
    pair.add_argument("--request-threshold", type=float, required=True)
    pair.add_argument("--request-direction", choices=("rising", "falling", "either"), default="rising")
    pair.add_argument("--response-signal", required=True)
    pair.add_argument("--response-threshold", type=float, required=True)
    pair.add_argument("--response-direction", choices=("rising", "falling", "either"), default="rising")

    compare = subparsers.add_parser("compare")
    compare.add_argument("--baseline-trace", required=True)
    compare.add_argument("--signal", required=True)
    compare.add_argument("--baseline-signal")
    compare.add_argument("--method", choices=("nearest", "previous", "linear"), default="linear")
    return parser


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if args.max_results < 1 or args.max_results > 10_000:
        raise QueryError("--max-results must be between 1 and 10000")
    allowed_roots = args.allowed_root or [str(root) for root in DEFAULT_ALLOWED_ROOTS]
    trace_path = resolve_allowed(args.trace, allowed_roots)
    fields, rows = load_trace(trace_path)

    if args.command in {"list", "summary"}:
        payload = summarize(fields, rows, args.max_results)
    elif args.command == "crossings":
        require_signal(fields, args.signal)
        payload = {
            "events": find_crossings(rows, args.signal, args.threshold, args.direction, args.max_results)
        }
    elif args.command == "sample":
        require_signal(fields, args.signal)
        payload = {
            "samples": [
                dict(event, **sample_signal(rows, args.signal, float(event["time"]), args.method))
                for event in parse_times(args)
            ]
        }
    elif args.command == "cycles":
        require_signal(fields, args.signal)
        events = find_crossings(rows, args.signal, args.threshold, args.direction, args.max_results + 1)
        payload = cycle_metrics(events, args.max_results)
    elif args.command == "pair":
        require_signal(fields, args.request_signal)
        require_signal(fields, args.response_signal)
        requests = find_crossings(
            rows,
            args.request_signal,
            args.request_threshold,
            args.request_direction,
            args.max_results,
        )
        responses = find_crossings(
            rows,
            args.response_signal,
            args.response_threshold,
            args.response_direction,
            args.max_results * 2,
        )
        payload = {"pairs": pair_next_response(requests, responses, args.max_results)}
    elif args.command == "compare":
        require_signal(fields, args.signal)
        baseline_path = resolve_allowed(args.baseline_trace, allowed_roots)
        baseline_fields, baseline_rows = load_trace(baseline_path)
        baseline_signal = args.baseline_signal or args.signal
        require_signal(baseline_fields, baseline_signal)
        payload = compare_traces(
            rows,
            baseline_rows,
            args.signal,
            baseline_signal,
            args.method,
            args.max_results,
        )
    else:
        raise QueryError(f"unknown command {args.command}")
    return {
        "ok": True,
        "command": args.command,
        "trace": os.fspath(trace_path),
        **payload,
    }


def main(argv: list[str] | None = None) -> int:
    try:
        return json_exit(run(argv), 0)
    except QueryError as exc:
        return json_exit({"ok": False, "error": str(exc)}, 2)
    except (OSError, json.JSONDecodeError, argparse.ArgumentError) as exc:
        return json_exit({"ok": False, "error": str(exc)}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
