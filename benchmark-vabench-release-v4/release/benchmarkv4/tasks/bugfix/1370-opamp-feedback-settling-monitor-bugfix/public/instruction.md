# Op-amp Feedback Settling Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `opamp_feedback_settling.va`:
  - Module `opamp_feedback_settling` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `gain_2` (inout, electrical)
    - position 5: `gain_1` (inout, electrical)
    - position 6: `gain_0` (inout, electrical)
    - position 7: `vout` (inout, electrical)
    - position 8: `error_metric` (inout, electrical)
    - position 9: `settled` (inout, electrical)

## Public Parameter Contract

- `opamp_feedback_settling.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `opamp_feedback_settling.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `opamp_feedback_settling.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `opamp_feedback_settling.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `opamp_feedback_settling.gain_lsb` defaults to `0.5`; valid range: finite; overrides gain_lsb.
- `opamp_feedback_settling.alpha` defaults to `0.3`; valid range: finite; overrides alpha.
- `opamp_feedback_settling.settle_tol` defaults to `40e-3`; valid range: finite; overrides settle_tol.
- `opamp_feedback_settling.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `opamp_feedback_settling.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: restore: On reset or when `enable` is low, drive `vout` to `vcm`, clear `error_metric`, and clear `settled`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_DECODE_GAIN_2_GAIN_0_INTO`: restore: Decode `gain_2..gain_0` into a closed-loop target gain of at least unity. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_UPDATE_VOUT_ONCE_PER_RISING_CLK`: restore: Update `vout` once per rising `clk` edge toward the target closed-loop output using `alpha`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_CLAMP_VOUT_TO_THE_RANGE_VSS`: restore: Clamp `vout` to the range `vss` through `vdd`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_ERROR_METRIC_MUST_EXPOSE_THE_SIGNED`: restore: `error_metric` must expose the signed difference between the current output and the target closed-loop value. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_THREE_CONSECUTIVE_UPDATES`: restore: Assert `settled` after three consecutive updates where the absolute error is below `settle_tol`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `gain_2`, `gain_1`, `gain_0`, `vout`, `error_metric`, `settled`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `opamp_feedback_settling.va`.
Every supplied `.va` file is editable; do not add or omit files.
