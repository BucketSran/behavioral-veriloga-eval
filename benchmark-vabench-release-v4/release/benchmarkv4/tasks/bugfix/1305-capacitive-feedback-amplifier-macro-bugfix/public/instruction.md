# Capacitive-feedback Amplifier Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `capacitive_feedback_amplifier_macro.va`:
  - Module `capacitive_feedback_amplifier_macro` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `gain_1` (inout, electrical)
    - position 5: `gain_0` (inout, electrical)
    - position 6: `vout` (inout, electrical)
    - position 7: `sampled_metric` (inout, electrical)
    - position 8: `settled` (inout, electrical)

## Public Parameter Contract

- `capacitive_feedback_amplifier_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `capacitive_feedback_amplifier_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `capacitive_feedback_amplifier_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `capacitive_feedback_amplifier_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `capacitive_feedback_amplifier_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `capacitive_feedback_amplifier_macro.gain_step` defaults to `0.75`; valid range: finite; overrides gain_step.
- `capacitive_feedback_amplifier_macro.settle_tol` defaults to `10e-3`; valid range: finite; overrides settle_tol.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear `sampled_metric`, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: restore: On each rising `clk` edge while enabled, sample `vin` and decode `gain_1..gain_0` as a programmable capacitor ratio. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_DRIVE_SAMPLED_METRIC_WITH_THE_HELD`: restore: Drive `sampled_metric` with the held input sample. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_MOVE_VOUT_TOWARD_VCM_GAIN_SAMPLE`: restore: Move `vout` toward `vcm + gain * (sample - vcm)` with bounded per-update movement. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_THE_OUTPUT_HAS`: restore: Assert `settled` after the output has stayed within `settle_tol` of the target for two enabled updates. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `capacitive_feedback_amplifier_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
