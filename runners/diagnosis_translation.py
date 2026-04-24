#!/usr/bin/env python3
"""
Diagnosis translation for EVAS repair prompts.

P0 goals implemented here:
1. Replace fragile broad substring matching with structured, prioritized matching.
2. Preserve model-agnostic behavior: all routing is based on EVAS diagnostics only.
3. Emit typed diagnosis metadata for downstream prompt routing.
"""
from __future__ import annotations

import re
from typing import Optional

_KV_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_BOOKKEEPING_KEYS = {"generated_include", "returncode"}


def _parse_metrics(note: str) -> dict[str, str]:
    return {k: v for k, v in _KV_RE.findall(note)}


def _behavior_metrics(metrics: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in metrics.items() if k not in _BOOKKEEPING_KEYS}


def _has_key(note: str, key: str) -> bool:
    return re.search(rf"\b{re.escape(key)}=", note) is not None


def _returncode_is_nonzero(metrics: dict[str, str]) -> bool:
    raw = metrics.get("returncode")
    if raw is None:
        return False
    try:
        return int(float(raw)) != 0
    except ValueError:
        return False


def _route_failure_type(note: str, metrics: dict[str, str]) -> str:
    lowered = note.lower()
    if (
        "tran.csv missing" in lowered
        or "evas_timeout" in lowered
        or "tb_not_executed" in lowered
        or _returncode_is_nonzero(metrics)
    ):
        return "simulation_artifact"
    if (
        "normalized_tb_save_tokens" in lowered
        or lowered.startswith("missing ")
        or "missing_" in lowered
        or "no vdac activity" in lowered
        or "missing clk_in/clk_out" in lowered
        or "insufficient_window_samples" in lowered
        or "insufficient_post_reset_samples" in lowered
    ):
        return "observability_contract"
    return "behavior_semantic"


def translate_diagnosis(note: str, task_id: Optional[str] = None) -> dict:
    """Translate one EVAS note into structured, actionable repair guidance."""
    metrics = _parse_metrics(note)
    failure_type = _route_failure_type(note, metrics)
    lowered = note.lower()

    result = {
        "diagnosis": "",
        "causes": [],
        "repair_suggestions": [],
        "example_fix": "",
        "circuit_specific": "",
        "failure_type": failure_type,
        "matched_rule": "",
        "matched_keys": [],
    }

    # Priority 1: infra/simulation artifacts.
    if failure_type == "simulation_artifact":
        result.update(
            {
                "diagnosis": "Simulation artifact failure (output waveform unavailable or invalid)",
                "matched_rule": "SIM_ARTIFACT",
                "causes": [
                    "Transient CSV not produced or simulation timed out",
                    "Netlist execution failed before behavior checker stage",
                ],
                "repair_suggestions": [
                    "Keep one valid top-level tran setup and avoid tiny maxstep values",
                    "Ensure DUT/TB include paths and required files are complete",
                    "Fix compile/runtime errors before semantic tuning",
                ],
            }
        )
        result["matched_keys"] = sorted(metrics.keys())
    # Priority 2: observability / contract failures.
    elif failure_type == "observability_contract":
        if (
            "insufficient_post_reset_samples" in lowered
            or any(_has_key(note, key) for key in ("too_few_clock_edges", "too_few_edges", "no_clock_edges"))
        ):
            result.update(
                {
                    "diagnosis": "Expected post-reset clock/sample edges are missing",
                    "matched_rule": "POST_RESET_SAMPLE_BUDGET",
                    "causes": [
                        "Reset may deassert too late relative to transient stop time",
                        "Clock period or clock delay may leave too few sampled edges after reset",
                        "Stimulus changes may occur outside the checker sampling window",
                    ],
                    "repair_suggestions": [
                        "Repair the testbench timing budget before changing DUT behavior",
                        "Ensure reset deasserts early and several rising clock edges occur before tran stop",
                        "If tran stop is fixed, shorten/move the clock/reset/stimulus schedule inside the existing window",
                    ],
                }
            )
        else:
            result.update(
                {
                    "diagnosis": "Observability or checker-contract mismatch",
                    "matched_rule": "OBSERVABILITY_CONTRACT",
                    "causes": [
                        "Saved waveform columns do not match checker-required names",
                        "Testbench save statement is incomplete or aliased incorrectly",
                    ],
                    "repair_suggestions": [
                        "Fix save statement names first; match checker-required lowercase signals exactly",
                        "Avoid colon-instance save syntax and keep one canonical save list",
                        "After observability is fixed, re-check behavioral metrics",
                    ],
                }
            )
        result["matched_keys"] = sorted(metrics.keys())
    # Priority 3: semantic behavioral failures (ordered rules).
    elif _has_key(note, "freq_ratio"):
        result.update(
            {
                "diagnosis": "PLL frequency tracking ratio is incorrect",
                "matched_rule": "PLL_FREQ_RATIO",
                "causes": [
                    "Divider ratio or DCO period update path is incorrect",
                    "Lock condition logic does not reflect actual frequency convergence",
                ],
                "repair_suggestions": [
                    "Align divider update and output edge generation with target ratio",
                    "Compute/observe frequency ratio in the same timing window as checker",
                    "Gate lock assertion on stable ratio conditions rather than static thresholds",
                ],
            }
        )
        result["matched_keys"] = ["freq_ratio"] + [k for k in ("lock_time", "fb_jitter_frac") if k in metrics]
    elif "ratio_hop_not_detected" in lowered:
        result.update(
            {
                "diagnosis": "PLL ratio-hop behavior not detected by checker",
                "matched_rule": "PLL_RATIO_HOP",
                "causes": [
                    "Hop event timing or ratio state transition is missing",
                    "Reference/hop phase windows do not produce expected edge counts",
                ],
                "repair_suggestions": [
                    "Implement explicit pre-hop and post-hop ratio states",
                    "Ensure hop trigger occurs in checker-visible simulation window",
                    "Keep edge counters/lock indicators coherent through the hop",
                ],
            }
        )
    elif _has_key(note, "relock_time"):
        result.update(
            {
                "diagnosis": "PLL relock time is outside expected range",
                "matched_rule": "PLL_RELOCK_TIME",
                "causes": [
                    "Loop dynamics are too slow after disturbance",
                    "Charge-pump / control update is too weak or delayed",
                ],
                "repair_suggestions": [
                    "Increase effective loop responsiveness after phase/frequency error",
                    "Verify relock detection is based on stable post-disturbance behavior",
                ],
            }
        )
        result["matched_keys"] = ["relock_time"]
    elif task_id and "flash_adc" in task_id.lower() and re.search(r"\bonly_\d+_codes\b", lowered):
        result.update(
            {
                "diagnosis": "Flash ADC code coverage is insufficient",
                "matched_rule": "FLASH_ADC_CODE_COVERAGE",
                "causes": [
                    "Quantizer code may be stuck or not updated on clock edges",
                    "Threshold ladder may not cover all 8 bins over the ramp",
                    "Output bit targets may not be initialized or driven from the code state",
                ],
                "repair_suggestions": [
                    "Implement seven ordered thresholds across the reference range",
                    "Update one integer code state on each rising clock edge",
                    "Drive dout2/dout1/dout0 from that code with MSB-to-LSB order",
                    "Use Verilog-A `floor(...)` rather than `$floor(...)` when computing integer codes",
                ],
            }
        )
        result["matched_keys"] = ["only_N_codes"]
    elif _has_key(note, "unique_codes") or re.search(r"\bonly_\d+_codes\b", lowered):
        result.update(
            {
                "diagnosis": "ADC/DAC code coverage is insufficient",
                "matched_rule": "ADC_DAC_CODE_COVERAGE",
                "causes": [
                    "Quantization thresholds or code mapping collapse to a narrow range",
                    "Output update logic is stuck or clipped",
                ],
                "repair_suggestions": [
                    "Rebuild code mapping from vin range to full-scale code range",
                    "Clamp only at boundaries; keep linear region monotonic",
                    "Verify each bit/output branch uses distinct threshold logic",
                ],
            }
        )
        result["matched_keys"] = ["unique_codes"] + [k for k in ("vout_span", "vin_span") if k in metrics]
        if re.search(r"\bonly_\d+_codes\b", lowered):
            result["matched_keys"].append("only_N_codes")
    elif _has_key(note, "late_edge_ratio"):
        result.update(
            {
                "diagnosis": "ADPLL late-window edge ratio is incorrect",
                "matched_rule": "ADPLL_EDGE_RATIO",
                "causes": [
                    "Feedback/output edge cadence does not match the expected locked ratio",
                    "Lock is asserted without the measured edge ratio converging",
                ],
                "repair_suggestions": [
                    "Tie lock behavior to measured edge cadence rather than a static delay",
                    "Update divider/DCO timing so late-window edge counts match the target ratio",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("late_edge_ratio", "lock_time", "vctrl_range_ok") if k in metrics]
    elif _has_key(note, "lead_window_updn"):
        result.update(
            {
                "diagnosis": "BBPD/PFD data-edge alignment window is incorrect",
                "matched_rule": "BBPD_EDGE_ALIGNMENT",
                "causes": [
                    "UP/DN pulse decision is not aligned to the intended data-edge window",
                    "Pulse generation may be level-sensitive instead of edge-window-sensitive",
                ],
                "repair_suggestions": [
                    "Generate UP/DN pulses from edge ordering in the checker-visible window",
                    "Keep pulse width finite and reset both outputs between comparisons",
                ],
            }
        )
        result["matched_keys"] = ["lead_window_updn"]
    elif _has_key(note, "code_span") or _has_key(note, "settled_high"):
        result.update(
            {
                "diagnosis": "Calibration/code range behavior is not reaching the required span",
                "matched_rule": "CAL_CODE_SPAN",
                "causes": [
                    "Calibration state machine is stuck or stops before covering the code range",
                    "Settling flag/output does not reflect the final calibrated state",
                ],
                "repair_suggestions": [
                    "Make the calibration code update monotonically through the required range",
                    "Assert settled only after the final code/range condition is reached",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("code_span", "settled_high") if k in metrics]
    elif _has_key(note, "clk_out_hi_frac") or _has_key(note, "rising_edges"):
        result.update(
            {
                "diagnosis": "Clock burst output duty/edge count is incorrect",
                "matched_rule": "CLOCK_BURST",
                "causes": [
                    "Burst enable window or edge counter is too short",
                    "Output clock is not toggled for the expected number of cycles",
                ],
                "repair_suggestions": [
                    "Drive the output clock only inside the burst window but preserve full toggles",
                    "Use an explicit edge counter/state machine for burst length",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("clk_out_hi_frac", "rising_edges") if k in metrics]
    elif _has_key(note, "ratio_code") or _has_key(note, "period_match") or _has_key(note, "interval_hist"):
        result.update(
            {
                "diagnosis": "Programmable clock divider ratio/period is incorrect",
                "matched_rule": "CLOCK_DIVIDER_RATIO",
                "causes": [
                    "Divider terminal count does not correspond to the programmed ratio",
                    "Lock/period output is asserted without matching the measured interval",
                ],
                "repair_suggestions": [
                    "Decode ratio_code into an explicit terminal count and toggle only on terminal count",
                    "Keep lock/high indicators consistent with the period observed in clk_out",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("ratio_code", "in_edges", "out_edges", "period_match", "interval_hist") if k in metrics]
    elif "insufficient_toggle" in lowered:
        result.update(
            {
                "diagnosis": "Comparator output does not toggle over the stimulus range",
                "matched_rule": "COMPARATOR_TOGGLE",
                "causes": [
                    "Differential decision threshold or output polarity is wrong",
                    "Outputs may be stuck because the input comparison is not connected to state update",
                ],
                "repair_suggestions": [
                    "Drive complementary outputs from the sign of the input difference",
                    "Ensure both high and low decisions are reachable in the test window",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("out_p_span", "out_n_span") if k in metrics]
    elif _has_key(note, "seen_out_never_high"):
        result.update(
            {
                "diagnosis": "Crossing/interval output never asserts in the expected window",
                "matched_rule": "CROSS_INTERVAL_ASSERT",
                "causes": [
                    "Event threshold or interval comparison is not reached",
                    "Output pulse may be too narrow or outside the checker sampling window",
                ],
                "repair_suggestions": [
                    "Use cross-triggered state updates and hold the output long enough to observe",
                    "Align threshold/time interval constants with the prompt specification",
                ],
            }
        )
        result["matched_keys"] = ["seen_out_never_high"]
    elif _has_key(note, "levels") or _has_key(note, "aout_span"):
        result.update(
            {
                "diagnosis": "DAC output level coverage is insufficient",
                "matched_rule": "DAC_LEVEL_COVERAGE",
                "causes": [
                    "Digital input decoding collapses multiple codes to one analog level",
                    "Output update is not clocked or not connected to the stimulus code",
                ],
                "repair_suggestions": [
                    "Decode every input bit with binary/thermometer weights as specified",
                    "Update the analog output after the intended clock/sample event",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("levels", "aout_span") if k in metrics]
    elif _has_key(note, "max_ones") or _has_key(note, "max_vout"):
        result.update(
            {
                "diagnosis": "Thermometer DAC count-to-voltage behavior is incorrect",
                "matched_rule": "THERM_DAC_COUNT",
                "causes": [
                    "Input ones count or reset handling does not match the expected checkpoints",
                    "Voltage scaling may not be held stable at checker sampling times",
                ],
                "repair_suggestions": [
                    "Count all 16 thermometer inputs explicitly and multiply by vstep",
                    "Give transition outputs enough settling time before checkpoint samples",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("max_ones", "max_vout") if k in metrics]
    elif any(_has_key(note, k) for k in ("q_mismatch", "qb_mismatch")):
        result.update(
            {
                "diagnosis": "DFF reset/Q-QB behavior is inconsistent with expected samples",
                "matched_rule": "DFF_RESET_COMPLEMENT",
                "causes": [
                    "Reset priority or clocked sampling order is wrong",
                    "QB is not maintained as the complement of Q",
                ],
                "repair_suggestions": [
                    "Give reset highest priority and sample D only on the intended clock edge",
                    "Drive QB from the same state variable as Q with opposite polarity",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("checks", "q_mismatch", "qb_mismatch") if k in metrics]
    elif task_id and "flash_adc" in task_id.lower() and _has_key(note, "too_few_edges"):
        result.update(
            {
                "diagnosis": "Flash ADC checker cannot observe enough clocked conversion samples",
                "matched_rule": "FLASH_ADC_EDGE_BUDGET",
                "causes": [
                    "Clock source may not create checker-visible rising crossings",
                    "Clock period or transient window may not provide at least 20 sampled conversions",
                    "Input sweep may not be aligned with the sampled clock window",
                ],
                "repair_suggestions": [
                    "Repair the testbench clock/stimulus budget before changing quantizer thresholds",
                    "Use a pulse clock with enough rising edges inside the fixed tran stop",
                    "Sweep vin across the full reference range during those clocked samples",
                ],
            }
        )
        result["matched_keys"] = ["too_few_edges"]
    elif any(
        _has_key(note, key)
        for key in ("too_few_edges", "too_few_clock_edges", "insufficient_post_reset_samples", "no_clock_edges")
    ):
        result.update(
            {
                "diagnosis": "Expected post-reset clock/sample edges are missing",
                "matched_rule": "POST_RESET_SAMPLE_BUDGET",
                "causes": [
                    "Reset may deassert too late relative to transient stop time",
                    "Clock period or clock delay may leave too few sampled edges after reset",
                    "Stimulus changes may occur outside the checker sampling window",
                ],
                "repair_suggestions": [
                    "Repair the testbench timing budget before changing DUT behavior",
                    "Ensure reset deasserts early and several rising clock edges occur before tran stop",
                    "If tran stop is fixed, shorten/move the clock/reset/stimulus schedule inside the existing window",
                ],
            }
        )
        result["matched_keys"] = [
            key
            for key in ("too_few_edges", "too_few_clock_edges", "insufficient_post_reset_samples", "no_clock_edges")
            if _has_key(note, key)
        ]
    elif any(_has_key(note, k) for k in ("transitions", "complement_err", "swing")):
        result.update(
            {
                "diagnosis": "NRZ/PRBS waveform transition behavior is incorrect",
                "matched_rule": "NRZ_PRBS_TRANSITIONS",
                "causes": [
                    "PRBS state may be stuck or not clocked",
                    "Complement/output swing is present but data transitions are absent",
                ],
                "repair_suggestions": [
                    "Advance the LFSR/PRBS state on every intended clock edge",
                    "Drive NRZ output from the generated bit state with full voltage swing",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("transitions", "complement_err", "swing") if k in metrics]
    elif any(_has_key(note, k) for k in ("up_first", "dn_first", "up_second", "dn_second", "overlap_frac")):
        result.update(
            {
                "diagnosis": "PFD reset-race pulse ordering/window behavior is incorrect",
                "matched_rule": "PFD_RESET_RACE",
                "causes": [
                    "UP/DN pulses are not reset and sequenced according to input edge order",
                    "Pulse windows leak into the wrong comparison interval",
                ],
                "repair_suggestions": [
                    "Latch which input edge arrived first, emit only the corresponding pulse, then reset both",
                    "Keep UP/DN non-overlapping and window-local across the first and second intervals",
                    "If pulse counts are sufficient but window fractions are too high, shorten pulse width rather than adding pulses",
                ],
            }
        )
        result["matched_keys"] = [
            k
            for k in ("up_first", "dn_first", "up_second", "dn_second", "up_pulses_first", "dn_pulses_second", "overlap_frac")
            if k in metrics
        ]
    elif any(_has_key(note, k) for k in ("wraps", "clk_rises", "phase_span")):
        result.update(
            {
                "diagnosis": "Phase accumulator wrap/clock-rise behavior is incorrect",
                "matched_rule": "PHASE_ACCUM_WRAP",
                "causes": [
                    "Phase increment/wrap logic is not synchronized to clock crossings",
                    "Accumulator may wrap numerically but not produce checker-visible clock events",
                ],
                "repair_suggestions": [
                    "Update phase exactly once per clock edge and wrap modulo full scale",
                    "Expose output transitions tied to wrap events so clk_rises and phase_span agree",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("wraps", "clk_rises", "phase_span") if k in metrics]
    elif (
        (task_id and "no_overlap" in task_id.lower())
        or any(_has_key(note, k) for k in ("max_active_cells", "overlap_count"))
    ):
        result.update(
            {
                "diagnosis": "DWA no-overlap pointer/window behavior is incorrect",
                "matched_rule": "DWA_NO_OVERLAP_WINDOW",
                "causes": [
                    "Cell enable window is not driven from the decoded code and pointer state",
                    "Pointer output may be valid while cell-enable outputs remain inactive",
                    "Consecutive enabled cell sets may be reused instead of rotating to a disjoint set",
                ],
                "repair_suggestions": [
                    "Decode the 4-bit code on each valid clock edge using fixed bit reads",
                    "Build a fresh active-cell set from ptr_q and code_q on every sampled cycle",
                    "Drive exactly one pointer bit high and drive at least one cell_en bit high when code_q is nonzero",
                    "Advance ptr_q so the next enabled set does not overlap the previous active set",
                ],
            }
        )
        result["matched_keys"] = [
            k
            for k in ("sampled_cycles", "bad_ptr_rows", "max_active_cells", "overlap_count")
            if k in metrics
        ]
    elif any(_has_key(note, k) for k in ("bad_count_rows", "wrap_events", "split_wrap_rows")):
        result.update(
            {
                "diagnosis": "DWA wraparound pointer/count behavior is incorrect",
                "matched_rule": "DWA_WRAPAROUND_WINDOW",
                "causes": [
                    "Pointer update order does not match checker expectation from initial pointer 13",
                    "Pointer output is not one-hot at the expected post-update pointer",
                    "Active cell count does not equal decoded input code",
                    "Wraparound selections across cell 15 to cell 0 are missing or malformed",
                ],
                "repair_suggestions": [
                    "Initialize ptr_q to 13 and update expected pointer as `(ptr_q + code_q) % 16` on each rising clock",
                    "After updating ptr_q, make only `ptr_q` high in ptr outputs",
                    "Enable exactly `code_q` cells in the rotating window ending at or starting from the updated pointer",
                    "When the window crosses 15-to-0, split the enabled cells across both ends of the 16-cell array",
                ],
            }
        )
        result["matched_keys"] = [
            k
            for k in ("sampled_cycles", "bad_ptr_rows", "bad_count_rows", "wrap_events", "split_wrap_rows")
            if k in metrics
        ]
    elif any(_has_key(note, k) for k in ("droop_failures", "insufficient_high_hold_windows", "sample_mismatch")):
        result.update(
            {
                "diagnosis": "Sample-hold droop or aperture behavior is incorrect",
                "matched_rule": "SAMPLE_HOLD_DROOP",
                "causes": [
                    "Output may still track input during hold instead of holding sampled state",
                    "Droop may be too small, too large, or non-monotonic inside hold windows",
                    "Sample edge update may not settle to vin quickly enough after the aperture",
                ],
                "repair_suggestions": [
                    "Capture vin once on the intended sample edge into a held state variable",
                    "During hold, update vout only from the held state with a monotonic downward droop",
                    "Use timer-based droop updates and avoid re-sampling vin while clk is low",
                    "Tune droop magnitude so high hold windows show visible but bounded decay",
                ],
            }
        )
        result["matched_keys"] = [
            k
            for k in ("droop_failures", "windows", "insufficient_high_hold_windows", "sample_mismatch")
            if k in metrics
        ]
    elif _has_key(note, "max_err"):
        result.update(
            {
                "diagnosis": "Analog waveform approximation error is too large",
                "matched_rule": "ANALOG_MAX_ERR",
                "causes": [
                    "Generated waveform coefficients or phase/frequency terms are incorrect",
                    "Output scaling/offset does not match the specified signal model",
                ],
                "repair_suggestions": [
                    "Recompute the output expression directly from the specified sine/tone components",
                    "Check amplitude, offset, frequency, and phase units before tuning other logic",
                ],
            }
        )
        result["matched_keys"] = ["max_err"]
    elif any(_has_key(note, k) for k in ("base", "pre_count", "post_count")):
        result.update(
            {
                "diagnosis": "Multi-modulus divider pre/post switch counts are incorrect",
                "matched_rule": "MULTIMOD_DIVIDER_COUNTS",
                "causes": [
                    "Divider modulus is not switching at the requested time",
                    "Pre-switch and post-switch terminal counts are identical or off by one",
                ],
                "repair_suggestions": [
                    "Use separate pre-switch and post-switch modulus states",
                    "Reset or carry the divider counter deliberately at the switch boundary",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("base", "pre_count", "post_count", "switch_time_ns") if k in metrics]
    elif "bit_mismatch" in lowered:
        result.update(
            {
                "diagnosis": "Serializer bit order or sampling phase is incorrect",
                "matched_rule": "SERIALIZER_BIT_ORDER",
                "causes": [
                    "Serializer shifts in the opposite bit order from the expected frame",
                    "Load/shift timing is off by one bit period",
                ],
                "repair_suggestions": [
                    "Load the parallel word once per frame and shift in the specified MSB/LSB order",
                    "Align the first serial bit with the first checker sample after frame start",
                    "If the observed bits are shifted by one, latch on LOAD but output the MSB on the first post-LOAD CLK before shifting",
                ],
            }
        )
        result["matched_keys"] = ["bit_mismatch"]
    elif _has_key(note, "frame_rises"):
        result.update(
            {
                "diagnosis": "Serializer frame marker does not rise as expected",
                "matched_rule": "SERIALIZER_FRAME_ALIGNMENT",
                "causes": [
                    "Frame pulse is missing or not aligned to the serialized word boundary",
                    "Frame marker may be held low/high instead of pulsed once per frame",
                ],
                "repair_suggestions": [
                    "Generate a one-cycle frame pulse at the word boundary",
                    "Synchronize bit counter reset, word load, and frame marker timing",
                ],
            }
        )
        result["matched_keys"] = ["frame_rises"]
    elif "means=" in lowered:
        result.update(
            {
                "diagnosis": "Transition branch target levels are incorrect",
                "matched_rule": "TRANSITION_BRANCH_LEVELS",
                "causes": [
                    "Branch selection never reaches the intended target levels",
                    "Transition output is stuck at one level across all stimulus phases",
                ],
                "repair_suggestions": [
                    "Map each branch condition to a distinct target voltage",
                    "Hold each branch long enough for transition settling before the checker window",
                ],
            }
        )
        result["matched_keys"] = ["means"]
    elif "gray_property_violated" in lowered or _has_key(note, "bad_transitions"):
        result.update(
            {
                "diagnosis": "Gray-code one-bit transition property is violated",
                "matched_rule": "GRAY_PROPERTY",
                "causes": [
                    "State update does not follow Gray conversion rules",
                    "Multiple bits change in a single logical step",
                ],
                "repair_suggestions": [
                    "Derive Gray output from a consistent binary counter state",
                    "Update state once per valid edge and emit Gray-mapped output only",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("bad_transitions",) if k in metrics]
    elif any(_has_key(note, k) for k in ("sel0_err", "sel1_err", "sel2_err", "sel3_err")):
        result.update(
            {
                "diagnosis": "MUX selection-to-input mapping is incorrect",
                "matched_rule": "MUX_SELECTION",
                "causes": [
                    "Selection decoding order is wrong",
                    "One or more selection cases drive incorrect source input",
                ],
                "repair_suggestions": [
                    "Re-check the full truth table for each select code",
                    "Ensure each output branch references the intended input signal",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("sel0_err", "sel1_err", "sel2_err", "sel3_err") if k in metrics]
    elif "window_fracs" in lowered or _has_key(note, "rise_t_out_of_range") or _has_key(note, "fall_t_out_of_range"):
        result.update(
            {
                "diagnosis": "Hysteresis or transition-window behavior is incorrect",
                "matched_rule": "HYST_WINDOW",
                "causes": [
                    "Rising/falling thresholds or edge directions are inconsistent",
                    "Window hold behavior does not preserve prior state",
                ],
                "repair_suggestions": [
                    "Use two explicit thresholds with opposite cross directions",
                    "Hold previous state between thresholds and update only at crossings",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("rise_t_out_of_range", "fall_t_out_of_range") if k in metrics]
    elif any(_has_key(note, k) for k in ("pre_high_frac", "post_low_frac", "pre_low_frac", "post_high_frac", "mid_frac")):
        result.update(
            {
                "diagnosis": "Time-window output fraction target not met",
                "matched_rule": "WINDOW_FRAC",
                "causes": [
                    "Edge-triggered state updates do not align with checker windows",
                    "Reset/hold ordering causes output to stay in wrong level",
                ],
                "repair_suggestions": [
                    "Align state update edges with expected window boundaries",
                    "Verify reset priority and output hold behavior across phases",
                ],
            }
        )
        result["matched_keys"] = [k for k in ("pre_high_frac", "post_low_frac", "pre_low_frac", "post_high_frac", "mid_frac") if k in metrics]
    elif _behavior_metrics(metrics):
        result.update(
            {
                "diagnosis": "Behavioral metric mismatch detected",
                "matched_rule": "GENERIC_METRIC_MISMATCH",
                "causes": [
                    "Generated behavior diverges from checker constraints",
                    "Implementation does not satisfy measured metric targets",
                ],
                "repair_suggestions": [
                    "Prioritize fixing the largest-magnitude metric gaps first",
                    "Keep interface/testbench stable while adjusting DUT semantics",
                ],
                "matched_keys": sorted(_behavior_metrics(metrics).keys()),
            }
        )

    if task_id:
        result["circuit_specific"] = _circuit_specific_knowledge(note, task_id)
    return result


def _circuit_specific_knowledge(note: str, task_id: str) -> str:
    lowered_task = task_id.lower()
    lowered_note = note.lower()

    if any(k in lowered_task for k in ("pll", "adpll", "cppll", "pfd")) and (
        "freq_ratio" in lowered_note or "lock" in lowered_note or "vctrl" in lowered_note
    ):
        return (
            "## PLL Repair Focus\n"
            "- Keep divider ratio, DCO update, and lock criteria consistent in the same measurement window.\n"
            "- Avoid static lock assertions; derive lock from stable frequency/phase behavior."
        )
    if "hysteresis" in lowered_task and ("window" in lowered_note or "rise_t" in lowered_note or "fall_t" in lowered_note):
        return (
            "## Hysteresis Repair Focus\n"
            "- Use separate rising/falling thresholds and opposite edge directions.\n"
            "- Hold state between thresholds instead of recomputing combinationally each sample."
        )
    if "flash_adc" in lowered_task and ("unique_codes" in lowered_note or "vout_span" in lowered_note):
        return (
            "## Flash ADC Repair Focus\n"
            "- Ensure full threshold ladder coverage and monotonic code mapping.\n"
            "- Verify each output bit corresponds to the correct quantization boundary."
        )
    if "dwa" in lowered_task:
        return (
            "## DWA Repair Focus\n"
            "- Keep integer state for `ptr_q`, decoded `code_q`, and loop index `j`.\n"
            "- Use real arrays for `cell_en_val[0:15]` and `ptr_val[0:15]`, then drive bus outputs with module-scope `genvar` contributions.\n"
            "- Decode input code bits with fixed `V(code[0])`, `V(code[1])`, ... reads inside the clock event.\n"
            "- Clear all 16 output-state array entries before setting the new pointer and active-cell window."
        )
    return ""


def format_repair_section(translation: dict) -> str:
    lines = []
    if translation.get("failure_type"):
        lines.append(f"**Failure Type**: {translation['failure_type']}")
    if translation.get("matched_rule"):
        lines.append(f"**Rule**: {translation['matched_rule']}")
    if translation.get("matched_keys"):
        lines.append(f"**Matched Keys**: {', '.join(translation['matched_keys'])}")
    if translation.get("diagnosis"):
        lines.append(f"**Diagnosis**: {translation['diagnosis']}")
    if translation.get("causes"):
        lines.append("**Possible Causes**:")
        for cause in translation["causes"]:
            lines.append(f"- {cause}")
    if translation.get("repair_suggestions"):
        lines.append("**Repair Suggestions**:")
        for suggestion in translation["repair_suggestions"]:
            lines.append(f"- {suggestion}")
    if translation.get("circuit_specific"):
        lines.append(translation["circuit_specific"])
    if translation.get("example_fix"):
        lines.append(translation["example_fix"])
    return "\n".join(lines)


def translate_all_notes(notes: list[str], task_id: Optional[str] = None) -> str:
    sections = []
    for note in notes:
        translation = translate_diagnosis(note, task_id)
        if translation.get("diagnosis"):
            sections.append(f"### Diagnostic: `{note}`\n\n{format_repair_section(translation)}")
    if sections:
        return "\n\n---\n\n".join(sections)
    return ""


if __name__ == "__main__":
    test_notes = [
        "freq_ratio=2.0000 fb_jitter_frac=0.0000 lock_time=nan vctrl_min=1.200 vctrl_max=1.200",
        "normalized_tb_save_tokens=5",
        "window_fracs pre=1.000 mid=0.000 post=0.752",
        "unique_codes=1 vout_span=0.000 vin_span=0.721",
    ]
    for n in test_notes:
        print("=" * 80)
        print(n)
        print(format_repair_section(translate_diagnosis(n, "cppll_timer")))
