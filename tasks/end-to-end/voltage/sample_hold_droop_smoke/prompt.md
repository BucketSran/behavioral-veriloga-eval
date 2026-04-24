Write a Verilog-A module named `sample_hold_droop_ref` and one minimal EVAS-compatible Spectre testbench.

# Task: sample_hold_droop_smoke

## Objective

Create a pure voltage-domain sample-and-hold model with observable hold droop. The testbench must
produce several sampling and hold windows so EVAS can measure droop behavior.

## DUT Contract

- Module name: `sample_hold_droop_ref`
- Ports, all `electrical`, exactly in this order: `vdd`, `vss`, `clk`, `vin`, `vout`
- Parameters:
  - `vth` real, default `0.45`
  - `tau` real, default `120n`
  - `dt` real, default `0.5n`
  - `trf` real, default `40p`
- Behavior:
  - Sample `V(vin)` on each rising edge of `clk`.
  - Between rising edges, hold the sampled value while adding finite droop toward `V(vss)`.
  - Output should remain in the supply range.
  - Use `@(cross(V(clk) - vth, +1))` and `transition(...)`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `clk` with enough rising edges inside the final validation window to create multiple hold intervals.
- Drive `vin` through several distinct levels so the held output changes between samples.
- Instantiate the DUT by positional ports.
- Save these exact scalar names: `vin`, `clk`, `vout`.
- Include the generated DUT file `sample_hold_droop_ref.va`.
- Use the final transient setting provided by the injected Strict EVAS Validation Contract.

## Deliverables

Return exactly two fenced code blocks:

1. `sample_hold_droop_ref.va`
2. `tb_sample_hold_droop.scs`
