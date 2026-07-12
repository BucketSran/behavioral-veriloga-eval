# Capacitive-feedback Amplifier Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Capacitive-feedback Amplifier Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `capacitive_feedback_amplifier_macro` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, enable=enable, gain_1=gain_1, gain_0=gain_0, vout=vout, sampled_metric=sampled_metric, settled=settled.

## Public Parameter Contract

- `capacitive_feedback_amplifier_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `capacitive_feedback_amplifier_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `capacitive_feedback_amplifier_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `capacitive_feedback_amplifier_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `capacitive_feedback_amplifier_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `capacitive_feedback_amplifier_macro.gain_step` defaults to `0.75`; valid range: finite; overrides gain_step.
- `capacitive_feedback_amplifier_macro.settle_tol` defaults to `10e-3`; valid range: finite; overrides settle_tol.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm`, clear `sampled_metric`, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: exercise and make observable: On each rising `clk` edge while enabled, sample `vin` and decode `gain_1..gain_0` as a programmable capacitor ratio. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_DRIVE_SAMPLED_METRIC_WITH_THE_HELD`: exercise and make observable: Drive `sampled_metric` with the held input sample. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_MOVE_VOUT_TOWARD_VCM_GAIN_SAMPLE`: exercise and make observable: Move `vout` toward `vcm + gain * (sample - vcm)` with bounded per-update movement. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_THE_OUTPUT_HAS`: exercise and make observable: Assert `settled` after the output has stayed within `settle_tol` of the target for two enabled updates. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `enable`, `gain_1`, `gain_0`, `vout`, `sampled_metric`, `settled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
