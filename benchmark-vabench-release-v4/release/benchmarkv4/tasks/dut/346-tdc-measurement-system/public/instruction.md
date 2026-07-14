# TDC Event Measurement System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `tdc_measurement_top.va`, `edge_detector.va`, `interval_counter.va`, `binary_encoder.va`, `valid_latch.va`
- Public top module: `tdc_measurement_top`
- Required public modules: `tdc_measurement_top`, `edge_detector`, `interval_counter`, `binary_encoder`, `valid_latch`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `tdc_measurement_top` with positional electrical ports `start, stop, clk, rst, code_7, code_6, code_5, code_4, code_3, code_2, code_1, code_0, valid, overflow`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `edge_detector(start, stop, rst, clear_i, start_evt, stop_evt)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `interval_counter(clk, rst, start_evt, stop_evt, count_7, count_6, count_5, count_4, count_3, count_2, count_1, count_0, valid_i, overflow_i, clear_o)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `binary_encoder(count_7, count_6, count_5, count_4, count_3, count_2, count_1, count_0, code_7, code_6, code_5, code_4, code_3, code_2, code_1, code_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `valid_latch(rst, start_evt, valid_i, overflow_i, valid, overflow)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for `start`, `stop`, `clk`, and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the interval counter, output code, `valid`, and `overflow`.
- A rising `start` crossing arms a measurement and clears the active count.
- While armed, increment the active count on each rising `clk` edge until a rising `stop` crossing is observed.
- On the first stop edge after start, latch the count into `code_7..code_0`, assert `valid`, and disarm the measurement.
- If the active count exceeds 255 before stop, saturate the output code to 255, assert `overflow`, assert `valid`, and disarm.
- A new rising `start` edge begins a new measurement and clears `valid` and `overflow`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `tdc_measurement_top.va`
- `edge_detector.va`
- `interval_counter.va`
- `binary_encoder.va`
- `valid_latch.va`
