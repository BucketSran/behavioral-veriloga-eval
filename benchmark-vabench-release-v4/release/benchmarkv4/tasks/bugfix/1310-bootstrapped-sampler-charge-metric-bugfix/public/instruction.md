# Bootstrapped Sampler Charge Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bootstrapped_sampler_charge_metric.va`:
  - Module `bootstrapped_sampler_charge_metric` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `vhold` (inout, electrical)
    - position 5: `boot_metric` (inout, electrical)
    - position 6: `droop_flag` (inout, electrical)

## Public Parameter Contract

- `bootstrapped_sampler_charge_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `bootstrapped_sampler_charge_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `bootstrapped_sampler_charge_metric.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `bootstrapped_sampler_charge_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `bootstrapped_sampler_charge_metric.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `bootstrapped_sampler_charge_metric.droop_step` defaults to `2e-3`; valid range: finite; overrides droop_step.
- `bootstrapped_sampler_charge_metric.droop_tol` defaults to `10e-3`; valid range: finite; overrides droop_tol.
- `bootstrapped_sampler_charge_metric.tick` defaults to `1n from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear held output, bootstrap metric, and droop flag. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: restore: On each rising `clk` edge while enabled, capture `vin` into `vhold`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.
- `P_EXPOSE_A_BOOT_METRIC_THAT_INCREASES`: restore: Expose a `boot_metric` that increases when the sampled input is near the rails and decreases near common-mode. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.
- `P_BETWEEN_SAMPLES_HOLD_VHOLD_AND_APPLY`: restore: Between samples, hold `vhold` and apply a bounded droop step toward `vcm`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.
- `P_ASSERT_DROOP_FLAG_WHEN_ACCUMULATED_HOLD`: restore: Assert `droop_flag` when accumulated hold error exceeds `droop_tol`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `vhold`, `boot_metric`, `droop_flag`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bootstrapped_sampler_charge_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
