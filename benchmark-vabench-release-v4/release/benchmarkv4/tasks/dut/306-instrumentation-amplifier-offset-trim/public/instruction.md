# Instrumentation Amplifier Offset-trim System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `instrumentation_amp_offset_trim_top.va`, `diff_gain_core.va`, `offset_trim_controller.va`
- Public top module: `instrumentation_amp_offset_trim_top`
- Required public modules: `instrumentation_amp_offset_trim_top`, `diff_gain_core`, `offset_trim_controller`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `instrumentation_amp_offset_trim_top` with positional electrical ports `vinp, vinn, clk, rst, cal_en, trim_2, trim_1, trim_0, vout, offset_metric, ready`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `diff_gain = 8.0`: corrected differential gain.
- `trim_lsb = 8e-3 V`: correction step per trim code.

## Required Behavior

- On reset, clear the trim state, drive `vout` to `vcm`, clear `offset_metric`, and clear `ready`.
- Decode `trim_2..trim_0` as a signed offset correction around zero.
- While `cal_en` is high, update the internal trim accumulator once per rising `clk` edge toward reducing the measured input offset.
- Drive `vout` from the corrected differential input and clamp to the output rails.
- Expose the active correction on `offset_metric` and assert `ready` after three calibration updates.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `instrumentation_amp_offset_trim_top.va`
- `diff_gain_core.va`
- `offset_trim_controller.va`
