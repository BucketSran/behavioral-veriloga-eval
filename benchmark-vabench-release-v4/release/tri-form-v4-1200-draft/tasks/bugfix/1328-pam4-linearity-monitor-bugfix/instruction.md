# PAM4 Linearity Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pam4_linearity_monitor.va`:
  - Module `pam4_linearity_monitor` (entry)
    - position 0: `symbol_1` (inout, electrical)
    - position 1: `symbol_0` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `level_out` (inout, electrical)
    - position 6: `linearity_metric` (inout, electrical)
    - position 7: `valid` (inout, electrical)

## Public Parameter Contract

- `pam4_linearity_monitor.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `pam4_linearity_monitor.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `pam4_linearity_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pam4_linearity_monitor.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `pam4_linearity_monitor.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear output, metric, and `valid`. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, decode `symbol_1..symbol_0` as one of four PAM4 levels. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_DRIVE_LEVEL_OUT_TO_EVENLY_SPACED`: restore: Drive `level_out` to evenly spaced voltage levels between `vss` and `vdd`. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_EXPOSE_A_LINEARITY_METRIC_THAT_IS`: restore: Expose a `linearity_metric` that is high only when adjacent level spacing is uniform. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_EACH_SAMPLED_SYMBOL`: restore: Assert `valid` after each sampled symbol update. Required traces: `time`, `symbol_1`, `symbol_0`, `clk`, `rst`, `enable`, `level_out`, `linearity_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pam4_linearity_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
