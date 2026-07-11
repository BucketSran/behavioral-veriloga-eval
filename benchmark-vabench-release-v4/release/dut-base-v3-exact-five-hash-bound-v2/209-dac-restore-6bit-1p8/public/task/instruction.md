# DAC Restore 6bit 1p8

## Task Contract

Implement `dac_restore_6bit_1p8.va` as a clocked 6-bit restore DAC DUT. The task is an L1 data-converter component with a 1.8 V logic domain and a bipolar mid-rise output mapping.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module dac_restore_6bit_1p8(d1, d2, d3, d4, d5, d6, clk, vout);
```

All ports are electrical. `d1` is the most significant decision bit, `d6` is the least significant decision bit, `clk` is the sample clock, and `vout` is the restored analog output.

## Public Parameter Contract

Provide `parameter real vth = 0.9;` as the logic threshold for `clk` and all decision-bit inputs.

## Required Behavior

On each rising crossing of `clk` through `vth`, sample `d1..d6` and decode an unsigned 6-bit code with weights `32, 16, 8, 4, 2, 1`. Hold the decoded output until the next rising clock event. Map the sampled code to a bipolar 1.8 V mid-rise level:

```text
vout = (code + 0.5) * 3.6 / 64 - 1.8
```

The all-zero code therefore produces the lowest half-LSB-centered negative level, and the all-one code produces the highest half-LSB-centered positive level.

## Modeling Constraints

Use event-driven voltage-domain Verilog-A. Do not continuously track bit changes between clock events. Do not add current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times.

## Output Contract

Return exactly one source artifact named `dac_restore_6bit_1p8.va`.
