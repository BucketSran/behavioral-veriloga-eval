# Programmable Frequency Divider Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `programmable_frequency_divider.va`:
  - Module `programmable_frequency_divider` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `n_3` (input, electrical)
    - position 4: `n_2` (input, electrical)
    - position 5: `n_1` (input, electrical)
    - position 6: `n_0` (input, electrical)
    - position 7: `clk_div` (output, electrical)
    - position 8: `ratio_metric` (output, electrical)
    - position 9: `valid` (output, electrical)

## Public Parameter Contract

- `programmable_frequency_divider.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `programmable_frequency_divider.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `programmable_frequency_divider.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `programmable_frequency_divider.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_LOW_ENABLE_CLEARS_THE`: restore: Reset or low `enable` clears the divider state, `clk_div`, `ratio_metric`, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_IN`: restore: On each enabled rising `clk_in` edge, sample the four control bits and form divisor `N = code + 1`. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_TOGGLE_CLK_DIV_WHENEVER_N_ENABLED`: restore: Toggle `clk_div` whenever `N` enabled input-clock rising edges have been counted. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_RATIO_METRIC_EXPOSES_THE_SAMPLED_DIVISOR`: restore: `ratio_metric` exposes the sampled divisor as a voltage-coded fraction of the 1-to-16 range. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_VALID_IS_HIGH_AFTER_THE_FIRST`: restore: `valid` is high after the first divider toggle and low before that or during reset/disable. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `programmable_frequency_divider.va`.
Every supplied `.va` file is editable; do not add or omit files.
