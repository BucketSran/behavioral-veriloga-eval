# Reference Ladder with Buffered Taps Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reference Ladder with Buffered Taps` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `reference_ladder_buffered_taps.va`:
  - Module `reference_ladder_buffered_taps` (entry)
    - position 0: `vref_hi` (inout, electrical)
    - position 1: `vref_lo` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `tap0` (inout, electrical)
    - position 5: `tap1` (inout, electrical)
    - position 6: `tap2` (inout, electrical)
    - position 7: `tap3` (inout, electrical)
    - position 8: `monotonic_ok` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `reference_ladder_buffered_taps` as `XDUT` with ordered public binding: vref_hi=vref_hi, vref_lo=vref_lo, enable=enable, rst=rst, tap0=tap0, tap1=tap1, tap2=tap2, tap3=tap3, monotonic_ok=monotonic_ok.

## Public Parameter Contract

- `reference_ladder_buffered_taps.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `reference_ladder_buffered_taps.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `reference_ladder_buffered_taps.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `reference_ladder_buffered_taps.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reference_ladder_buffered_taps.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `reference_ladder_buffered_taps.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive taps to `vss` and clear `monotonic_ok`. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_WHEN_ENABLED_GENERATE_FOUR_EVENLY_SPACED`: exercise and make observable: When enabled, generate four evenly spaced buffered tap voltages between `vref_lo` and `vref_hi`. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_CLAMP_REVERSED_OR_OUT_OF_RANGE`: exercise and make observable: Clamp reversed or out-of-range references into the public rail range before generating taps. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_ASSERT_MONOTONIC_OK_ONLY_WHEN_THE`: exercise and make observable: Assert `monotonic_ok` only when the exposed tap sequence is nondecreasing. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_SMOOTH_TAP_OUTPUT_TRANSITIONS_WITH_THE`: exercise and make observable: Smooth tap output transitions with the public transition parameter. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.

The required trace names are: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
