# Resistor Ladder Monotonic Decoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `resistor_ladder_monotonic_decoder.va`:
  - Module `resistor_ladder_monotonic_decoder` (entry)
    - position 0: `code_2` (inout, electrical)
    - position 1: `code_1` (inout, electrical)
    - position 2: `code_0` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `rst` (inout, electrical)
    - position 5: `vout` (inout, electrical)
    - position 6: `step_metric` (inout, electrical)
    - position 7: `monotonic_ok` (inout, electrical)

## Public Parameter Contract

- `resistor_ladder_monotonic_decoder.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `resistor_ladder_monotonic_decoder.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `resistor_ladder_monotonic_decoder.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `resistor_ladder_monotonic_decoder.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `resistor_ladder_monotonic_decoder.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `resistor_ladder_monotonic_decoder.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` low, clear `step_metric`, and clear `monotonic_ok`. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_DECODE_CODE_2_CODE_0_AS`: restore: Decode `code_2..code_0` as an unsigned ladder tap index from 0 to 7. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_DRIVE_VOUT_TO_THE_CORRESPONDING_EVENLY`: restore: Drive `vout` to the corresponding evenly spaced ladder voltage between `vss` and `vdd`. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_EXPOSE_ONE_LSB_STEP_ON_STEP`: restore: Expose one LSB step on `step_metric` while enabled. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_ASSERT_MONOTONIC_OK_WHEN_THE_ACTIVE`: restore: Assert `monotonic_ok` when the active code-to-output mapping is nondecreasing. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `resistor_ladder_monotonic_decoder.va`.
Every supplied `.va` file is editable; do not add or omit files.
