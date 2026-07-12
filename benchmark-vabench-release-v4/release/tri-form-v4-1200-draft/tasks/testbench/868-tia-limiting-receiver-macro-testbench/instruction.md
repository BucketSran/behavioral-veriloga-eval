# TIA Limiting Receiver Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `TIA Limiting Receiver Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `tia_limiting_receiver` as `XDUT` with ordered public binding: vin_proxy=vin_proxy, clk=clk, rst=rst, enable=enable, vout=vout, decision=decision, limit_flag=limit_flag, valid=valid, amp_metric=amp_metric.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: exercise and make observable: On reset or when `enable` is low, drive `vout` to `vcm` and clear `decision`, `limit_flag`, `valid`, and `amp_metric`. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_TREAT_VIN_PROXY_AS_A_VOLTAGE`: exercise and make observable: Treat `vin_proxy` as a voltage-domain proxy for receiver input magnitude; no current ports are required. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_APPLY_GAIN_TO_THE_DEVIATION_FROM`: exercise and make observable: Apply gain to the deviation from `vcm` and clamp the output to `vcm +/- limit`. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ASSERT_LIMIT_FLAG_WHEN_THE_UNCLAMPED`: exercise and make observable: Assert `limit_flag` when the unclamped amplified signal would exceed the limiter range. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ON_EACH_RISING_CLK_EDGE_DRIVE`: exercise and make observable: On each rising `clk` edge, drive `decision` high when the limited output is at or above `vcm`, otherwise low. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.
- `P_ASSERT_VALID_WHEN_AMP_METRIC_IS`: exercise and make observable: Assert `valid` when `amp_metric` is at least `valid_min` for two consecutive clock updates. Required traces: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.

The required trace names are: `time`, `vin_proxy`, `clk`, `rst`, `enable`, `vout`, `decision`, `limit_flag`, `valid`, `amp_metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
