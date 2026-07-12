# Reference Ladder with Buffered Taps Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `reference_ladder_buffered_taps.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `reference_ladder_buffered_taps.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `reference_ladder_buffered_taps.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `reference_ladder_buffered_taps.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reference_ladder_buffered_taps.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `reference_ladder_buffered_taps.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive taps to `vss` and clear `monotonic_ok`. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_WHEN_ENABLED_GENERATE_FOUR_EVENLY_SPACED`: restore: When enabled, generate four evenly spaced buffered tap voltages between `vref_lo` and `vref_hi`. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_CLAMP_REVERSED_OR_OUT_OF_RANGE`: restore: Clamp reversed or out-of-range references into the public rail range before generating taps. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_ASSERT_MONOTONIC_OK_ONLY_WHEN_THE`: restore: Assert `monotonic_ok` only when the exposed tap sequence is nondecreasing. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_SMOOTH_TAP_OUTPUT_TRANSITIONS_WITH_THE`: restore: Smooth tap output transitions with the public transition parameter. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vref_hi`, `vref_lo`, `enable`, `rst`, `tap0`, `tap1`, `tap2`, `tap3`, `monotonic_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `reference_ladder_buffered_taps.va`.
Every supplied `.va` file is editable; do not add or omit files.
