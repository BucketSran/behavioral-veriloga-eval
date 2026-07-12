# Quadrature Phase Interpolator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `quadrature_phase_interpolator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `quadrature_phase_interpolator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `quadrature_phase_interpolator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `quadrature_phase_interpolator.unit_delay` defaults to `5e-12`; valid range: finite; overrides unit_delay.
- `quadrature_phase_interpolator.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.
- `quadrature_phase_interpolator.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_CLEAR_CLK_OUT_QUADRANT`: restore: On reset, clear `clk_out`, quadrant outputs, and `phase_metric`. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_OBSERVE_THE_RISING_EDGES_OF_CLK`: restore: Observe the rising edges of `clk_i` and `clk_q` and maintain a four-quadrant phase reference. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_DECODE_CODE_4_CODE_0_AS`: restore: Decode `code_4..code_0` as an unsigned phase code from 0 to 31. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_GENERATE_CLK_OUT_EDGES_DELAYED_FROM`: restore: Generate `clk_out` edges delayed from the selected quadrant reference by `unit_delay` times the intra-quadrant code. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_QUADRANT_1_QUADRANT_0_MUST_EXPOSE`: restore: `quadrant_1..quadrant_0` must expose the selected quadrant. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.
- `P_PHASE_METRIC_MUST_EXPOSE_THE_DECODED`: restore: `phase_metric` must expose the decoded phase code as a voltage-level metric. Required traces: `time`, `clk_i`, `clk_q`, `rst`, `code_4`, `code_0`, `clk_out`, `quadrant_1`, `quadrant_0`, `phase_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `quadrature_phase_interpolator.va`.
Every supplied `.va` file is editable; do not add or omit files.
