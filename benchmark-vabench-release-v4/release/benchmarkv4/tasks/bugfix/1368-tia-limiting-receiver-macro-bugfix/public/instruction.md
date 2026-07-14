# TIA Limiting Receiver Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `tia_limiting_receiver.va`:
  - Module `tia_limiting_receiver` (entry)
    - position 0: `vin_proxy` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `decision` (inout, electrical)
    - position 6: `limit_flag` (inout, electrical)
    - position 7: `valid` (inout, electrical)
    - position 8: `amp_metric` (inout, electrical)

## Public Parameter Contract

- `tia_limiting_receiver.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `tia_limiting_receiver.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `tia_limiting_receiver.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `tia_limiting_receiver.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `tia_limiting_receiver.gain` defaults to `4.0`; valid range: finite; overrides gain.
- `tia_limiting_receiver.limit` defaults to `0.35`; valid range: finite; overrides limit.
- `tia_limiting_receiver.valid_min` defaults to `40e-3`; valid range: finite; overrides valid_min.
- `tia_limiting_receiver.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `tia_limiting_receiver.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: restore: On reset or when `enable` is low, drive `vout` to `vcm` and clear `decision`, `limit_flag`, `valid`, and `amp_metric`. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_TREAT_VIN_PROXY_AS_A_VOLTAGE`: restore: Treat `vin_proxy` as a voltage-domain proxy for receiver input magnitude; no current ports are required. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_APPLY_GAIN_TO_THE_DEVIATION_FROM`: restore: Apply gain to the deviation from `vcm` and clamp the output to `vcm +/- limit`. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ASSERT_LIMIT_FLAG_WHEN_THE_UNCLAMPED`: restore: Assert `limit_flag` when the unclamped amplified signal would exceed the limiter range. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ON_EACH_RISING_CLK_EDGE_DRIVE`: restore: On each rising `clk` edge, drive `decision` high when the limited output is at or above `vcm`, otherwise low. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ASSERT_VALID_WHEN_AMP_METRIC_IS`: restore: Assert `valid` when `amp_metric` is at least `valid_min` for two consecutive clock updates. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `tia_limiting_receiver.va`.
Every supplied `.va` file is editable; do not add or omit files.
