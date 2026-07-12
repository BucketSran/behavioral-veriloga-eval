# Configurable Pulse Train Generator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `configurable_pulse_train.va`:
  - Module `configurable_pulse_train` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `start` (input, electrical)
    - position 2: `period0` (input, electrical)
    - position 3: `period1` (input, electrical)
    - position 4: `period2` (input, electrical)
    - position 5: `period3` (input, electrical)
    - position 6: `width0` (input, electrical)
    - position 7: `width1` (input, electrical)
    - position 8: `width2` (input, electrical)
    - position 9: `width3` (input, electrical)
    - position 10: `count0` (input, electrical)
    - position 11: `count1` (input, electrical)
    - position 12: `count2` (input, electrical)
    - position 13: `count3` (input, electrical)
    - position 14: `pulse` (output, electrical)
    - position 15: `done` (output, electrical)

## Public Parameter Contract

- `configurable_pulse_train.vdd` defaults to `0.9` V; valid range: vdd > 0; sets pulse and done high levels.
- `configurable_pulse_train.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the threshold for clk, start, and every control-word bit.
- `configurable_pulse_train.tr` defaults to `2e-11` s; valid range: tr > 0; sets rise and fall smoothing for pulse and done.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_IDLE_CAPTURE`: restore: A sampled high start while idle captures unsigned period3:period0, width3:width0, and count3:count0 on a rising clk crossing. Required traces: `time`, `clk`, `start`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_ZERO_CODE_MINIMUM`: restore: A zero-coded period, width, or count is interpreted as one clock sample rather than zero. Required traces: `time`, `clk`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_PULSE_COUNT`: restore: Each accepted command emits exactly the captured count number of pulses. Required traces: `time`, `clk`, `start`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_WIDTH_AND_PERIOD`: restore: Each pulse remains high for the captured width in clock samples and pulse starts are separated by the captured period in clock samples. Required traces: `time`, `clk`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `pulse`.
- `P_COMPLETION`: restore: After the final pulse completes, pulse is low and done is asserted. Required traces: `time`, `clk`, `pulse`, `done`.
- `P_OUTPUT_LEVELS`: restore: pulse and done use 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `pulse`, `done`.

## Modeling Constraints

- AMS role: finite pulse-train sequencer for calibration, startup, and sampled-data control timing.
- Use deterministic rising-edge clocked state for command capture and pulse sequencing.
- Decode each four-bit control word as unsigned with bit 3 as the MSB and bit 0 as the LSB.
- Do not add undeclared reset, debug, or validation-only ports or behavior.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `configurable_pulse_train.va`.
Every supplied `.va` file is editable; do not add or omit files.
