# Quadrature Oscillator Phase-error Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Quadrature Oscillator Phase-error Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `quadrature_oscillator_phase_error_monitor.va`:
  - Module `quadrature_oscillator_phase_error_monitor` (entry)
    - position 0: `clk_i` (inout, electrical)
    - position 1: `clk_q` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `phase_error_metric` (inout, electrical)
    - position 5: `quadrature_ok` (inout, electrical)
    - position 6: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `quadrature_oscillator_phase_error_monitor` as `XDUT` with ordered public binding: clk_i=clk_i, clk_q=clk_q, rst=rst, enable=enable, phase_error_metric=phase_error_metric, quadrature_ok=quadrature_ok, valid=valid.

## Public Parameter Contract

- `quadrature_oscillator_phase_error_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `quadrature_oscillator_phase_error_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `quadrature_oscillator_phase_error_monitor.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `quadrature_oscillator_phase_error_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `quadrature_oscillator_phase_error_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `quadrature_oscillator_phase_error_monitor.phase_tol` defaults to `60e-3`; valid range: finite; overrides phase_tol.
- `quadrature_oscillator_phase_error_monitor.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear phase metric, status, and `valid`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_TRACK_RISING_THRESHOLD_CROSSINGS_OF_CLK`: exercise and make observable: Track rising threshold crossings of `clk_i` and `clk_q`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ESTIMATE_A_VOLTAGE_DOMAIN_PHASE_ERROR`: exercise and make observable: Estimate a voltage-domain phase-error metric from the relative event order and interval proxy. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ASSERT_QUADRATURE_OK_WHEN_THE_MEASURED`: exercise and make observable: Assert `quadrature_ok` when the measured phase proxy stays within `phase_tol` for two cycles. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.
- `P_ASSERT_VALID_AFTER_BOTH_I_AND`: exercise and make observable: Assert `valid` after both I and Q edges have been observed. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.

The required trace names are: `time`, `clk_i`, `clk_q`, `rst`, `enable`, `phase_error_metric`, `quadrature_ok`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
