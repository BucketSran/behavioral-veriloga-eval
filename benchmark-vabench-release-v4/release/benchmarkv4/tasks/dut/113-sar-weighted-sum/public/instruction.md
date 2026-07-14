# SAR Weighted Sum

## Task Contract

Implement the requested Verilog-A artifact for `SAR Weighted Sum`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `sar_weighted_sum.va`

Implement `sar_weighted_sum.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `sar_weighted_sum(D10, D9, D8, D7, D6, D5, D4, D3, D2, D1, D0,
VOUT)` with scalar electrical voltage-domain ports. `D10` is the most
significant decision input and `D0` is the least significant decision input.

## Public Parameter Contract

Provide this overrideable public parameter:

- `vth = 0.45 V`: digital decision threshold for each input.

## Required Behavior

- Treat each `D*` input as logic `1` when its voltage is greater than `vth`,
  otherwise logic `0`.
- Implement a continuous SAR residue/source weighting law:
  - `D10` is the coarse residue bit with a seven-eighths full-scale weight.
  - `D9` and `D8` continue with half-scale and quarter-scale weights.
  - `D7` and `D6` split the next binary step in a 5:3 ratio to model a
    redundant SAR decision boundary.
  - `D5` through `D0` continue as the binary tail down to the unit LSB.
- Normalize the accumulated residue on a 512-unit bipolar scale so that all
  inputs low produce `-1 V`, the output is monotonic with added decision weight,
  and all inputs high land one 512-unit step below `+1 V`.
- Drive `VOUT` continuously from the decoded voltage-domain decision inputs.

## Modeling Constraints

Return only `sar_weighted_sum.va`. Do not emit a testbench, validation harness
logic, validation-only hooks, hard-coded validation-only sample points, or
simulator-specific side channels. Use voltage contributions only; do not use
current contributions, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `sar_weighted_sum.va`. Do not include explanatory prose outside the source artifact contents.
