"""Independent waveform oracle for canonical v4 family 091."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from ..api import Checker


VDD = 0.9
VSS = 0.0
VCM = 0.45
VTH = 0.45
GAIN = 3.0
VOS_AMP = 0.020
LP_ALPHA = 0.25
SETTLE_TOL = 0.020
SETTLE_CYCLES = 3


def _sample(rows: list[dict[str, float]], signal: str, time_s: float) -> float:
    for left, right in zip(rows, rows[1:]):
        if left["time"] <= time_s <= right["time"]:
            span = right["time"] - left["time"]
            if span == 0.0:
                return right[signal]
            alpha = (time_s - left["time"]) / span
            return left[signal] + alpha * (right[signal] - left[signal])
    return rows[-1][signal]


def _crossings(rows: list[dict[str, float]], signal: str, direction: int) -> list[float]:
    result: list[float] = []
    for left, right in zip(rows, rows[1:]):
        v0, v1 = left[signal], right[signal]
        hit = v0 <= VTH < v1 if direction > 0 else v0 >= VTH > v1
        if hit:
            fraction = (VTH - v0) / (v1 - v0) if v1 != v0 else 1.0
            result.append(left["time"] + fraction * (right["time"] - left["time"]))
    return result


@dataclass
class _State:
    baseband: float = 0.0
    residual: float = 0.0
    settled: float = VSS
    converged: int = 0

    def clear(self) -> None:
        self.baseband = 0.0
        self.residual = 0.0
        self.settled = VSS
        self.converged = 0

    def update(self, input_diff: float, polarity: int) -> None:
        chopped = polarity * input_diff
        amplified = GAIN * (chopped + VOS_AMP)
        demodulated = polarity * amplified
        self.baseband += LP_ALPHA * (demodulated - self.baseband)
        self.residual = self.baseband - GAIN * input_diff
        self.converged = self.converged + 1 if abs(self.residual) <= SETTLE_TOL else 0
        self.settled = VDD if self.converged >= SETTLE_CYCLES else VSS

    def outputs(self) -> dict[str, float]:
        return {
            "voutp": min(VDD, max(VSS, VCM + 0.5 * self.baseband)),
            "voutn": min(VDD, max(VSS, VCM - 0.5 * self.baseband)),
            "settled": self.settled,
            "offset_residual": self.residual,
        }


def check_chopper_stabilized_differential_amplifier(
    rows: list[dict[str, float]],
) -> tuple[bool, str]:
    required = {
        "time", "vinp", "vinn", "chop_clk", "rst", "enable", "hold",
        "voutp", "voutn", "settled", "offset_residual",
    }
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - (set(rows[0]) if rows else set()))
        return False, "missing_columns=" + ",".join(missing)
    chop_rising = _crossings(rows, "chop_clk", +1)
    chop_periods = [right - left for left, right in zip(chop_rising, chop_rising[1:])]
    if not chop_periods:
        return False, "insufficient_excitation chop_periods"
    events: list[tuple[float, int, str, int]] = []
    events += [(time_s, 1, "chop", +1) for time_s in chop_rising]
    events += [(time_s, 1, "chop", -1) for time_s in _crossings(rows, "chop_clk", -1)]
    events += [(time_s, 0, "clear", 0) for time_s in _crossings(rows, "rst", +1)]
    events += [(time_s, 0, "clear", 0) for time_s in _crossings(rows, "enable", -1)]
    events.sort()

    state = _State()
    sample_steps = [
        right["time"] - left["time"]
        for left, right in zip(rows, rows[1:])
        if right["time"] > left["time"]
    ]
    nominal_sample_step = median(sample_steps) if sample_steps else 0.0
    observed_events = active_updates = hold_edges = clear_events = 0
    positive_updates = negative_updates = settled_events = 0
    errors: list[str] = []

    for index, (event_time, _priority, kind, polarity) in enumerate(events):
        # The DUT samples every state-driving input at the reconstructed
        # chopper event.  A solver-dependent post-edge row is suitable for
        # observing settled outputs, but not for replaying the state update.
        rst = _sample(rows, "rst", event_time)
        enable = _sample(rows, "enable", event_time)
        hold = _sample(rows, "hold", event_time)
        if kind == "clear" or rst > VTH or enable <= VTH:
            state.clear()
            clear_events += 1
        elif hold > VTH:
            hold_edges += 1
        else:
            input_diff = _sample(rows, "vinp", event_time) - _sample(rows, "vinn", event_time)
            state.update(input_diff, polarity)
            active_updates += 1
            positive_updates += polarity > 0
            negative_updates += polarity < 0

        next_time = next(
            (later[0] for later in events[index + 1:] if later[0] > event_time),
            rows[-1]["time"],
        )
        if next_time <= event_time:
            continue
        if next_time - event_time <= 0.55 * nominal_sample_step:
            # Two state-changing events inside one observation interval cannot
            # expose the intermediate state without inventing waveform data.
            continue
        probe = event_time + 0.5 * (next_time - event_time)
        observed_events += 1
        for signal, expected in state.outputs().items():
            observed = _sample(rows, signal, probe)
            tolerance = 0.015 if signal != "settled" else 0.08
            if abs(observed - expected) > tolerance:
                errors.append(
                    f"{signal}@{probe * 1e9:.3f}ns={observed:.5f} expected={expected:.5f}"
                )
                if len(errors) >= 5:
                    break
        settled_events += _sample(rows, "settled", probe) > VTH
        if len(errors) >= 5:
            break

    coverage_ok = (
        active_updates >= SETTLE_CYCLES
        and hold_edges >= 1
        and clear_events >= 1
        and positive_updates >= 1
        and negative_updates >= 1
        and settled_events >= 1
        and observed_events >= 1
    )
    ok = not errors and coverage_ok
    note = (
        f"observed_events={observed_events} active={active_updates} hold_edges={hold_edges} "
        f"clears={clear_events} polarity=+{positive_updates}/-{negative_updates} "
        f"settled_events={settled_events} "
        f"errors={len(errors)}"
    )
    if errors:
        note += " first=" + errors[0]
    elif not coverage_ok:
        note = "insufficient_excitation " + note
    return ok, note


CHECKER_ID = "v4_091_chopper_stabilized_differential_amplifier"
CHECKER: Checker = check_chopper_stabilized_differential_amplifier
