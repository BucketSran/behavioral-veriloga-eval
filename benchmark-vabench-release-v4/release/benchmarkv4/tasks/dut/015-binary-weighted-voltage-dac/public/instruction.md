# Binary Weighted Voltage DAC

## Task Contract

Implement the requested Verilog-A artifact for `Binary Weighted Voltage DAC`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `simple_binary_voltage_dac_4b.va`

Implement a 4-bit binary-weighted voltage DAC.

## Public Verilog-A Interface

Declare module `simple_binary_voltage_dac_4b` with positional ports `code_0,
code_1, code_2, code_3, vref, vss, aout`. All ports are electrical.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: digital decision threshold for each code bit.
- `tr = 500 ps`: output transition smoothing time.

## Required Behavior

Treat `code_0..code_3` as an unsigned 4-bit binary word with weights 1, 2, 4,
and 8. Drive `aout` linearly between `vss` and `vref`, with the all-zero input
at `vss` and the all-ones input at `vref`. The output should update
continuously with input bit changes.

## Modeling Constraints

Return only `simple_binary_voltage_dac_4b.va`. Use deterministic
voltage-domain Verilog-A and smooth output transitions. Do not modify or emit
the support testbench, add validation logic, hard-code validation-only waveform sample
points, add simulator-specific side channels, use current contributions,
`ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `simple_binary_voltage_dac_4b.va`. Do not include explanatory prose outside the source artifact contents.
