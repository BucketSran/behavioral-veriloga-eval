# SAR CDAC Residue

## Task Contract

Implement the requested Verilog-A artifact for `SAR CDAC Residue`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter_models`
- Target artifact(s): `sar_cdac_residue.va`

Implement the Verilog-A DUT `sar_cdac_residue.va` for a sampled SAR capacitive-DAC residue update model.

This is a data-converter support DUT. The testbench supplies switching events; the DUT must implement the residue state machine implied by the public ports and parameters.

## Public Verilog-A Interface

Provide `module sar_cdac_residue(VIN, CLK, S6, S5, S4, S3, S2, S1, VRES);` with electrical inputs `VIN`, `CLK`, `S6` through `S1`, and electrical output `VRES`.

## Public Parameter Contract

Expose `vdd = 0.9`, `vrefp = 0.9`, `vrefn = 0.0`, and output transition time
`tr = 1p`. Testbenches may override these parameters. The decision threshold
for `CLK` and all `S1` through `S6` switching inputs is `vdd/2`.

## Required Behavior

Sample `VIN` into the residue at `initial_step` and on each rising `CLK`
crossing at `vdd/2`. A falling `S6` crossing through `vdd/2` adds one half of
the reference span. Rising `S5`, `S4`, `S3`, `S2`, and `S1` crossings through
`vdd/2` subtract one fourth, one eighth, one sixteenth, one thirty-second, and
one sixty-fourth of the reference span respectively. Drive `VRES` from the
current residue state.

## Modeling Constraints

Use event-driven state updates with Spectre-compatible `cross` behavior and drive `VRES` with an explicit transition time. Preserve the specified edge directions and binary residue weights; do not omit the least-significant step.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Submit only the completed Verilog-A module in `sar_cdac_residue.va`.
