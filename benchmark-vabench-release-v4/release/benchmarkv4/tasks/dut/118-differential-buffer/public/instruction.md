# Differential Buffer

## Task Contract

Implement the requested Verilog-A artifact for `Differential Buffer`.
- Form: `dut`
- Level: `L1`
- Category: `analog_macromodels`
- Target artifact(s): `differential_buffer.va`

Implement the Verilog-A macro `differential_buffer.va` for a unity-gain
differential pass-through buffer used to preserve polarity and common-mode in
AMS signal-chain interfaces.

This is a small reusable AMS macro task. The solver should implement the
stated interface behavior without adding gain, delay, common-mode conversion,
or rail logic.

## Public Verilog-A Interface

Provide `module differential_buffer(VINP, VINN, VOUTP, VOUTN);` with electrical inputs `VINP`, `VINN` and electrical outputs `VOUTP`, `VOUTN`.

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

Drive `VOUTP` from `VINP` and `VOUTN` from `VINN` with unity gain and the same polarity on each side.

## Modeling Constraints

Use direct voltage contributions. Do not swap polarity, collapse the output to common mode, or add unnecessary retained state.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Submit only the completed Verilog-A module in `differential_buffer.va`.
