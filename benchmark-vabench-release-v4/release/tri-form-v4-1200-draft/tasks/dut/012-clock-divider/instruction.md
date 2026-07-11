# PLL Feedback Clock Divider

## Task Contract

Implement the requested Verilog-A artifact for `Clock Divider`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `clk_divider_ref.va`

Implement `clk_divider_ref.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module clk_divider_ref (
    input  electrical clk_in,
    input  electrical rst_n,
    input  electrical div_code_0,
    input  electrical div_code_1,
    input  electrical div_code_2,
    input  electrical div_code_3,
    input  electrical div_code_4,
    input  electrical div_code_5,
    input  electrical div_code_6,
    input  electrical div_code_7,
    output electrical clk_out,
    output electrical lock
);
```

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Unit / Range | Contract |
| --- | ---: | --- | --- |
| `vdd` | `0.9` | V, `(0:inf)` | High level for voltage-coded outputs. |
| `vth` | `0.45` | V | Logic threshold for clock, reset, and ratio-code inputs. |
| `trf` | `10 ps` | time, `(0:inf)` | Rise/fall smoothing for `clk_out` and `lock`. |
| `td` | `0 ps` | time, `[0:inf)` | Transition delay for voltage-coded outputs. |

## Required Behavior

The module is a resettable, voltage-domain PLL/ADPLL feedback divider with an 8-bit programmable ratio code and a lock indicator.

- Treat all inputs and outputs as electrical voltage-domain signals.
- Interpret `rst_n` as active-low reset. While reset is low, clear the divider
  state and drive `clk_out` and `lock` low.
- Decode `div_code_0` through `div_code_7` as an unsigned 8-bit LSB-first
  voltage-coded ratio. Code 0 maps to divide ratio 1.
- For divide ratio 1, reproduce the input clock activity on `clk_out` and
  assert `lock` after the first valid post-reset clock cycle.
- For divide ratios greater than 1, generate a periodic divided clock whose
  rising-to-rising output period spans the decoded number of input rising
  edges after startup.
- For odd divide ratios, use floor/ceil segment lengths so both high and low
  phases are present and the long segment differs by at most one input cycle
  from the short segment.
- Assert `lock` only after the first complete output period for the current
  decoded ratio. If the ratio code changes after reset, clear divider phase and
  `lock`, then reacquire using the new ratio.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `clk_divider_ref.va`.
