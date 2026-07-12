# Serializer MUX Timing Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Serializer MUX Timing Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `serializer_mux_timing_macro` as `XDUT` with ordered public binding: clk=clk, rst=rst, enable=enable, d0=d0, d1=d1, d2=d2, d3=d3, serial_out=serial_out, slot_1=slot_1, slot_0=slot_0, valid=valid.

## Public Parameter Contract

- `serializer_mux_timing_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `serializer_mux_timing_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `serializer_mux_timing_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `serializer_mux_timing_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `serializer_mux_timing_macro.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear `serial_out`, slot outputs, and `valid`. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_WHEN_ENABLED_STEP_THROUGH_INPUTS_D0`: exercise and make observable: When enabled, step through inputs `d0`, `d1`, `d2`, and `d3` on successive rising `clk` edges. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_DRIVE_SERIAL_OUT_AS_THE_VOLTAGE`: exercise and make observable: Drive `serial_out` as the voltage-coded value of the active input slot. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_SLOT_1_SLOT_0_MUST_EXPOSE`: exercise and make observable: `slot_1..slot_0` must expose the active slot index. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_COMPLETE`: exercise and make observable: Assert `valid` after the first complete four-slot frame. Required traces: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.

The required trace names are: `time`, `clk`, `rst`, `enable`, `d0`, `d1`, `d2`, `d3`, `serial_out`, `slot_1`, `slot_0`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
