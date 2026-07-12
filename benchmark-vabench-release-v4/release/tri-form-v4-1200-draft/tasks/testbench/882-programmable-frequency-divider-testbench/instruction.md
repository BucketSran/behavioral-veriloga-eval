# Programmable Frequency Divider Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Programmable Frequency Divider` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `programmable_frequency_divider` as `XDUT` with ordered public binding: clk_in=clk_in, rst=rst, enable=enable, n_3=n_3, n_2=n_2, n_1=n_1, n_0=n_0, clk_div=clk_div, ratio_metric=ratio_metric, valid=valid.

## Public Parameter Contract

- `programmable_frequency_divider.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `programmable_frequency_divider.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `programmable_frequency_divider.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `programmable_frequency_divider.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_LOW_ENABLE_CLEARS_THE`: exercise and make observable: Reset or low `enable` clears the divider state, `clk_div`, `ratio_metric`, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_IN`: exercise and make observable: On each enabled rising `clk_in` edge, sample the four control bits and form divisor `N = code + 1`. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_TOGGLE_CLK_DIV_WHENEVER_N_ENABLED`: exercise and make observable: Toggle `clk_div` whenever `N` enabled input-clock rising edges have been counted. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_RATIO_METRIC_EXPOSES_THE_SAMPLED_DIVISOR`: exercise and make observable: `ratio_metric` exposes the sampled divisor as a voltage-coded fraction of the 1-to-16 range. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.
- `P_VALID_IS_HIGH_AFTER_THE_FIRST`: exercise and make observable: `valid` is high after the first divider toggle and low before that or during reset/disable. Required traces: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.

The required trace names are: `time`, `clk_in`, `rst`, `enable`, `n_3`, `n_2`, `n_1`, `n_0`, `clk_div`, `ratio_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
