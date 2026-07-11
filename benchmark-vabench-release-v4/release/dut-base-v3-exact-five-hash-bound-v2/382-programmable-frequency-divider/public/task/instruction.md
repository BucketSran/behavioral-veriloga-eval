# Programmable Frequency Divider

## Task Contract

Implement one Verilog-A DUT artifact for `Programmable Frequency Divider`.

- Target artifact: `programmable_frequency_divider.va`
- Public top module: `programmable_frequency_divider`
- Task level: `L1`
- Circuit category: `clock_timing`

## Public Verilog-A Interface

Declare module `programmable_frequency_divider` with positional electrical ports `clk_in, rst, enable, n_3, n_2, n_1, n_0, clk_div, ratio_metric, valid`. All ports are electrical.

`n_3..n_0` form a sampled unsigned divide-control code with `n_0` as the least significant bit. `clk_div` toggles after the programmed number of enabled input-clock rising edges.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic-high output level
- `vss = 0.0 V`: logic-low output level
- `vth = 0.45 V`: logic threshold
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or low `enable` clears the divider state, `clk_div`, `ratio_metric`, and `valid`.
- On each enabled rising `clk_in` edge, sample the four control bits and form divisor `N = code + 1`.
- Toggle `clk_div` whenever `N` enabled input-clock rising edges have been counted.
- `ratio_metric` exposes the sampled divisor as a voltage-coded fraction of the 1-to-16 range.
- `valid` is high after the first divider toggle and low before that or during reset/disable.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `programmable_frequency_divider.va`.
