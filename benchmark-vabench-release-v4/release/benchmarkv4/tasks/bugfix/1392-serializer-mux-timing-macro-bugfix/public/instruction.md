# Serializer MUX Timing Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `serializer_mux_timing_macro.va`:
  - Module `serializer_mux_timing_macro` (entry)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `d0` (inout, electrical)
    - position 4: `d1` (inout, electrical)
    - position 5: `d2` (inout, electrical)
    - position 6: `d3` (inout, electrical)
    - position 7: `serial_out` (inout, electrical)
    - position 8: `slot_1` (inout, electrical)
    - position 9: `slot_0` (inout, electrical)
    - position 10: `valid` (inout, electrical)

## Public Parameter Contract

- `serializer_mux_timing_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `serializer_mux_timing_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `serializer_mux_timing_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `serializer_mux_timing_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `serializer_mux_timing_macro.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear `serial_out`, slot outputs, and `valid`. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_WHEN_ENABLED_STEP_THROUGH_INPUTS_D0`: restore: When enabled, step through inputs `d0`, `d1`, `d2`, and `d3` on successive rising `clk` edges. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_DRIVE_SERIAL_OUT_AS_THE_VOLTAGE`: restore: Drive `serial_out` as the voltage-coded value of the active input slot. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_SLOT_1_SLOT_0_MUST_EXPOSE`: restore: `slot_1..slot_0` must expose the active slot index. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_COMPLETE`: restore: Assert `valid` after the first complete four-slot frame. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Implement a serializer timing DUT rather than a generic bus splitter.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `serializer_mux_timing_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
