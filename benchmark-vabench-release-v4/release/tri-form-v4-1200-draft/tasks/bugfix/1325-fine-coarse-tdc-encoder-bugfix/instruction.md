# Fine/coarse TDC Encoder Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fine_coarse_tdc_encoder_top.va`:
  - Module `fine_coarse_tdc_encoder_top` (entry)
    - position 0: `start` (inout, electrical)
    - position 1: `stop` (inout, electrical)
    - position 2: `ref_clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `coarse_3` (inout, electrical)
    - position 6: `coarse_2` (inout, electrical)
    - position 7: `coarse_1` (inout, electrical)
    - position 8: `coarse_0` (inout, electrical)
    - position 9: `fine_metric` (inout, electrical)
    - position 10: `valid` (inout, electrical)
- Artifact `coarse_counter.va`:
  - Module `coarse_counter` (required_submodule)
    - position 0: `a` (inout, electrical)
    - position 1: `b` (inout, electrical)
- Artifact `fine_residual_metric.va`:
  - Module `fine_residual_metric` (required_submodule)
    - position 0: `a` (inout, electrical)
    - position 1: `b` (inout, electrical)

## Public Parameter Contract

- `fine_coarse_tdc_encoder_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `fine_coarse_tdc_encoder_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `fine_coarse_tdc_encoder_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `fine_coarse_tdc_encoder_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `fine_coarse_tdc_encoder_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `coarse_counter.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `fine_residual_metric.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear coarse code, fine metric, and `valid`. Required traces: `time`, `start`, `stop`, `ref_clk`, `rst`, `enable`, `coarse_3`, `coarse_2`, `coarse_1`, `coarse_0`, `fine_metric`, `valid`.
- `P_A_RISING_START_EDGE_ARMS_A`: restore: A rising `start` edge arms a measurement and clears the coarse counter. Required traces: `time`, `start`, `stop`, `ref_clk`, `rst`, `enable`, `coarse_3`, `coarse_2`, `coarse_1`, `coarse_0`, `fine_metric`, `valid`.
- `P_COUNT_RISING_REF_CLK_EDGES_UNTIL`: restore: Count rising `ref_clk` edges until the first rising `stop` edge. Required traces: `time`, `start`, `stop`, `ref_clk`, `rst`, `enable`, `coarse_3`, `coarse_2`, `coarse_1`, `coarse_0`, `fine_metric`, `valid`.
- `P_LATCH_THE_COARSE_COUNT_INTO_COARSE`: restore: Latch the coarse count into `coarse_3..coarse_0` and expose a fine residual proxy on `fine_metric`. Required traces: `time`, `start`, `stop`, `ref_clk`, `rst`, `enable`, `coarse_3`, `coarse_2`, `coarse_1`, `coarse_0`, `fine_metric`, `valid`.
- `P_ASSERT_VALID_ONLY_AFTER_THE_STOP`: restore: Assert `valid` only after the stop edge completes the measurement. Required traces: `time`, `start`, `stop`, `ref_clk`, `rst`, `enable`, `coarse_3`, `coarse_2`, `coarse_1`, `coarse_0`, `fine_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fine_coarse_tdc_encoder_top.va`, `coarse_counter.va`, `fine_residual_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
