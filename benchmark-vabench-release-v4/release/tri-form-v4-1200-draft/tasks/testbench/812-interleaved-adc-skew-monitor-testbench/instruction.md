# Interleaved ADC Timing-skew Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Interleaved ADC Timing-skew Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `interleaved_adc_skew_monitor_top.va`:
  - Module `interleaved_adc_skew_monitor_top` (entry)
    - position 0: `vin_a` (input, electrical)
    - position 1: `vin_b` (input, electrical)
    - position 2: `clk_a` (input, electrical)
    - position 3: `clk_b` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `enable` (input, electrical)
    - position 6: `skew_metric` (output, electrical)
    - position 7: `magnitude_metric` (output, electrical)
    - position 8: `alarm` (output, electrical)
- Artifact `sample_pair_latch.va`:
  - Module `sample_pair_latch` (required_submodule)
    - position 0: `vin_a` (input, electrical)
    - position 1: `vin_b` (input, electrical)
    - position 2: `clk_a` (input, electrical)
    - position 3: `clk_b` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `enable` (input, electrical)
    - position 6: `sa` (output, electrical)
    - position 7: `sb` (output, electrical)
    - position 8: `ready` (output, electrical)
- Artifact `skew_metric_core.va`:
  - Module `skew_metric_core` (required_submodule)
    - position 0: `sa` (input, electrical)
    - position 1: `sb` (input, electrical)
    - position 2: `ready` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `skew_metric` (output, electrical)
    - position 6: `magnitude_metric` (output, electrical)
    - position 7: `alarm` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `interleaved_adc_skew_monitor_top` as `XDUT` with ordered public binding: vin_a=vin_a, vin_b=vin_b, clk_a=clk_a, clk_b=clk_b, rst=rst, enable=enable, skew_metric=skew_metric, magnitude_metric=magnitude_metric, alarm=alarm.

## Public Parameter Contract

- `interleaved_adc_skew_monitor_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `interleaved_adc_skew_monitor_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `interleaved_adc_skew_monitor_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `interleaved_adc_skew_monitor_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `interleaved_adc_skew_monitor_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `interleaved_adc_skew_monitor_top.skew_limit` defaults to `40e-3`; valid range: finite; overrides skew_limit.
- `sample_pair_latch.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `sample_pair_latch.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `sample_pair_latch.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `sample_pair_latch.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `sample_pair_latch.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `skew_metric_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `skew_metric_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `skew_metric_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `skew_metric_core.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `skew_metric_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `skew_metric_core.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.
- `skew_metric_core.skew_limit` defaults to `40e-3`; valid range: finite; overrides skew_limit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear both sample states and all metrics. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_CAPTURE_VIN_A_ON_RISING_CLK`: exercise and make observable: Capture `vin_a` on rising `clk_a` and `vin_b` on rising `clk_b`. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_ESTIMATE_A_SKEW_PROXY_FROM_THE`: exercise and make observable: Estimate a skew proxy from the signed difference between the two most recent samples. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE`: exercise and make observable: Drive `skew_metric` with the absolute skew proxy and `magnitude_metric` with the average sample magnitude. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_ASSERT_ALARM_WHEN_SKEW_METRIC_EXCEEDS`: exercise and make observable: Assert `alarm` when `skew_metric` exceeds `skew_limit` for two consecutive comparisons. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.

The required trace names are: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
