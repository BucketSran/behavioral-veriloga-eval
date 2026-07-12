# Segmented DAC with DEM Control

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `segmented_dac_dem_top.va`, `thermometer_decoder.va`, `binary_decoder.va`, `dwa_rotator.va`, `dac_driver.va`
- Public top module: `segmented_dac_dem_top`
- Required public modules: `segmented_dac_dem_top`, `thermometer_decoder`, `binary_decoder`, `dwa_rotator`, `dac_driver`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `segmented_dac_dem_top` with positional electrical ports `clk, rst, code_5, code_4, code_3, code_2, code_1, code_0, vout, sel_7, sel_6, sel_5, sel_4, sel_3, sel_2, sel_1, sel_0, ptr_2, ptr_1, ptr_0`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `thermometer_decoder(code_5, code_4, code_3, req_2, req_1, req_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `binary_decoder(code_2, code_1, code_0, fine_2, fine_1, fine_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `dwa_rotator(clk, rst, req_2, req_1, req_0, sel_7, sel_6, sel_5, sel_4, sel_3, sel_2, sel_1, sel_0, ptr_2, ptr_1, ptr_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `dac_driver(clk, rst, req_2, req_1, req_0, fine_2, fine_1, fine_0, vout)`; parameters: vss=0.0, vref=0.9, vth=0.45, tr=200p.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vref = 0.9 V`: full-scale DAC reference.
- `vth = 0.45 V`: threshold for input code bits, `clk`, and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the DEM pointer, selected unit mask, pointer outputs, and `vout`.
- On each rising `clk` edge, sample the 6-bit input code as an unsigned integer from 0 to 63.
- `thermometer_decoder` must decode the three MSBs into a requested count from 0 to 7 unit elements.
- `dwa_rotator` must select that many unit elements in a rotating circular order and then advance the pointer by the selected count.
- `binary_decoder` must decode the three LSBs as the fine binary contribution.
- `dac_driver` must drive `vout = vref * code / 63.0` while `sel_7..sel_0` expose the rotated unit-element mask.
- `ptr_2..ptr_0` must expose the pointer value after the sampled update.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `segmented_dac_dem_top.va`
- `thermometer_decoder.va`
- `binary_decoder.va`
- `dwa_rotator.va`
- `dac_driver.va`
