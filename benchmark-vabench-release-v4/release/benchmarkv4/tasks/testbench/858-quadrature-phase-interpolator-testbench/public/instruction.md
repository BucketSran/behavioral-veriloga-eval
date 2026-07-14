# Quadrature Phase Interpolator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Quadrature Phase Interpolator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `quadrature_phase_interpolator.va`:
  - Module `quadrature_phase_interpolator` (entry)
    - position 0: `clk_i` (inout, electrical)
    - position 1: `clk_q` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `code_4` (inout, electrical)
    - position 4: `code_3` (inout, electrical)
    - position 5: `code_2` (inout, electrical)
    - position 6: `code_1` (inout, electrical)
    - position 7: `code_0` (inout, electrical)
    - position 8: `clk_out` (inout, electrical)
    - position 9: `quadrant_1` (inout, electrical)
    - position 10: `quadrant_0` (inout, electrical)
    - position 11: `phase_metric` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `quadrature_phase_interpolator` as `XDUT` with ordered public binding: clk_i=clk_i, clk_q=clk_q, rst=rst, code_4=code_4, code_3=code_3, code_2=code_2, code_1=code_1, code_0=code_0, clk_out=clk_out, quadrant_1=quadrant_1, quadrant_0=quadrant_0, phase_metric=phase_metric.

## Public Parameter Contract

- `quadrature_phase_interpolator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `quadrature_phase_interpolator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `quadrature_phase_interpolator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `quadrature_phase_interpolator.unit_delay` defaults to `5e-12`; valid range: finite; overrides unit_delay.
- `quadrature_phase_interpolator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.
- `quadrature_phase_interpolator.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_CLEAR_CLK_OUT_QUADRANT`: exercise and make observable: On reset, clear `clk_out`, quadrant outputs, and `phase_metric`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_OBSERVE_THE_RISING_EDGES_OF_CLK`: exercise and make observable: Observe the rising edges of `clk_i` and `clk_q` and maintain a four-quadrant phase reference. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_DECODE_CODE_4_CODE_0_AS`: exercise and make observable: Decode `code_4..code_0` as an unsigned phase code from 0 to 31. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_GENERATE_CLK_OUT_EDGES_DELAYED_FROM`: exercise and make observable: Generate `clk_out` edges delayed from the selected quadrant reference by `unit_delay` times the intra-quadrant code. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_QUADRANT_1_QUADRANT_0_MUST_EXPOSE`: exercise and make observable: `quadrant_1..quadrant_0` must expose the selected quadrant. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_PHASE_METRIC_MUST_EXPOSE_THE_DECODED`: exercise and make observable: `phase_metric` must expose the decoded phase code as a voltage-level metric. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.

The required trace names are: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`, `code_3`, `code_2`, `code_1`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
