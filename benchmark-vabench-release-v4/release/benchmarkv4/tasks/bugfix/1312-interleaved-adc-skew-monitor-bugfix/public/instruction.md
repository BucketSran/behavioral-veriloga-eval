# Interleaved ADC Timing-skew Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear both sample states and all metrics. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_CAPTURE_VIN_A_ON_RISING_CLK`: restore: Capture `vin_a` on rising `clk_a` and `vin_b` on rising `clk_b`. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_ESTIMATE_A_SKEW_PROXY_FROM_THE`: restore: Estimate a skew proxy from the signed difference between the two most recent samples. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_DRIVE_SKEW_METRIC_WITH_THE_ABSOLUTE`: restore: Drive `skew_metric` with the absolute skew proxy and `magnitude_metric` with the average sample magnitude. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_ASSERT_ALARM_WHEN_SKEW_METRIC_EXCEEDS`: restore: Assert `alarm` when `skew_metric` exceeds `skew_limit` for two consecutive comparisons. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin_a`, `vin_b`, `clk_a`, `clk_b`, `rst`, `enable`, `skew_metric`, `magnitude_metric`, `alarm`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `interleaved_adc_skew_monitor_top.va`, `sample_pair_latch.va`, `skew_metric_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
