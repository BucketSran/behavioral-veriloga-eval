# Capacitor Mismatch Calibration Engine

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `capacitor_mismatch_cal_engine_top.va`, `cal_code_accumulator.va`, `correction_metric_dac.va`
- Public top module: `capacitor_mismatch_cal_engine_top`
- Required public modules: `capacitor_mismatch_cal_engine_top`, `cal_code_accumulator`, `correction_metric_dac`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the top-level DUT entry point; helper modules must be part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `capacitor_mismatch_cal_engine_top` with positional electrical ports `err_in, clk, rst, enable, cal_3, cal_2, cal_1, cal_0, correction_metric, done`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `err_tol = 20e-3 V`: completion tolerance.
- `corr_lsb = 6e-3 V`: correction step.

## Required Behavior

- On reset or when disabled, clear the calibration code, metric, and `done`.
- On each enabled rising `clk` edge, update a signed correction accumulator using the sign of `err_in - vcm`.
- Saturate the public 4-bit calibration code at the endpoints.
- Drive `correction_metric` as the voltage-coded correction applied by the active code.
- Assert `done` after eight enabled updates or when the error remains within `err_tol` for two updates.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

Decode the public calibration outputs as `code = cal_0 + 2*cal_1 + 4*cal_2 + 8*cal_3` using `vth`, and drive `correction_metric = clamp(code*corr_lsb, vss, vdd)`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. Keep required public modules present and meaningful, and keep top-level behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `capacitor_mismatch_cal_engine_top.va`
- `cal_code_accumulator.va`
- `correction_metric_dac.va`
