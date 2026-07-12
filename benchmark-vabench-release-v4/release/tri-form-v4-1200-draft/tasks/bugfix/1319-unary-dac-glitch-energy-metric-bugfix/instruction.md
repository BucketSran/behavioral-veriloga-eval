# Unary DAC Glitch-energy Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `unary_dac_glitch_energy_metric.va`:
  - Module `unary_dac_glitch_energy_metric` (entry)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `code_2` (inout, electrical)
    - position 4: `code_1` (inout, electrical)
    - position 5: `code_0` (inout, electrical)
    - position 6: `vout` (inout, electrical)
    - position 7: `glitch_metric` (inout, electrical)
    - position 8: `valid` (inout, electrical)

## Public Parameter Contract

- `unary_dac_glitch_energy_metric.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `unary_dac_glitch_energy_metric.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `unary_dac_glitch_energy_metric.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `unary_dac_glitch_energy_metric.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `unary_dac_glitch_energy_metric.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear output, previous code, glitch metric, and `valid`. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, decode the 3-bit code as a unary element count. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.
- `P_DRIVE_VOUT_PROPORTIONAL_TO_THE_DECODED`: restore: Drive `vout` proportional to the decoded count. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.
- `P_DRIVE_GLITCH_METRIC_PROPORTIONAL_TO_THE`: restore: Drive `glitch_metric` proportional to the absolute change in count since the previous enabled update. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_ENABLED`: restore: Assert `valid` after the first enabled code update. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `clk`, `rst`, `enable`, `code_2`, `code_1`, `code_0`, `vout`, `glitch_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `unary_dac_glitch_energy_metric.va`.
Every supplied `.va` file is editable; do not add or omit files.
