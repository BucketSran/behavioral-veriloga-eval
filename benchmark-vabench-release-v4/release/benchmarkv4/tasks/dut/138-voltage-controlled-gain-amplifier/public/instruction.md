# Voltage Controlled Gain Amplifier

## Task Contract
Implement the Verilog-A DUT `voltage_controlled_gain_amplifier.va` for a voltage-controlled differential gain block with a unipolar output range.

## Public Verilog-A Interface
Provide `module voltage_controlled_gain_amplifier(vin_p, vin_n, vctrl_p, vctrl_n, vout);` with electrical inputs `vin_p`, `vin_n`, `vctrl_p`, `vctrl_n` and electrical output `vout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Use `V(vctrl_p, vctrl_n)` as the gain-control voltage. Subtract a 0.05 V input-referred offset from `V(vin_p, vin_n)`, multiply by the control voltage and a gain constant of 1.5, center the output around 0.5 V, and clamp the final target to 0.1 V through 0.9 V.

## Modeling Constraints
Use direct voltage-domain arithmetic. Do not use a single-ended control input, omit the input offset, remove the unipolar clamp, or depend on testbench timing.

## Output Contract
Submit only the completed Verilog-A module in `voltage_controlled_gain_amplifier.va`.
