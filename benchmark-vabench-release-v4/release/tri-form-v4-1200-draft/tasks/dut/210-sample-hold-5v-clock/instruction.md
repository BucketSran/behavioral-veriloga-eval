# Sample-Hold With 5 V Clock

## Task Contract

Implement `sample_hold_5v_clock.va` as an ideal rising-edge sample-and-hold DUT controlled by a 5 V clock.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module sample_hold_5v_clock(vin, vout, vclk);
```

All ports are electrical. `vin` is the analog input, `vclk` is the sampling clock, and `vout` is the held output.

## Public Parameter Contract

Provide `parameter real vtrans_clk = 2.5;` as the rising-edge threshold for the 5 V clock.

## Required Behavior

Detect rising crossings of `vclk` through `vtrans_clk`. At each qualifying edge, sample the instantaneous value of `vin` and hold that sampled value on `vout` until the next rising clock edge. Falling clock edges must not update the held value.

## Modeling Constraints

Use voltage contributions only. Do not continuously track `vin` between sampling edges. Do not add current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times.

## Output Contract

Return exactly one source artifact named `sample_hold_5v_clock.va`.
