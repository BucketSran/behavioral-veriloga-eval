# LT Readout SAR4

## Task Contract

Implement `lt_readout_sar4.va` as a continuous 4-bit SAR readout DAC DUT.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module lt_readout_sar4(d0, d1, d2, d3, vout, gnd);
```

All ports are electrical. `d0` is the least significant bit, `d3` is the most significant bit, `vout` is the analog readout, and `gnd` is the supplied reference node.

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vth` | `0.9` | Logic threshold for `d0..d3`. |
| `vref` | `1.8` | Full-scale voltage reference for the unsigned readout. |

## Required Behavior

Continuously decode `d0..d3` as an unsigned binary code with `d0` as LSB and `d3` as MSB. Drive `vout` to the readout level `code * vref / 16`. The output should update when the voltage-coded input bits cross the threshold.

## Modeling Constraints

Use voltage contributions only. Do not add clocked state, current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times.

## Output Contract

Return exactly one source artifact named `lt_readout_sar4.va`.
