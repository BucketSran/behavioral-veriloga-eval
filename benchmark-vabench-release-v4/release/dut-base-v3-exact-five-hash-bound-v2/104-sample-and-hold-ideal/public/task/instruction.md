# Ideal Sample And Hold

## Task Contract

Implement the single-DUT Verilog-A artifact `source_sample_hold.va` for an ideal
voltage-domain sample-and-hold primitive. The model should capture an analog
input on clock events and hold the sampled value between events.

## Public Verilog-A Interface

The file `source_sample_hold.va` must define:

```verilog
module source_sample_hold(vin, vout, vclk);
```

All ports are electrical. `vin` is the analog input, `vclk` is the sampling
clock, and `vout` is the held analog output.

## Public Parameter Contract

- `vtrans_clk = 0.45 V`: rising-clock threshold.
- `tr = 20p`: transition smoothing time for `vout`.

These parameters may be overridden by the validation harness.

## Required Behavior

On each rising crossing of `vclk` through `vtrans_clk`, sample the instantaneous
input voltage `V(vin)`. Hold that sampled value until the next rising sampling
event and drive it on `vout`.

## Modeling Constraints

Use voltage-domain event-driven Verilog-A and voltage contributions only. Do
not use current contributions, transistor-level devices, `ddt()`, `idt()`,
validation logic, auxiliary test hooks, or testbench-specific timing constants
inside the DUT.

## Output Contract

Return exactly one complete Verilog-A source artifact named
`source_sample_hold.va`. Do not include explanatory prose outside the source
artifact contents.
