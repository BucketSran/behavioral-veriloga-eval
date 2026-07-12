# Safe Voltage Divider

## Task Contract
Implement the single-DUT Verilog-A artifact `safe_voltage_divider.va` for an
analog voltage divider with a sign-preserving denominator guard. The visible
testbench is a public verification scenario; additional validation may exercise
different numerator and denominator waveforms.

## Public Verilog-A Interface
Provide `module safe_voltage_divider(signumer, sigdenom, sigout);` with electrical inputs `signumer`, `sigdenom` and electrical output `sigout`.

## Public Parameter Contract
Expose `parameter real gain = 1;` and `parameter real min_sigdenom = 1.0e-9 from (0:inf);`. Testbenches may override both parameters.

## Required Behavior
Compute the output as `gain` times the numerator voltage divided by a guarded denominator voltage. If the denominator magnitude is below `min_sigdenom`, replace it with `+min_sigdenom` for a nonnegative denominator and `-min_sigdenom` for a negative denominator.

## Modeling Constraints
Use continuous voltage-domain arithmetic with no unnecessary retained state. Preserve the
denominator sign when applying the guard, do not drop the gain parameter, and
do not hard-code any testbench stimulus into the DUT.

## Output Contract
Submit only the completed Verilog-A module in `safe_voltage_divider.va`.
