# SUM5 Signed SAR Weight

## Task Contract

Implement `sum5_signed_sar_weight.va` as a continuous signed SAR weighted-sum DUT. The row models a small signed reconstruction helper used in SAR-style readout paths.

## Public Verilog-A Interface

Use this exact module signature:

```verilog
module sum5_signed_sar_weight(d1, d2, d3, d4, d5, out);
```

All ports are electrical. `d1..d5` are voltage-coded decision inputs and `out` is the analog weighted-sum output.

## Public Parameter Contract

Provide `parameter real vth = 0.55;` as the logic threshold for all decision inputs. The output scale is the public fixed scale used by this source-normalized row: `1.1 V`.

## Required Behavior

Treat each decision input as `+1` when its voltage is above `vth` and `-1` otherwise. Combine the signed decisions with SAR weights `d5 = 1/2`, `d4 = 1/4`, `d3 = 1/8`, `d2 = 1/16`, and `d1 = 1/32`. Drive `out` to the scaled signed reconstruction:

```text
out = 1.1 * (2 * signed_weighted_sum - 1)
```

The behavior is continuous with respect to the voltage-coded decision inputs after thresholding.

## Modeling Constraints

Use voltage-domain Verilog-A only. Do not add clocked state, current contributions, transistor devices, checker logic, out-of-band test hooks, simulator side channels, or hard-coded testbench sample times.

## Output Contract

Return exactly one source artifact named `sum5_signed_sar_weight.va`.
