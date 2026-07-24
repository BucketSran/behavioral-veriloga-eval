"""Small primitives for stimulus-relative V4 waveform checkers.

These helpers deliberately derive probe locations from observed events.  They
must not encode a particular public or private deck's absolute schedule.
"""
from __future__ import annotations

import re
from bisect import bisect_left
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from statistics import median


Row = dict[str, float]
Interval = tuple[float, float]
CheckResult = tuple[bool, str]
Checker = Callable[[list[Row]], CheckResult]

_SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9_.:+/-]+")


def diagnostic(
    property_id: str,
    category: str,
    *,
    expected: str,
    observed: str,
    event: str,
) -> str:
    """Return the stable, redaction-safe feedback shape used by V4 checkers."""

    return (
        f"property_id={property_id} category={category} "
        f"expected={expected} observed={observed} event={event}"
    )


def _redacted_observation(note: str) -> str:
    """Collapse a free-form checker note into a public-safe diagnostic token."""

    head = (note or "checker_failed").strip().split(";", 1)[0].split()
    token = head[0] if head else "checker_failed"
    token = token.split("=", 1)[0].split("@", 1)[0]
    token = _SAFE_TOKEN_RE.sub("_", token).strip("_")
    return (token or "checker_failed")[:96]


def structured_result(
    checker: Checker,
    property_ids: Iterable[str],
    *,
    event: str = "stimulus_relative_trace",
) -> Checker:
    """Wrap a checker with redacted property-level V4 diagnostics."""

    property_tuple = tuple(property_ids)
    primary = property_tuple[0] if property_tuple else "P_OBSERVABLE_CONTRACT"

    def wrapped(rows: list[Row]) -> CheckResult:
        ok, note = checker(rows)
        observed = _redacted_observation(note)
        if ok:
            return True, pass_note(property_tuple, observed)
        return False, diagnostic(
            primary,
            "observable_mismatch",
            expected="satisfy_observable_contract",
            observed=observed,
            event=event,
        )

    wrapped.__name__ = checker.__name__
    wrapped.__doc__ = checker.__doc__
    wrapped.__module__ = checker.__module__
    return wrapped


def require_signals(rows: list[Row], signals: Iterable[str], property_id: str) -> str | None:
    required = set(signals)
    if not rows:
        return diagnostic(
            property_id,
            "invalid_trace",
            expected="nonempty_trace",
            observed="empty_trace",
            event="full_trace",
        )
    missing = sorted(required - set(rows[0]))
    if missing:
        return diagnostic(
            property_id,
            "invalid_trace",
            expected="signals:" + ",".join(sorted(required)),
            observed="missing:" + ",".join(missing),
            event="full_trace",
        )
    return None


def sample(rows: list[Row], signal: str, time_s: float) -> float | None:
    """Linearly interpolate one public signal at ``time_s``."""

    if not rows or signal not in rows[0] or time_s < rows[0]["time"] or time_s > rows[-1]["time"]:
        return None
    if time_s == rows[0]["time"]:
        return rows[0][signal]
    for left, right in zip(rows, rows[1:]):
        t0 = left["time"]
        t1 = right["time"]
        if not (t0 <= time_s <= t1):
            continue
        if t1 == t0:
            return right[signal]
        alpha = (time_s - t0) / (t1 - t0)
        return left[signal] + alpha * (right[signal] - left[signal])
    return None


def mean_signal(rows: list[Row], signal: str) -> float | None:
    values = [row[signal] for row in rows if signal in row]
    if not values:
        return None
    return sum(values) / len(values)


def rows_in_interval(rows: list[Row], start: float, stop: float) -> list[Row]:
    return [row for row in rows if start <= row["time"] <= stop]


def mean_in_interval(rows: list[Row], signal: str, interval: Interval) -> float | None:
    return mean_signal(rows_in_interval(rows, interval[0], interval[1]), signal)


def median_step(rows: list[Row]) -> float:
    steps = [
        right["time"] - left["time"]
        for left, right in zip(rows, rows[1:])
        if right.get("time", 0.0) > left.get("time", 0.0)
    ]
    if not steps:
        return 0.0
    return percentile(steps, 0.5)


def intervals_where(
    rows: list[Row],
    predicate: Callable[[Row], bool],
    *,
    min_duration: float = 0.0,
) -> list[Interval]:
    """Return contiguous time intervals where an observed predicate holds."""

    intervals: list[Interval] = []
    start: float | None = None
    previous: float | None = None
    for row in rows:
        time_s = row["time"]
        if predicate(row):
            if start is None:
                start = time_s
            previous = time_s
        elif start is not None and previous is not None:
            if previous - start >= min_duration:
                intervals.append((start, previous))
            start = None
            previous = None
    if start is not None and previous is not None and previous - start >= min_duration:
        intervals.append((start, previous))
    return intervals


def inner_interval(
    interval: Interval, start_fraction: float, stop_fraction: float
) -> Interval | None:
    start, stop = interval
    if stop <= start:
        return None
    start_fraction = max(0.0, min(1.0, start_fraction))
    stop_fraction = max(0.0, min(1.0, stop_fraction))
    if stop_fraction <= start_fraction:
        return None
    span = stop - start
    return start + span * start_fraction, start + span * stop_fraction


def mean_in_inner_interval(
    rows: list[Row],
    signal: str,
    interval: Interval,
    start_fraction: float,
    stop_fraction: float,
) -> float | None:
    inner = inner_interval(interval, start_fraction, stop_fraction)
    if inner is None:
        return None
    return mean_in_interval(rows, signal, inner)


def sample_around_event(
    rows: list[Row],
    signal: str,
    event_time: float,
    *,
    step_multiplier: float = 2.0,
) -> tuple[float | None, float | None]:
    step = median_step(rows)
    if step <= 0.0:
        return None, None
    return (
        sample(rows, signal, event_time - step_multiplier * step),
        sample(rows, signal, event_time + step_multiplier * step),
    )


def nearest_row(rows: list[Row], time_s: float) -> Row | None:
    if not rows:
        return None
    return min(rows, key=lambda row: abs(row["time"] - time_s))


def logic_bits_to_int(row: Row, prefix: str, width: int, threshold: float = 0.45) -> int:
    return sum((1 << bit) for bit in range(width) if row[f"{prefix}{bit}"] > threshold)


def crossings(
    rows: list[Row],
    signal: str,
    *,
    threshold: float,
    direction: str,
) -> list[float]:
    """Return interpolated threshold-crossing times from the observed trace."""

    edges: list[float] = []
    for left, right in zip(rows, rows[1:]):
        v0 = left[signal]
        v1 = right[signal]
        if direction == "rising":
            hit = v0 <= threshold < v1
        elif direction == "falling":
            hit = v0 >= threshold > v1
        else:
            raise ValueError(f"unsupported crossing direction: {direction}")
        if not hit:
            continue
        if v1 == v0:
            edges.append(right["time"])
            continue
        alpha = (threshold - v0) / (v1 - v0)
        edges.append(left["time"] + alpha * (right["time"] - left["time"]))
    return edges


def normalize_affine_time(
    rows: list[Row],
    anchors: Iterable[tuple[str, float, str, float, int]],
) -> list[Row] | None:
    """Map an affinely transformed trace back to its canonical time axis.

    Anchors are ``(signal, threshold, direction, canonical_ns, occurrence)``
    tuples and must describe public input-stimulus edges only.
    """

    pairs: list[tuple[float, float]] = []
    for signal, threshold, direction, canonical_ns, occurrence in anchors:
        if not rows or signal not in rows[0]:
            return None
        observed = crossings(rows, signal, threshold=threshold, direction=direction)
        if occurrence >= len(observed):
            return None
        pairs.append((canonical_ns * 1e-9, observed[occurrence]))
    if len(pairs) < 2:
        return None
    canonical_first, observed_first = pairs[0]
    canonical_last, observed_last = pairs[-1]
    canonical_span = canonical_last - canonical_first
    if canonical_span <= 0 or observed_last <= observed_first:
        return None
    scale = (observed_last - observed_first) / canonical_span
    shift = observed_first - scale * canonical_first
    return [{**row, "time": (row["time"] - shift) / scale} for row in rows]


def probe_time(
    rows: list[Row],
    event_time: float,
    next_event_time: float | None,
    *,
    fraction: float = 0.25,
) -> float | None:
    """Choose a settled probe as a fraction of the observed event interval."""

    stop = rows[-1]["time"]
    interval_stop = stop if next_event_time is None else min(stop, next_event_time)
    if interval_stop <= event_time:
        return None
    return event_time + fraction * (interval_stop - event_time)


def event_label(kind: str, index: int, time_s: float) -> str:
    return f"{kind}[{index}]@{time_s:.6e}s"


def close(observed: float, expected: float, tolerance: float) -> bool:
    return abs(observed - expected) <= tolerance


def max_signal_value(rows: list[Row], signals: Iterable[str], *, default: float) -> float:
    values = [row[signal] for row in rows for signal in signals if signal in row]
    return max(values, default=default)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(fraction * (len(ordered) - 1))))
    return ordered[index]


def pass_note(property_ids: Iterable[str], summary: str) -> str:
    diagnostics = "; ".join(f"{property_id} mismatch_count=0" for property_id in property_ids)
    return f"{summary}; {diagnostics}"


@dataclass
class PropertyResult:
    """Compact, redacted diagnostic for one public property."""

    property_id: str
    checked: int = 0
    mismatch_count: int = 0
    expected: str = "contract_satisfied"
    observed: str = "contract_satisfied"
    sample_time: float = 0.0
    metric_gap: float = 0.0

    def check(self) -> None:
        self.checked += 1

    def compare(self, *, expected: float, observed: float, tolerance: float,
                time_s: float, label: str = "value") -> None:
        self.check()
        gap = abs(float(observed) - float(expected))
        if gap > tolerance:
            self.mismatch(
                expected=f"{label}={expected:.6g}+/-{tolerance:.3g}",
                observed=f"{label}={observed:.6g}", time_s=time_s, gap=gap,
            )

    def condition(self, passed: bool, *, expected: object, observed: object,
                  time_s: float, gap: float = 0.0) -> None:
        self.check()
        if not passed:
            self.mismatch(expected=expected, observed=observed, time_s=time_s, gap=gap)

    def mismatch(self, *, expected: object, observed: object,
                 time_s: float, gap: float = 0.0) -> None:
        self.mismatch_count += 1
        if self.mismatch_count == 1:
            self.expected = str(expected).replace(" ", "_")
            self.observed = str(observed).replace(" ", "_")
            self.sample_time = float(time_s)
            self.metric_gap = float(gap)

    def require_coverage(self, minimum: int = 1) -> None:
        if self.checked < minimum:
            self.mismatch(
                expected=f"checked>={minimum}", observed=f"checked={self.checked}",
                time_s=0.0, gap=float(minimum - self.checked),
            )

    def render(self) -> str:
        return (
            f"{self.property_id} checked={self.checked} "
            f"mismatch_count={self.mismatch_count} "
            f"expected={self.expected} observed={self.observed} "
            f"sample_time={self.sample_time:.12g} metric_gap={self.metric_gap:.6g}"
        )


def finish(task_id: str, results: list[PropertyResult], *, coverage: str,
           minimum_checks: int = 1) -> tuple[bool, str]:
    for result in results:
        result.require_coverage(minimum_checks)
    ok = all(result.mismatch_count == 0 for result in results)
    checked = sum(result.checked for result in results)
    mismatches = sum(result.mismatch_count for result in results)
    details = "; ".join(result.render() for result in results)
    return ok, (
        f"{task_id} checked={checked} mismatch_count={mismatches} "
        f"coverage={coverage}; {details}"
    )


def missing_trace(task_id: str, rows: list[Row], required: set[str],
                  property_ids: list[str]) -> tuple[list[PropertyResult], tuple[bool, str] | None]:
    results = [PropertyResult(property_id) for property_id in property_ids]
    missing = sorted(required - set(rows[0])) if rows else sorted(required)
    if not missing:
        return results, None
    observed = "missing_signals:" + ",".join(missing)
    for result in results:
        result.check()
        result.mismatch(
            expected="complete_public_trace", observed=observed,
            time_s=0.0, gap=float(len(missing)),
        )
    return results, finish(task_id, results, coverage="trace_incomplete")


def rising_indices(rows: list[Row], signal: str, threshold: float = 0.45) -> list[int]:
    return [index for index in range(1, len(rows))
            if float(rows[index - 1][signal]) <= threshold < float(rows[index][signal])]


def falling_indices(rows: list[Row], signal: str, threshold: float = 0.45) -> list[int]:
    return [index for index in range(1, len(rows))
            if float(rows[index - 1][signal]) >= threshold > float(rows[index][signal])]


def interpolate_crossing(previous: Row, current: Row, signal: str, threshold: float) -> float:
    v0 = float(previous[signal])
    v1 = float(current[signal])
    t0 = float(previous["time"])
    t1 = float(current["time"])
    if v1 == v0:
        return t1
    return t0 + (threshold - v0) / (v1 - v0) * (t1 - t0)


def edge_times(rows: list[Row], signal: str, *, threshold: float = 0.45,
               rising: bool = True) -> list[float]:
    indices = rising_indices(rows, signal, threshold) if rising else falling_indices(rows, signal, threshold)
    return [interpolate_crossing(rows[index - 1], rows[index], signal, threshold)
            for index in indices]


def row_at_or_after(rows: list[Row], time_s: float) -> Row:
    times = [float(row["time"]) for row in rows]
    return rows[min(bisect_left(times, time_s), len(rows) - 1)]


def row_before(rows: list[Row], time_s: float) -> Row:
    times = [float(row["time"]) for row in rows]
    return rows[max(0, bisect_left(times, time_s) - 1)]


def representative_clear_rows(rows: list[Row], *, has_enable: bool) -> list[Row]:
    """Select settled clear samples from rows in nondecreasing time order."""

    if not rows:
        return []

    def clear(row: Row) -> bool:
        reset = float(row.get("rst", 0.0)) > 0.45
        disabled = has_enable and float(row.get("enable", 0.0)) <= 0.45
        return reset or disabled

    selected: list[Row] = []
    last_selected = -1e99
    settled_index = 0
    for row in rows:
        time_s = float(row["time"])
        settled_time = time_s - 0.6e-9
        while (
            settled_index + 1 < len(rows)
            and float(rows[settled_index + 1]["time"]) < settled_time
        ):
            settled_index += 1
        if (
            clear(row)
            and clear(rows[settled_index])
            and time_s - last_selected >= 1e-9
        ):
            selected.append(row)
            last_selected = time_s
    return selected


def event_settle_delay(event_times: list[float], *, fraction: float = 0.12,
                       minimum_s: float = 1.5e-10, maximum_s: float = 2.0e-9) -> float:
    spacings = [right - left for left, right in zip(event_times, event_times[1:])
                if right > left]
    if not spacings:
        return minimum_s
    return min(maximum_s, max(minimum_s, fraction * median(spacings)))


def bit_code(row: Row, bits_lsb_first: list[str], threshold: float = 0.45) -> int:
    return sum(1 << index for index, signal in enumerate(bits_lsb_first)
               if float(row[signal]) > threshold)


def transformed_rows(rows: list[Row], *, scale: float = 1.37,
                     shift_s: float = 2e-9) -> list[Row]:
    """Return a timing metamorph used only by checker regression tests."""

    return [
        {
            **row,
            "time": scale * float(row["time"]) + shift_s,
            "_time_scale": scale * float(row.get("_time_scale", 1.0)),
            "_time_shift_s": (
                scale * float(row.get("_time_shift_s", 0.0)) + shift_s
            ),
        }
        for row in rows
    ]


def canonical_time_rows(rows: list[Row]) -> list[Row]:
    """Undo an explicitly annotated affine trace-coordinate transform."""

    if not rows:
        return rows
    scale = float(rows[0].get("_time_scale", 1.0))
    shift_s = float(rows[0].get("_time_shift_s", 0.0))
    if scale == 1.0 and shift_s == 0.0:
        return rows
    if scale <= 0.0:
        raise ValueError("trace time scale must be positive")
    return [
        {
            **row,
            "time": (float(row["time"]) - shift_s) / scale,
            "_time_scale": 1.0,
            "_time_shift_s": 0.0,
        }
        for row in rows
    ]
