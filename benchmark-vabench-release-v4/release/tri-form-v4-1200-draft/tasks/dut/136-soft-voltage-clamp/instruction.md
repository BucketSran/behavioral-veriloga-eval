# Soft Voltage Clamp

## Task Contract
Implement the Verilog-A DUT `soft_voltage_clamp_behavior.va` for a ground-referenced voltage limiter with smooth exponential knees.

## Public Verilog-A Interface
Provide `module soft_voltage_clamp_behavior(vin, vout, vgnd);` with electrical inputs `vin`, `vgnd` and electrical output `vout`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Use `V(vin, vgnd)` as the input. Pass the input through linearly from 0.0 V to 0.4 V, including the knee points. Below 0.0 V, apply an exponential soft lower limit that approaches -0.2 V. Above 0.4 V, apply an exponential soft upper limit that approaches 0.6 V. Use a 0.2 V softness span on both sides.

## Modeling Constraints
Drive `V(vout, vgnd)` with a continuous, monotonic soft-limited response. Do not hard-clip at the asymptotes or ignore the `vgnd` reference terminal.

## Output Contract
Submit only the completed Verilog-A module in `soft_voltage_clamp_behavior.va`.
