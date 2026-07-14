# Accum3 Pulse

## Task Contract

Implement `accum3_pulse.va` as a 3-bit modulo accumulator pulse generator.

## Public Verilog-A Interface

Use this module signature:

```verilog
module accum3_pulse(clk, out);
```

Both ports are scalar `electrical` nodes. `clk` is the input clock and `out` is the voltage-coded modulo pulse output.

## Public Parameter Contract

- `vth`: rising-edge threshold for `clk`, default `0.45`.
- `vdd`: high level for the output, default `0.9`.
- `tdel`: output transition delay, default `10p`.
- `tr`: output rise/fall smoothing time, default `10p`.

## Required Behavior

- Initialize the internal 3-bit count to 7.
- Increment the count modulo 8 on each rising `clk` crossing.
- Drive `out` high only when the modulo count is 0.
- Drive `out` low for all other count values.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, transistor-level devices, AC/noise analysis, checker logic, out-of-band test hooks, or simulator side channels.

## Output Contract

Return exactly one source artifact named `accum3_pulse.va`.
