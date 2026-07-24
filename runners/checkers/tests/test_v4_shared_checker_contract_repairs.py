from __future__ import annotations

import math

from runners.checkers.v4.task_001 import CHECKER as CHECK_BBPD
from runners.checkers.v4.task_004 import CHECKER as CHECK_TRIM_CONTROLLER
from runners.checkers.v4.task_006 import CHECKER as CHECK_ELEMENT_SHUFFLER
from runners.checkers.v4.task_009 import CHECKER as CHECK_LOCK_DETECTOR
from runners.checkers.v4.task_064 import CHECKER as CHECK_EDGE_DELAY
from runners.checkers.v4.task_091 import CHECKER as CHECK_CHOPPER_AMPLIFIER
from runners.checkers.v4.task_219 import CHECKER as CHECK_BIN2THER
from runners.checkers.v4.task_235 import CHECKER as CHECK_PFD
from runners.checkers.v4.task_299 import CHECKER as CHECK_SINE_VCO


def _bbpd_rows(*, add_isolated_overlap: bool = False) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for index in range(101):
        time_ns = 0.1 * index
        data = 0.0 if time_ns < 1.0 else 0.9
        if 2.0 <= time_ns < 3.0:
            data = 0.0
        clk = 0.0
        if 0.8 <= time_ns < 1.4 or 2.4 <= time_ns:
            clk = 0.9
        retimed_data = 0.9 if 1.8 <= time_ns else 0.0
        up = 0.9 if 1.0 <= time_ns <= 1.2 else 0.0
        down = 0.9 if 2.0 <= time_ns <= 2.2 else 0.0
        if add_isolated_overlap and abs(time_ns - 8.0) < 1e-12:
            up = down = 0.9
        rows.append(
            {
                "time": time_ns * 1e-9,
                "data": data,
                "clk": clk,
                "retimed_data": retimed_data,
                "up": up,
                "down": down,
            }
        )
    return rows


def test_task001_rejects_any_observed_up_down_overlap() -> None:
    passed, note = CHECK_BBPD(_bbpd_rows())
    assert passed, note

    passed, note = CHECK_BBPD(_bbpd_rows(add_isolated_overlap=True))
    assert not passed, note
    assert "overlap" in note


def _trim_controller_rows() -> list[dict[str, float]]:
    first_edge_ns = 0.1
    edge_times_ns = [first_edge_ns + 5.0 * index for index in range(22)]
    target_by_edge: list[float] = []
    target = 0.45
    for index in range(len(edge_times_ns)):
        if index == 0:
            target = 0.45
        elif index <= 7:
            target = min(0.85, target + 0.06)
        else:
            target = max(0.05, target - 0.06)
        target_by_edge.append(target)

    rows: list[dict[str, float]] = []
    stop_index = int((edge_times_ns[-1] + 4.0) * 10)
    for sample_index in range(stop_index + 1):
        time_ns = 0.1 * sample_index
        completed = [i for i, edge in enumerate(edge_times_ns) if edge <= time_ns]
        last_edge_index = completed[-1] if completed else None
        trim = 0.45 if last_edge_index is None else target_by_edge[last_edge_index]
        clk = 0.9 if any(edge <= time_ns < edge + 0.5 for edge in edge_times_ns) else 0.0
        rst = 0.9 if first_edge_ns <= time_ns < first_edge_ns + 0.2 else 0.0
        err = 0.9 if first_edge_ns + 5.0 <= time_ns < first_edge_ns + 40.0 else 0.0
        rows.append({"time": time_ns * 1e-9, "clk": clk, "rst": rst, "err": err, "trim": trim})
    return rows


def test_task004_accepts_initial_state_observed_immediately_before_first_clock() -> None:
    passed, note = CHECK_TRIM_CONTROLLER(_trim_controller_rows())
    assert passed, note


def _element_shuffler_rows(*, reassert_reset: bool) -> list[dict[str, float]]:
    clock_edges_ns = [5.0, 10.0, 15.0, 20.0]
    if reassert_reset:
        clock_edges_ns += [27.0, 32.0, 37.0, 42.0]
    events: list[tuple[float, str]] = [(edge, "clock") for edge in clock_edges_ns]
    if reassert_reset:
        events.append((22.0, "reset"))
    events.sort()

    rows: list[dict[str, float]] = []
    stop_ns = 46.0 if reassert_reset else 24.0
    for sample_index in range(int(stop_ns * 10) + 1):
        time_ns = 0.1 * sample_index
        rst_n = 0.0 if time_ns < 2.0 else 0.9
        if reassert_reset and 22.0 <= time_ns < 24.0:
            rst_n = 0.0
        clk = 0.9 if any(edge <= time_ns < edge + 0.5 for edge in clock_edges_ns) else 0.0
        state = 0
        for event_time, kind in events:
            if event_time > time_ns:
                break
            if kind == "reset":
                state = 0
            elif not (reassert_reset and 22.0 <= event_time < 24.0):
                state = (state + 1) % 4
        active_index = (1, 2, 0, 3)[state]
        row = {"time": time_ns * 1e-9, "clk": clk, "rst_n": rst_n}
        row.update({f"out{index}": 0.9 if index == active_index else 0.0 for index in range(4)})
        rows.append(row)
    return rows


def test_task006_requires_reset_to_clear_an_already_advanced_state() -> None:
    passed, note = CHECK_ELEMENT_SHUFFLER(_element_shuffler_rows(reassert_reset=False))
    assert not passed, note

    passed, note = CHECK_ELEMENT_SHUFFLER(_element_shuffler_rows(reassert_reset=True))
    assert passed, note


def _lock_detector_rows(*, post_reset_alignment_count: int) -> list[dict[str, float]]:
    pre_ref_edges = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    post_ref_edges = [80.0, 90.0, 100.0][:post_reset_alignment_count]
    ref_edges = pre_ref_edges + post_ref_edges
    fb_edges = [9.5, 19.5, 29.5, 35.0, 49.5, 59.5]
    fb_edges += [edge - 0.5 for edge in post_ref_edges]
    first_post_lock_ns = post_ref_edges[-1] + 0.4

    rows: list[dict[str, float]] = []
    stop_ns = post_ref_edges[-1] + 4.0
    for sample_index in range(int(stop_ns * 10) + 1):
        time_ns = 0.1 * sample_index
        ref_clk = 0.9 if any(edge <= time_ns < edge + 1.0 for edge in ref_edges) else 0.0
        fb_clk = 0.9 if any(edge <= time_ns < edge + 1.0 for edge in fb_edges) else 0.0
        rst_n = 0.0 if 65.0 <= time_ns < 70.0 else 0.9
        lock = 0.9 if 30.4 <= time_ns < 35.0 or time_ns >= first_post_lock_ns else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "ref_clk": ref_clk,
                "fb_clk": fb_clk,
                "rst_n": rst_n,
                "lock": lock,
            }
        )
    return rows


def test_task009_does_not_carry_alignment_streak_across_reset_epochs() -> None:
    passed, note = CHECK_LOCK_DETECTOR(_lock_detector_rows(post_reset_alignment_count=1))
    assert not passed, note

    passed, note = CHECK_LOCK_DETECTOR(_lock_detector_rows(post_reset_alignment_count=3))
    assert passed, note


def _edge_delay_rows(
    *,
    disabled_flags_stuck_high: bool = False,
    extra_valid_pulse: bool = False,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for sample_index in range(int(15.0 / 0.05) + 1):
        time_ns = 0.05 * sample_index
        rst = 0.9 if time_ns < 0.5 else 0.0
        enable = 0.9 if 1.0 <= time_ns < 12.0 or time_ns >= 14.0 else 0.0
        vin = 0.0
        if 2.0 <= time_ns < 6.0 or 10.0 <= time_ns < 10.5:
            vin = 0.9
        vout = 0.9 if 3.75 <= time_ns < 7.75 else 0.0
        edge_valid = 0.9 if 3.75 <= time_ns < 4.0 or 7.75 <= time_ns < 8.0 else 0.0
        rejected = 0.9 if 10.5 <= time_ns < 10.75 else 0.0
        if extra_valid_pulse and 9.0 <= time_ns < 9.25:
            edge_valid = 0.9
        if disabled_flags_stuck_high and 12.0 <= time_ns < 14.0:
            edge_valid = rejected = 0.9
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vin": vin,
                "rst": rst,
                "enable": enable,
                "vout": vout,
                "edge_valid": edge_valid,
                "rejected": rejected,
            }
        )
    return rows


def test_task064_disable_clears_all_outputs_and_valid_has_no_extra_pulse() -> None:
    passed, note = CHECK_EDGE_DELAY(_edge_delay_rows())
    assert passed, note

    passed, note = CHECK_EDGE_DELAY(_edge_delay_rows(disabled_flags_stuck_high=True))
    assert not passed, note

    passed, note = CHECK_EDGE_DELAY(_edge_delay_rows(extra_valid_pulse=True))
    assert not passed, note


def _sparse_chopper_rows() -> list[dict[str, float]]:
    times_ns = [0.0]
    for edge_ns in range(1, 16, 2):
        times_ns.extend([float(edge_ns), float(edge_ns + 1)])
    times_ns.append(17.0)

    baseband = 0.0
    residual = 0.0
    converged = 0
    settled = 0.0
    chop_high = False
    rows: list[dict[str, float]] = []
    for time_ns in times_ns:
        is_edge = int(time_ns) % 2 == 1 and time_ns <= 15.0
        if is_edge:
            chop_high = not chop_high
        rst = 0.9 if time_ns == 0.0 else 0.0
        hold = 0.9 if 6.0 <= time_ns < 8.0 else 0.0
        enable = 0.0 if 11.0 <= time_ns < 12.0 else 0.9
        if is_edge:
            if rst > 0.45 or enable <= 0.45:
                baseband = 0.0
                residual = 0.0
                converged = 0
                settled = 0.0
            elif hold <= 0.45:
                polarity = 1 if chop_high else -1
                demodulated = polarity * 3.0 * 0.020
                baseband += 0.25 * (demodulated - baseband)
                residual = baseband
                converged = converged + 1 if abs(residual) <= 0.020 else 0
                settled = 0.9 if converged >= 3 else 0.0
        rows.append(
            {
                "time": time_ns * 1e-9,
                "vinp": 0.0,
                "vinn": 0.0,
                "chop_clk": 0.9 if chop_high else 0.0,
                "rst": rst,
                "enable": enable,
                "hold": hold,
                "voutp": 0.45 + 0.5 * baseband,
                "voutn": 0.45 - 0.5 * baseband,
                "settled": settled,
                "offset_residual": residual,
            }
        )
    return rows


def test_task091_accepts_sparse_event_complete_waveforms() -> None:
    rows = _sparse_chopper_rows()
    assert len(rows) < 20
    passed, note = CHECK_CHOPPER_AMPLIFIER(rows)
    assert passed, note


def _bin2ther_four_state_rows() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for state_index, (b1_high, b0_high) in enumerate(
        ((False, False), (False, True), (True, False), (True, True))
    ):
        for offset_ns in (0.0, 0.2):
            time_ns = float(state_index) + offset_ns
            b1 = 0.9 if b1_high else 0.55
            b0 = 0.9 if b0_high else 0.55
            rows.append(
                {
                    "time": time_ns * 1e-9,
                    "vdd": 1.2,
                    "gnd": 0.2,
                    "b1": b1,
                    "b0": b0,
                    "t0": 1.2 if b1_high else 0.2,
                    "t1": 1.2 if b1_high else 0.2,
                    "t2": 1.2 if b0_high else 0.2,
                }
            )
    return rows


def test_task219_accepts_one_stable_observation_per_logic_combination() -> None:
    passed, note = CHECK_BIN2THER(_bin2ther_four_state_rows())
    assert passed, note


def _sparse_pfd_rows() -> list[dict[str, float]]:
    samples = [
        (0.0, 0.0, 0.0, 0.9, 0.0),
        (1.0, 0.0, 0.0, 0.9, 0.0),
        (1.0, 0.9, 0.0, 0.0, 0.0),
        (1.5, 0.0, 0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0, 0.0, 0.0),
        (2.0, 0.0, 0.9, 0.0, 0.9),
        (2.05, 0.0, 0.9, 0.0, 0.9),
        (2.10, 0.0, 0.9, 0.9, 0.0),
        (2.5, 0.0, 0.0, 0.9, 0.0),
        (4.0, 0.0, 0.0, 0.9, 0.0),
        (4.0, 0.0, 0.9, 0.9, 0.9),
        (4.5, 0.0, 0.0, 0.9, 0.9),
        (5.0, 0.0, 0.0, 0.9, 0.9),
        (5.0, 0.9, 0.0, 0.0, 0.9),
        (5.05, 0.9, 0.0, 0.0, 0.9),
        (5.10, 0.9, 0.0, 0.9, 0.0),
        (5.5, 0.0, 0.0, 0.9, 0.0),
        (6.0, 0.0, 0.0, 0.9, 0.0),
    ]
    return [
        {"time": time_ns * 1e-9, "a": a, "b": b, "ub": ub, "d": d}
        for time_ns, a, b, ub, d in samples
    ]


def test_task235_accepts_sparse_trace_covering_each_pfd_state() -> None:
    rows = _sparse_pfd_rows()
    assert len(rows) < 20
    passed, note = CHECK_PFD(rows)
    assert passed, note


def _sine_vco_rows() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    total_cycles = 0.0
    previous_vin = 0.20
    previous_time = 0.0
    for index in range(101):
        time_s = index * 1.0e-9
        vin = 0.20 if index < 50 else 0.25
        if index:
            previous_freq = 20.0e6 + 40.0e6 * previous_vin
            current_freq = 20.0e6 + 40.0e6 * vin
            total_cycles += 0.5 * (previous_freq + current_freq) * (time_s - previous_time)
        phase = total_cycles % 1.0
        rows.append(
            {
                "time": time_s,
                "vin": vin,
                "out": 0.9 * math.sin(2.0 * math.pi * phase),
                "metric": 0.9 * phase,
            }
        )
        previous_vin = vin
        previous_time = time_s
    return rows


def test_task299_accepts_two_distinct_input_regions_without_hidden_amplitude() -> None:
    passed, note = CHECK_SINE_VCO(_sine_vco_rows())
    assert passed, note
