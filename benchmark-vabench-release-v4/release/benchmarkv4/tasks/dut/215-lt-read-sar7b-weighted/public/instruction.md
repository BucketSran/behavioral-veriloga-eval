# LT Read SAR7B Weighted

## Task Contract

Implement `lt_read_sar7b_weighted.va` as a continuous 8-input weighted SAR readout DUT.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module lt_read_sar7b_weighted(d0, d1, d2, d3, d4, d5, d6, d7, vout, gnd);
```

All ports are electrical. `d7` is the most significant weighted input, `d0` is the least significant weighted input, `vout` is the analog output, and `gnd` is the supplied reference node.

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vth` | `0.45` | Logic threshold for `d7..d0`. |
| `vref` | `0.9` | Bipolar offset and weighting reference. |

## Required Behavior

Continuously drive:

```text
vout = -vref + vref * (d7 + d6/2 + d5/4 + d4/8 + d3/16 + d2/32 + d1/64 + d0/128)
```

where each `d` term is `1` when the corresponding input voltage is above `vth` and `0` otherwise.

## Modeling Constraints

Use voltage-domain Verilog-A only. Do not add clocked state, current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times.

## Output Contract

Return exactly one source artifact named `lt_read_sar7b_weighted.va`.
