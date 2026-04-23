#!/usr/bin/env python3
"""
Diagnosis Translation System for EVAS Repair Prompt Enhancement.

Translates EVAS checker diagnostic messages into specific repair suggestions.

Usage:
    from diagnosis_translation import translate_diagnosis

    translation = translate_diagnosis("pre_high_frac=0.000 post_low_frac=1.000")
    print(translation["repair_suggestions"])
"""
from __future__ import annotations

import re
from typing import Optional


# Diagnosis pattern -> repair rules mapping
DIAGNOSIS_RULES = {
    # === Time window output anomalies ===
    "_frac=0.0": {
        "diagnosis": "Output never reached expected level in time window",
        "causes": [
            "Missing falling-edge handler (only rising edge exists, no falling-edge reset)",
            "Clock threshold mismatch, clock edge not triggering",
            "Initial state overriding subsequent state updates",
        ],
        "repair_suggestions": [
            "Check if there is @(cross(V(clk) - threshold, -1)) for falling edge",
            "Verify clock threshold matches actual clock amplitude (vdd/2)",
            "Ensure state update happens inside @(cross) block, not just outside",
        ],
        "example_fix": """
Example fix for clocked comparator:
```verilog-a
@(cross(V(CLK) - vdd/2, +1)) begin  // Rising edge: latch decision
    out_p = (V(VINP) > V(VINN)) ? vdd : 0;
end
@(cross(V(CLK) - vdd/2, -1)) begin  // Falling edge: RESET output
    out_p = 0;
    out_n = 0;
end
```
""",
    },

    "insufficient_toggle": {
        "diagnosis": "Output not toggling, span close to 0",
        "causes": [
            "Output stays constant",
            "Missing state flip logic",
        ],
        "repair_suggestions": [
            "Add state variable and flip logic",
            "Verify @(cross) triggers correctly",
        ],
    },

    "outputs_do_not_toggle": {
        "diagnosis": "Both outputs stay at same level",
        "causes": [
            "No state change triggered",
            "Threshold logic missing",
        ],
        "repair_suggestions": [
            "Add @(cross) for input threshold detection",
            "Implement state machine for output switching",
        ],
    },

    # === Code count issues ===
    "unique_codes=": {
        "diagnosis": "ADC/DAC produces insufficient unique codes",
        "causes": [
            "Quantization thresholds not distributed across input range",
            "LSB calculation error",
            "floor/clamp logic error",
        ],
        "repair_suggestions": [
            "Ensure LSB = (vrefp - vrefn) / 2^N",
            "Verify code = floor((vin - vrefn) / LSB), clamped to [0, 2^N-1]",
            "Check thresholds distributed: each bit needs different reference",
        ],
        "example_fix": """
Flash ADC correct implementation:
```verilog-a
lsb = (vrefp - vrefn) / 8.0;
code = $floor((V(vin) - vrefn) / lsb);
if (code < 0) code = 0;
if (code > 7) code = 7;
// Each bit output:
V(dout2) <+ transition((code >= 4) ? V(vdd) : V(vss), ...);
V(dout1) <+ transition((code >= 2) ? V(vdd) : V(vss), ...);
V(dout0) <+ transition((code >= 1) ? V(vdd) : V(vss), ...);
```
""",
    },

    "only_": {
        "diagnosis": "Produces far fewer codes than expected",
        "causes": [
            "Quantization function wrong",
            "All outputs share same threshold",
        ],
        "repair_suggestions": [
            "Flash ADC needs 2^N different comparator thresholds",
            "Each output bit needs independent judgment condition",
        ],
    },

    # === Hysteresis specific ===
    "window_fracs": {
        "diagnosis": "Hysteresis window test failed - output didn't change in mid-phase",
        "causes": [
            "Only one threshold, missing two @(cross) with opposite directions",
            "Rising and falling thresholds are same",
        ],
        "repair_suggestions": [
            "Hysteresis requires TWO @(cross) statements:",
            "  @(cross(V(inp) - V(inn) - vhys/2, +1))  // Rising threshold",
            "  @(cross(V(inp) - V(inn) + vhys/2, -1))  // Falling threshold",
            "Threshold directions MUST be opposite: +1 for rising, -1 for falling",
            "Between thresholds, HOLD previous state (no change)",
        ],
        "example_fix": """
Hysteresis comparator correct implementation:
```verilog-a
integer state;  // 0: out_p LOW, 1: out_p HIGH

@(cross(V(vinp) - V(vinn) - vhys/2, +1)) begin  // Rising through +vhys/2
    state = 1;  // out_p goes HIGH
end

@(cross(V(vinp) - V(vinn) + vhys/2, -1)) begin  // Falling through -vhys/2
    state = 0;  // out_p goes LOW
end

V(out_p) <+ transition(state ? V(vdd) : V(vss), ...);
V(out_n) <+ transition(state ? V(vss) : V(vdd), ...);
```
""",
    },

    "rise_t_out_of_range": {
        "diagnosis": "Output rise time outside expected hysteresis window",
        "causes": ["Threshold polarity wrong", "Hysteresis parameter mismatch"],
        "repair_suggestions": [
            "Check vhys/2 threshold calculation",
            "Verify rising edge detection direction (+1)",
        ],
    },

    "fall_t_out_of_range": {
        "diagnosis": "Output fall time outside expected hysteresis window",
        "causes": ["Threshold polarity wrong", "Hysteresis parameter mismatch"],
        "repair_suggestions": [
            "Check -vhys/2 threshold calculation",
            "Verify falling edge detection direction (-1)",
        ],
    },

    # === Edge/timer issues ===
    "rising_edge_count=": {
        "diagnosis": "Edge count mismatch",
        "causes": ["@(timer) used incorrectly", "Time grid calculation wrong"],
        "repair_suggestions": [
            "Ensure next_t increments inside each @(timer) block",
            "Verify tstart and tstep parameters",
            "Use @(timer(next_t)) not @(timer(delay))",
        ],
        "example_fix": """
Timer on absolute grid:
```verilog-a
real next_t;
@(initial_step) begin
    next_t = tstart;
end

@(timer(next_t)) begin
    // Toggle output
    state = !state;
    next_t = next_t + tstep;  // Increment for next event
end
```
""",
    },

    "not_enough_clk_edges": {
        "diagnosis": "Insufficient clock edges detected",
        "causes": ["Clock not generated", "Simulation time too short"],
        "repair_suggestions": [
            "Check testbench clock source: vsource type=pulse period=...",
            "Increase tran stop time to get more clock cycles",
            "Verify clock amplitude matches threshold",
        ],
    },

    "frame_rises=": {
        "diagnosis": "Frame signal rises fewer times than expected",
        "causes": ["Frame marker logic missing", "Incorrect frame period"],
        "repair_suggestions": [
            "Serializer must output frame marker at each frame period",
            "Check frame period matches expected cycle count",
        ],
    },

    # === Logic gate issues ===
    "invert_match_frac=": {
        "diagnosis": "NOT gate inversion match rate low",
        "causes": [
            "VDD/VSS not dynamically read",
            "Threshold setting wrong",
            "Output level stuck at parameter default",
        ],
        "repair_suggestions": [
            "CRITICAL: Read V(vdd) and V(vss) INSIDE @(cross) block:",
            "  v_high = V(vdd);  // NOT v_high = vdd_parameter",
            "  v_low = V(vss);",
            "Do NOT use static parameter defaults for output levels",
        ],
        "example_fix": """
NOT gate correct:
```verilog-a
@(cross(V(a) - vth, +1 or -1)) begin
    v_high = V(vdd);  // Dynamic read!
    v_low = V(vss);   // Dynamic read!
    out_val = (V(a) < vth) ? v_high : v_low;
end
V(y) <+ transition(out_val, ...);
```
""",
    },

    "truth_table_match=": {
        "diagnosis": "Logic gate truth table match rate low",
        "causes": ["Logic expression wrong", "Output not switching correctly"],
        "repair_suggestions": [
            "AND: Y HIGH only when BOTH A AND B HIGH",
            "OR: Y HIGH when EITHER A OR B HIGH",
            "Use dynamic level: V(Y) <+ V(vdd) or V(vss)",
        ],
    },

    # === Reset issues ===
    "no post-reset": {
        "diagnosis": "No valid output after reset release",
        "causes": ["Reset logic wrong", "State not restored after reset"],
        "repair_suggestions": [
            "Check reset triggers correctly",
            "Reset release should enable normal operation",
            "Use @(cross(V(rst), -1)) for reset release",
        ],
    },

    "reset_": {
        "diagnosis": "Reset behavior incorrect",
        "causes": ["Reset not clearing state", "Reset priority wrong"],
        "repair_suggestions": [
            "Reset should clear internal state variables",
            "Reset takes priority over clock sampling",
        ],
    },

    # === Missing signals ===
    "missing": {
        "diagnosis": "Required signal missing from waveform",
        "causes": ["Save statement missing signals", "Port name mismatch"],
        "repair_suggestions": [
            "Add all required signals to save statement",
            "Ensure DUT port names match TB save signal names",
            "Check signal naming: out_p vs outp, clk vs CLK",
        ],
    },

    # === ADC/DAC specific ===
    "vout_span=": {
        "diagnosis": "DAC output span too small",
        "causes": ["Transfer function wrong", "Vref not used"],
        "repair_suggestions": [
            "DAC: aout = code/2^N * Vref",
            "Ensure output swings from V(vss) to V(vrefp)",
        ],
    },

    "no_samples": {
        "diagnosis": "No samples in expected selection window",
        "causes": ["Selection logic wrong", "Simulation time insufficient"],
        "repair_suggestions": [
            "Mux: check each selection case has test window",
            "Extend tran stop time to cover all selection cases",
        ],
    },

    # === Serializer issues ===
    "sel0_err": {
        "diagnosis": "Mux selection 0 output incorrect",
        "causes": ["Selection logic case 0 wrong", "Output expression uses wrong input port"],
        "repair_suggestions": [
            "SEL=00 should output d0",
            "Check each case: 00→d0, 01→d1, 10→d2, 11→d3",
            "Verify the output assignment uses the correct input for each selection",
        ],
    },

    # === PLL / Clock issues ===
    "pre_lock=0": {
        "diagnosis": "PLL never achieved lock before disturbance",
        "causes": [
            "VCTRL not settling to a stable value",
            "Reference frequency mismatch",
            "Divider ratio incorrect",
            "Missing or broken lock detection logic",
        ],
        "repair_suggestions": [
            "Check VCTRL is being updated by charge pump on each UP/DN event",
            "Verify divider ratio produces frequency matching reference",
            "Ensure loop filter parameters allow settling within simulation time",
            "Check PFD is generating UP/DN pulses correctly",
        ],
    },

    "post_lock=0": {
        "diagnosis": "PLL did not re-lock after disturbance",
        "causes": [
            "Same as pre_lock causes",
            "Disturbance too large for loop to recover",
            "Missing recovery/relock logic",
        ],
        "repair_suggestions": [
            "Same checks as pre_lock",
            "Verify the loop can recover from the applied disturbance",
            "Check if VCTRL range is sufficient after disturbance",
        ],
    },

    "lock=": {
        "diagnosis": "PLL lock state incorrect",
        "causes": ["Lock detection threshold wrong", "Lock counter not incrementing"],
        "repair_suggestions": [
            "Check lock detection criteria (e.g., consecutive frequency matches)",
            "Verify lock signal is asserted when frequency is within tolerance",
        ],
    },

    "vctrl_range_ok=True": {
        "diagnosis": "VCTRL is in valid range but PLL still not locked",
        "causes": ["VCTRL not at correct value for lock", "Frequency still mismatched despite VCTRL in range"],
        "repair_suggestions": [
            "VCTRL being in range does not guarantee lock",
            "Check actual output frequency vs reference",
            "Verify divider is working correctly",
        ],
    },

    "relock_time=": {
        "diagnosis": "PLL re-lock time outside expected range",
        "causes": ["Loop bandwidth too narrow", "Charge pump current too small"],
        "repair_suggestions": [
            "Check loop filter bandwidth allows fast settling",
            "Verify charge pump strength",
            "Ensure no unnecessary delays in control path",
        ],
    },

    "freq_ratio=": {
        "diagnosis": "Frequency ratio (output/reference) incorrect",
        "causes": ["Divider ratio wrong", "VCO frequency wrong"],
        "repair_suggestions": [
            "Check divider outputs correct frequency",
            "Verify VCO gain (Kvco) parameter",
            "Ensure reference frequency is as expected",
        ],
    },

    # === Delay / Timing issues ===
    "delays_ns=": {
        "diagnosis": "Delay values measured",
        "causes": ["May indicate correct or incorrect delays"],
        "repair_suggestions": [
            "Compare delays against expected values",
            "If delays vary wildly, check if all instances work correctly",
        ],
    },

    "monotonic=False": {
        "diagnosis": "Delay sequence is NOT monotonic",
        "causes": [
            "Some comparator instances bypass measurement (delay ~0)",
            "Edge timing measurement error",
            "Only one instance responding correctly",
        ],
        "repair_suggestions": [
            "Check if all parallel instances have correct thresholds",
            "Verify each instance triggers on the correct input edge",
            "Ensure no instance is stuck or bypassing the delay path",
        ],
    },

    # === BBPD / Edge alignment issues ===
    "lead_window": {
        "diagnosis": "Data edge alignment window mismatch",
        "causes": [
            "Data signal timing relative to clock edge incorrect",
            "Timer/cross threshold for window detection wrong",
            "Sampling edge direction mismatch",
        ],
        "repair_suggestions": [
            "Check data and clock edge timing relationship",
            "Verify timer timing matches expected window",
            "Ensure sampling happens at correct edge (rising vs falling)",
        ],
    },

    "updn": {
        "diagnosis": "UP/DN signal pattern incorrect",
        "causes": ["Phase detector logic wrong", "Edge direction inverted"],
        "repair_suggestions": [
            "Check PFD generates correct UP/DN for early/late conditions",
            "Verify UP when phase early (data leads clock), DN when late",
        ],
    },

    # === Reset issues (extended) ===
    "reset_outp_max=": {
        "diagnosis": "Reset does not clear output to zero",
        "causes": [
            "Reset priority logic incorrect",
            "Output not forced to zero during reset",
            "Reset edge detection missing or wrong direction",
        ],
        "repair_suggestions": [
            "Reset should force both outputs to zero immediately",
            "Check reset condition is checked BEFORE comparison logic",
            "Verify reset detection uses correct edge (rising for active-high reset)",
        ],
        "example_fix": """
StrongARM reset priority fix:
```verilog-a
@(cross(V(clk) - vth, +1)) begin
    if (V(rst) > vth) begin  // RESET TAKES PRIORITY
        outp_state = 0;
        outn_state = 0;
    end else begin  // Normal comparison only when reset inactive
        // ... comparison logic
    end
end
```
""",
    },

    "high_outp=": {
        "diagnosis": "Output high/low levels incorrect",
        "causes": ["Output not reaching expected voltage", "Logic state inverted"],
        "repair_suggestions": [
            "Check output levels match VDD/VSS",
            "Verify output state assignment logic",
        ],
    },

    # === ADC/DAC issues (extended) ===
    "delays": {
        "diagnosis": "Comparator/ADC delay values",
        "causes": ["Delays measured for analysis"],
        "repair_suggestions": [
            "If delays non-uniform, check comparator thresholds distribution",
            "Ensure all bits have similar response times",
        ],
    },
}


def translate_diagnosis(note: str, task_id: Optional[str] = None) -> dict:
    """
    Translate EVAS diagnostic message to repair suggestions.

    Args:
        note: Diagnostic string from EVAS checker, e.g. "pre_high_frac=0.000"
        task_id: Optional task ID for circuit-specific context

    Returns:
        dict with keys:
        - diagnosis: str, human-readable problem description
        - causes: list[str], possible root causes
        - repair_suggestions: list[str], specific fix hints
        - example_fix: str, example code (if available)
        - circuit_specific: str, circuit-specific knowledge (if applicable)
    """
    result = {
        "diagnosis": "",
        "causes": [],
        "repair_suggestions": [],
        "example_fix": "",
        "circuit_specific": "",
    }

    # Pattern matching
    for pattern, rules in DIAGNOSIS_RULES.items():
        if pattern in note:
            result["diagnosis"] = rules.get("diagnosis", "")
            result["causes"] = rules.get("causes", [])
            result["repair_suggestions"] = rules.get("repair_suggestions", [])
            result["example_fix"] = rules.get("example_fix", "")
            break

    # Circuit-specific knowledge injection
    if task_id:
        result["circuit_specific"] = _circuit_specific_knowledge(note, task_id)

    return result


def _circuit_specific_knowledge(note: str, task_id: str) -> str:
    """Add circuit-specific repair knowledge based on task context."""

    knowledge = ""

    # StrongARM comparator specific
    if "strongarm" in task_id.lower() and ("pre_high_frac=0" in note or "frac=0.0" in note or "reset" in note):
        knowledge = """
## StrongARM Comparator Specific Knowledge

StrongARM architecture requires output reset on clock **falling edge**:

The characteristic behavior:
- Rising edge:Latch comparison result
- **Falling edge: Reset both outputs to 0**

Without falling-edge reset, outputs stay latched and never show the expected pre/post window behavior.

**Reset priority**: Reset signal must force outputs to zero BEFORE any comparison logic.
"""

    # Hysteresis comparator specific
    elif "hysteresis" in task_id.lower() and "window_fracs" in note:
        knowledge = """
## Hysteresis Comparator Specific Knowledge

Hysteresis creates two different switching thresholds:
- Rising threshold (+vhys/2): higher than zero
- Falling threshold (-vhys/2): lower than zero

Key insight: When input is BETWEEN thresholds, output should **hold previous state**, not change.
"""

    # Flash ADC specific
    elif "flash_adc" in task_id.lower() and ("unique_codes" in note or "only_" in note):
        knowledge = """
## Flash ADC Specific Knowledge

3-bit Flash ADC requires 8 distinct quantization thresholds.
Each bit represents a different range of input voltage:
- dout2 (MSB): vin >= 4*LSB
- dout1: vin >= 2*LSB
- dout0 (LSB): vin >= 1*LSB

All bits should NOT share the same threshold.
"""

    # PLL / ADPLL / CPPLL specific
    elif any(kw in task_id.lower() for kw in ["pll", "adpll", "cppll", "pfd"]):
        if "lock" in note.lower() or "vctrl" in note.lower():
            knowledge = """
## PLL / Clock Generator Specific Knowledge

PLL lock condition:
- VCTRL stable at a constant value
- Divider output frequency matches reference frequency
- Phase error is zero (or within tolerance)

Key components:
- **PFD (Phase Frequency Detector)**: Generates UP/DN pulses based on phase difference
- **Charge Pump**: Converts UP/DN to current that charges/discharges VCTRL
- **VCO/DCO**: Output frequency controlled by VCTRL
- **Divider**: Divides VCO output to match reference

Common PLL bugs:
- PFD not generating correct UP/DN polarity
- Charge pump not updating VCTRL
- Divider ratio wrong (doesn't match target frequency)
- Loop bandwidth too narrow (slow settling)
- Missing lock detection logic
"""
        elif "bbpd" in task_id.lower() or "edge" in note.lower():
            knowledge = """
## Bang-Bang Phase Detector (BBPD) Specific Knowledge

BBPD is used in clock/data recovery:
- Samples data on clock edge
- Determines if data edge leads or lags clock
- UP pulse when data early, DN pulse when data late

Edge alignment window:
- Correct alignment: data edge centered in clock window
- Lead: data edge before clock edge → UP pulse
- Lag: data edge after clock edge → DN pulse
"""

    # MUX specific
    elif "mux" in task_id.lower():
        knowledge = """
## MUX (Multiplexer) Specific Knowledge

N-to-1 MUX selects one input based on SEL signal:
- 2-to-1 MUX: SEL=0 → output d0, SEL=1 → output d1
- 4-to-1 MUX: SEL=00→d0, SEL=01→d1, SEL=10→d2, SEL=11→d3

Common MUX bugs:
- SEL to input mapping incorrect
- Output uses wrong input port
- SEL bits interpreted in wrong order (LSB vs MSB)
"""

    # DAC specific
    elif "dac" in task_id.lower():
        knowledge = """
## DAC (Digital-to-Analog Converter) Specific Knowledge

DAC converts digital code to analog voltage:
- Binary-weighted DAC: each bit has different weight
- LSB weight = Vref / 2^N
- Total output = sum of (bit_value * bit_weight)

Common DAC bugs:
- Bit weights incorrect
- Missing bit in output sum
- Output level not matching Vref range
"""

    # Divider / Counter specific
    elif any(kw in task_id.lower() for kw in ["divider", "counter", "clk_divider"]):
        knowledge = """
## Clock Divider / Counter Specific Knowledge

Clock divider divides input frequency:
- Div_ratio = N means output frequency = input_freq / N
- Counter increments on each clock edge
- Output toggles when counter reaches threshold

Common divider bugs:
- Counter not incrementing correctly
- Wrong threshold for division
- Output not toggling at correct time
"""

    # Timer specific
    elif "timer" in task_id.lower() and "rising_edge_count" in note:
        knowledge = """
## Absolute Grid Timer Specific Knowledge

Timer on absolute grid uses @(timer(next_t)), not @(timer(delay)).
Each event must update next_t for the next scheduled event.
"""

    # NOT gate specific
    elif "not_gate" in task_id.lower() and "invert_match" in note:
        knowledge = """
## NOT Gate Specific Knowledge

Common mistake: Using parameter vdd instead of dynamic V(vdd).
Parameter vdd is a static default value, not the actual supply voltage.
Must read V(vdd) dynamically inside @(cross) for correct output levels.
"""

    return knowledge


def format_repair_section(translation: dict) -> str:
    """Format translation result as markdown section for repair prompt."""
    lines = []

    if translation["diagnosis"]:
        lines.append(f"**诊断**: {translation['diagnosis']}")

    if translation["causes"]:
        lines.append("**可能原因**:")
        for cause in translation["causes"]:
            lines.append(f"- {cause}")

    if translation["repair_suggestions"]:
        lines.append("**修复建议**:")
        for suggestion in translation["repair_suggestions"]:
            lines.append(f"- {suggestion}")

    if translation["circuit_specific"]:
        lines.append(translation["circuit_specific"])

    if translation["example_fix"]:
        lines.append(translation["example_fix"])

    return "\n".join(lines)


def translate_all_notes(notes: list[str], task_id: Optional[str] = None) -> str:
    """Translate all diagnostic notes and format as repair prompt section."""
    sections = []

    for note in notes:
        translation = translate_diagnosis(note, task_id)
        if translation["diagnosis"]:
            section = f"### 诊断信息: `{note}`\n\n{format_repair_section(translation)}"
            sections.append(section)

    if sections:
        return "\n\n---\n\n".join(sections)
    return ""


# Self-test
if __name__ == "__main__":
    test_notes = [
        "pre_high_frac=0.000 post_low_frac=1.000",
        "window_fracs pre=1.000 mid=0.000 post=0.752",
        "unique_codes=1 vout_span=0.000",
        "invert_match_frac=0.375",
    ]

    for note in test_notes:
        print(f"\n{'='*60}")
        print(f"Input: {note}")
        print(f"{'='*60}")
        translation = translate_diagnosis(note, "cmp_strongarm_smoke")
        print(format_repair_section(translation))