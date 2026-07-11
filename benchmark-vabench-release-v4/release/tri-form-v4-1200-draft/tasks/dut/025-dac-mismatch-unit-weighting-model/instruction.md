# DAC Mismatch Unit Weighting Model

## Task Contract

Implement the requested Verilog-A artifact for `DAC Mismatch Unit Weighting Model`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `dac_mismatch_unit_weighting_model.va`

Implement a bounded 4-bit DAC with explicit nonideal unit weights.

## Public Verilog-A Interface

Declare module `dac_mismatch_unit_weighting_model` with positional ports `b0,
b1, b2, b3, out`. All ports are electrical.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vhi = 0.9 V`: high endpoint of the reconstructed output range.
- `vlo = 0.0 V`: low endpoint of the reconstructed output range.
- `tr = 100 ps`: output transition smoothing time.

Use a 0.45 V logic threshold for each input bit.

## Required Behavior

Treat `b0..b3` as voltage-coded control bits. Reconstruct the DAC output from
explicit nonideal weights 1.00, 2.02, 3.96, and 8.08, normalized by the
all-active weight sum. Drive `out` between `vlo` and `vhi`; the all-zero input
maps to `vlo` and the all-active input maps to `vhi`.

## Modeling Constraints

Return only `dac_mismatch_unit_weighting_model.va`. Use deterministic
voltage-domain Verilog-A and smooth output transitions. Do not modify or emit
the support testbench, add validation logic, hard-code validation-only waveform sample
points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `dac_mismatch_unit_weighting_model.va`. Do not include explanatory prose outside the source artifact contents.
