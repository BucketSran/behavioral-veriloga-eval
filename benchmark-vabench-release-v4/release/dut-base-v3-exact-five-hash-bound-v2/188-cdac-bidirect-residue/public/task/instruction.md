# CDAC Bidirectional Residue

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter CDAC residue model.
- Target artifact: `cdac_bidirect_residue.va`.
- Role: sampled CDAC residue with bidirectional switching events.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module cdac_bidirect_residue(vin, clks, dctrl1, dctrl2, dctrl3, dctrl4, dctrl5, dctrl6, dctrl7, vres);
```

`vin` is the sampled analog input, `clks` is the sampling clock, `dctrl1..dctrl7` are voltage-coded control edges, and `vres` is the residue output. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Use a 0.5 V threshold for clock/control events and a 1 V normalized CDAC reference span.

## Required Behavior

At initialization and on each falling `clks` crossing, sample `vin` into the residue state. When `dctrl7` falls, add the half-scale MSB residue step. When `dctrl6` through `dctrl1` rise, subtract binary-weighted residue steps from MSB toward LSB. Continuously drive `vres` from the current residue state and hold it between events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `cdac_bidirect_residue.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
