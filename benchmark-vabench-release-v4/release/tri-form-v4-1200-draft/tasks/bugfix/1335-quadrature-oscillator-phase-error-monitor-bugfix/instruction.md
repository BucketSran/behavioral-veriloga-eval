# Quadrature Oscillator Phase-error Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `quadrature_oscillator_phase_error_monitor.va`:
  - Module `quadrature_oscillator_phase_error_monitor` (entry)
    - position 0: `clk_i` (inout, electrical)
    - position 1: `clk_q` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `phase_error_metric` (inout, electrical)
    - position 5: `quadrature_ok` (inout, electrical)
    - position 6: `valid` (inout, electrical)

## Public Parameter Contract

- `quadrature_oscillator_phase_error_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `quadrature_oscillator_phase_error_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `quadrature_oscillator_phase_error_monitor.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `quadrature_oscillator_phase_error_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `quadrature_oscillator_phase_error_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `quadrature_oscillator_phase_error_monitor.phase_tol` defaults to `60e-3`; valid range: finite; overrides phase_tol.
- `quadrature_oscillator_phase_error_monitor.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear phase metric, status, and `valid`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_TRACK_RISING_THRESHOLD_CROSSINGS_OF_CLK`: restore: Track rising threshold crossings of `clk_i` and `clk_q`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ESTIMATE_A_VOLTAGE_DOMAIN_PHASE_ERROR`: restore: Estimate a voltage-domain phase-error metric from the relative event order and interval proxy. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ASSERT_QUADRATURE_OK_WHEN_THE_MEASURED`: restore: Assert `quadrature_ok` when the measured phase proxy stays within `phase_tol` for two cycles. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ASSERT_VALID_AFTER_BOTH_I_AND`: restore: Assert `valid` after both I and Q edges have been observed. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `quadrature_oscillator_phase_error_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
