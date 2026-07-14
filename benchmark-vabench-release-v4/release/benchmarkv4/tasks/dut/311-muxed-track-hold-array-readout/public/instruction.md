# Muxed Track-hold Array Readout

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `muxed_track_hold_array_top.va`, `track_hold_cell.va`, `readout_mux.va`
- Public top module: `muxed_track_hold_array_top`
- Required public modules: `muxed_track_hold_array_top`, `track_hold_cell`, `readout_mux`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `muxed_track_hold_array_top` with positional electrical ports `vin0, vin1, vin2, clk, rst, sel_1, sel_0, sample_en, vout, channel_metric, valid`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear all held channel states, output, channel metric, and `valid`.
- On each enabled sampling clock edge, capture all three input channels into separate hold states.
- Decode `sel_1..sel_0` and route the selected held channel to `vout`; invalid code 3 must hold the previous output and clear `valid`.
- Expose the selected channel index on `channel_metric` as a voltage-coded metric.
- Hold all channel samples between sampling events.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `muxed_track_hold_array_top.va`
- `track_hold_cell.va`
- `readout_mux.va`
