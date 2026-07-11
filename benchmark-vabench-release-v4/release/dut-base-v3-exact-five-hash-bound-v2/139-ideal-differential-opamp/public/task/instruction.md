# Ideal Differential Opamp

## Task Contract
Implement the Verilog-A DUT `ideal_differential_opamp.va` for a fixed-gain ideal differential output stage.

## Public Verilog-A Interface
Provide `module ideal_differential_opamp(vinp, vinn, voutp, voutn);` with electrical inputs `vinp`, `vinn` and electrical outputs `voutp`, `voutn`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Maintain a fixed output common mode of 0.5 V. The differential output must be four times the input differential voltage, with `voutp` increasing and `voutn` decreasing when `V(vinp, vinn)` is positive.

## Modeling Constraints
Use direct voltage contributions and preserve symmetry around the output common mode. Do not invert polarity, halve the gain, or collapse the outputs to one common-mode value.

## Output Contract
Submit only the completed Verilog-A module in `ideal_differential_opamp.va`.
