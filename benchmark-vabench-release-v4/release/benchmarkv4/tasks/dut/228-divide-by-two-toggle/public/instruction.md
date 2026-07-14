# Divide By Two Toggle

## Task Contract

Implement `divide_by_two_toggle.va` as a voltage-domain divide-by-two edge toggle.

## Public Verilog-A Interface

Use this module signature:

```verilog
module divide_by_two_toggle(clk, out);
```

Both ports are scalar `electrical` nodes. `clk` is the input clock and `out` is the divided output.

## Public Parameter Contract

- `vth`: rising-edge decision threshold for `clk`, default `0.45`.
- `vdd`: high output level, default `0.9`.
- `tdel`: output transition delay, default `10p`.
- `tr`: output rise/fall transition time, default `10p`.

## Required Behavior

- Initialize the internal divider state low.
- Toggle the state on every rising `clk` crossing through `vth`.
- Drive `out` low when the state is low and to `vdd` when the state is high.
- The first valid rising edge drives `out` high.

## Modeling Constraints

Use voltage contributions only. Do not emit a support testbench, add checker logic, hard-code testbench waveform sample points, add simulator side channels, use current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `divide_by_two_toggle.va`.
