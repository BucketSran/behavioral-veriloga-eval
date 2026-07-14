# Successive Approximation Calibration Search Fsm

## Task Contract

Implement the requested Verilog-A artifact for `Successive Approximation Calibration Search Fsm`.
- Form: `dut`
- Level: `L1`
- Category: `calibration_control`
- Target artifact(s): `successive_approximation_calibration_search_fsm.va`

Implement a clocked voltage-domain successive-approximation calibration search controller. Return only the requested DUT artifact; do not generate the validation harness.

## Public Verilog-A Interface

Declare module `successive_approximation_calibration_search_fsm` with positional ports `clk, rst, vin, out, metric`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `vin` is the signed calibration decision input around the target voltage, `out` is the bounded trial trim output, and `metric` is a done flag.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: transition smoothing time for `out` and `metric`.
- `vth = 0.45 V`: logic threshold for `clk` and `rst`.
- `target = 0.45 V`: zero-error decision target for `vin`.
- `step_init = 0.18 V`: initial trial step size.
- `vmin = 0.05 V`: lower clamp for `out`.
- `vmax = 0.85 V`: upper clamp for `out`.

## Required Behavior

- Initialize the trial trim to `target`, the step size to `step_init`, and `metric` low.
- On each rising crossing of `clk` through `vth`, update the search state unless the search is already done.
- While `rst` is above `vth`, reset the trial trim to `target`, restore the initial step size, clear the cycle counter, and drive `metric` low.
- Treat `V(vin) - target` as the signed decision input.
- For a positive decision input, increase the trial trim by the current step size.
- For a negative decision input, decrease the trial trim by the current step size.
- Halve the step size after each active decision update.
- Assert `metric` after the public four-step search window has completed.
- Clamp the trial trim between `vmin` and `vmax`.

## Modeling Constraints

Use pure voltage-domain behavioral Verilog-A. Do not use current contributions, transistor-level devices, AC/noise analysis, validation logic, validation-only hooks, simulator-specific side channels, or KCL/KVL solving assumptions.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `successive_approximation_calibration_search_fsm.va`.
Do not include explanatory prose outside the source artifact contents.
