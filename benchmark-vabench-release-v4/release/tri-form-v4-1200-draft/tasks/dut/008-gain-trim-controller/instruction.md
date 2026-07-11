# Gain Trim Controller

## Task Contract

Implement the requested Verilog-A artifact for `Gain Trim Controller`.
- Form: `dut`
- Level: `L1`
- Category: `calibration_control`
- Target artifact(s): `gain_trim_controller.va`

Implement a clocked voltage-domain gain-trim controller. Return only the requested DUT artifact; do not generate a Spectre testbench.

## Public Verilog-A Interface

Declare module `gain_trim_controller` with positional ports `clk, rst, meas, target, gain_ctrl`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `meas` and `target` are analog comparison inputs, and `gain_ctrl` is the analog trim-control output.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `clk` and `rst`.
- `tr = 500 ps`: transition smoothing time for `gain_ctrl`.

## Required Behavior

- Initialize `gain_ctrl` to 0.30 V before the first clocked update.
- Treat `clk` and `rst` as voltage-coded logic with threshold `vth`.
- On every rising crossing of `clk` through `vth`, update the internal
  control state.
- Reset `gain_ctrl` to 0.30 V on a rising `clk` while `rst` is above `vth`.
- When `meas` is below `target - 0.02`, increase the control by 0.05 V; when above `target + 0.02`, decrease it by 0.05 V.
- Hold inside the deadband, clamp to 0.05 V to 0.85 V, and drive through `transition()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `gain_trim_controller.va`.
Do not include explanatory prose outside the source artifact contents.
