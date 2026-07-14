# Calibration Deadband Controller

## Task Contract

Implement the requested Verilog-A artifact for `Calibration Deadband Controller`.
- Form: `dut`
- Level: `L1`
- Category: `calibration_control`
- Target artifact(s): `calibration_deadband_controller.va`

Implement a clocked voltage-domain calibration deadband controller. Return only the requested DUT artifact; do not generate a testbench.

## Public Verilog-A Interface

Declare module `calibration_deadband_controller` with positional ports `clk, rst, vin, out, metric`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `vin` is the signed calibration-error input around the target voltage, `out` is the bounded trim output, and `metric` reports whether the last sample accepted an update.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: transition smoothing time for `out` and `metric`.
- `vth = 0.45 V`: logic threshold for `clk` and `rst`.
- `target = 0.45 V`: zero-error target for `vin`.
- `deadband = 0.05 V`: signed error magnitude below which the trim holds.
- `step_size = 0.06 V`: trim increment or decrement per accepted update.
- `vmin = 0.05 V`: lower clamp for `out`.
- `vmax = 0.85 V`: upper clamp for `out`.

## Required Behavior

- Initialize the trim output to `target`.
- On each rising crossing of `clk` through `vth`, sample `vin` and update the trim state.
- While `rst` is above `vth`, reset the trim state to `target` and drive `metric` low.
- Compute signed error as `V(vin) - target`.
- If the error is greater than `deadband`, increase the trim by `step_size`.
- If the error is less than `-deadband`, decrease the trim by `step_size`.
- If the error is inside the deadband, hold the trim state.
- Clamp the trim state between `vmin` and `vmax`.
- Drive `metric` high only on accepted trim updates and low otherwise.

## Modeling Constraints

Use pure voltage-domain behavioral Verilog-A. Do not use current contributions, transistor-level devices, AC/noise analysis, validation logic, validation-only hooks, simulator-specific side channels, or KCL/KVL solving assumptions.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `calibration_deadband_controller.va`.
Do not include explanatory prose outside the source artifact contents.
