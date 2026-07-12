# Burst Clock Source

## Task Contract

Implement the requested Verilog-A artifact for `Burst Clock Source`.
- Form: `dut`
- Level: `L1`
- Category: `stimulus_source_generators`
- Target artifact(s): `clk_burst_gen.va`

Implement `clk_burst_gen.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `clk_burst_gen` with positional ports `CLK, RST_N, CLK_OUT`.
All ports are electrical.

## Public Parameter Contract

- `div = 8`: burst repeat period in input-clock cycles. Values below 3 are out
  of contract.
- `vdd = 0.9 V`: high output level.
- `vth = 0.45 V`: clock and reset threshold.

## Required Behavior

`RST_N` is an active-low reset. While reset is asserted, restart the burst
cycle counter and drive `CLK_OUT` low. After reset is released, detect rising
crossings of `CLK` through `vth`. In each `div`-cycle frame, pass the input
clock waveform to `CLK_OUT` for frame positions 0 and 1, then hold `CLK_OUT`
low for the remaining frame positions. Repeat this frame pattern indefinitely.

Use voltage-domain event logic such as `@(cross(...,+1))`/`@(cross(...,-1))`
and drive the output with `transition(...)`.

## Modeling Constraints

Return only `clk_burst_gen.va`. Do not generate a the simulator example harness or validation harness
logic. Do not use current contributions, `ddt()`, `idt()`, transistor-level
devices, AC/noise analysis, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `clk_burst_gen.va`. Do not include explanatory prose outside the source artifact contents.
