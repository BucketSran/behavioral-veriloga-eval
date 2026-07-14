# Fixed-frequency Oscillator Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fixed_frequency_oscillator_source.va`:
  - Module `fixed_frequency_oscillator_source` (entry)
    - position 0: `enable` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `osc_out` (inout, electrical)
    - position 3: `period_metric` (inout, electrical)
    - position 4: `valid` (inout, electrical)

## Public Parameter Contract

- `fixed_frequency_oscillator_source.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `fixed_frequency_oscillator_source.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `fixed_frequency_oscillator_source.period` defaults to `20e-9`; valid range: finite; overrides period.
- `fixed_frequency_oscillator_source.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `fixed_frequency_oscillator_source.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `fixed_frequency_oscillator_source.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `osc_out`, `period_metric`, and `valid` low. Required traces: `time`, `enable`, `rst`, `osc_out`, `period_metric`, `valid`.
- `P_WHEN_ENABLED_GENERATE_A_PERIODIC_VOLTAGE`: restore: When enabled, generate a periodic voltage-domain clock that toggles between `vss` and `vdd` with the configured period. Required traces: `time`, `enable`, `rst`, `osc_out`, `period_metric`, `valid`.
- `P_PERIOD_METRIC_MUST_EXPOSE_A_STABLE`: restore: `period_metric` must expose a stable voltage-coded representation of the configured period after the first complete cycle. Required traces: `time`, `enable`, `rst`, `osc_out`, `period_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_COMPLETE`: restore: Assert `valid` after the first complete oscillator cycle following enable. Required traces: `time`, `enable`, `rst`, `osc_out`, `period_metric`, `valid`.
- `P_RESET_OR_DISABLE_MUST_RESTART_THE`: restore: Reset or disable must restart the oscillator phase deterministically. Required traces: `time`, `enable`, `rst`, `osc_out`, `period_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fixed_frequency_oscillator_source.va`.
Every supplied `.va` file is editable; do not add or omit files.
