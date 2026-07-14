# Variable Gain Differential Amplifier

## Task Contract
Implement the Verilog-A DUT `variable_gain_differential_amplifier.va` for a differential variable-gain amplifier with output limiting.

## Public Verilog-A Interface
Provide `module variable_gain_differential_amplifier(sigin_p, sigin_n, sigctrl_p, sigctrl_n, sigout);` with electrical inputs `sigin_p`, `sigin_n`, `sigctrl_p`, `sigctrl_n` and electrical output `sigout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Use `V(sigctrl_p, sigctrl_n)` as the gain-control voltage and `V(sigin_p, sigin_n)` as the signal input. Multiply the two differential voltages by a gain constant of 2.0, center the output around 0.2 V, and clamp the final target to -0.4 V through 0.8 V.

## Modeling Constraints
Use real-valued voltage-domain arithmetic. Do not use a single-ended control input, omit the output midpoint, remove the clamp, or add unrelated filtering.

## Output Contract
Submit only the completed Verilog-A module in `variable_gain_differential_amplifier.va`.
