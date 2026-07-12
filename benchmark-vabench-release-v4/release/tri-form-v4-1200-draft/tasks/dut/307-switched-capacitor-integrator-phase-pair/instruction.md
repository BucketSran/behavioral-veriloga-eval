# Switched-capacitor Integrator Phase Pair

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `switched_cap_integrator_phase_pair_top.va`, `sample_phase_cell.va`, `integrator_state_cell.va`
- Public top module: `switched_cap_integrator_phase_pair_top`
- Required public modules: `switched_cap_integrator_phase_pair_top`, `sample_phase_cell`, `integrator_state_cell`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `switched_cap_integrator_phase_pair_top` with positional electrical ports `vin, phi1, phi2, rst, enable, vout, phase_metric, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `k_int = 0.2`: integration increment per phase pair.

## Required Behavior

- On reset or when disabled, clear the integration state, drive `vout` to `vcm`, and clear `valid`.
- On a rising `phi1` crossing, sample the input deviation from `vcm` into the sampling state.
- On the following rising `phi2` crossing, add `k_int` times the sampled deviation to the integrator state.
- Reject overlapping `phi1` and `phi2` updates by holding the previous state and lowering `valid` for that cycle.
- Expose the most recent accepted phase pair on `phase_metric` and clamp `vout` to the rails.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `switched_cap_integrator_phase_pair_top.va`
- `sample_phase_cell.va`
- `integrator_state_cell.va`
