# 4-bit SAR ADC System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `sar_adc_top.va`, `sample_hold.va`, `sar_comparator.va`, `sar_controller.va`, `binary_weighted_cdac.va`
- Public top module: `sar_adc_top`
- Required public modules: `sar_adc_top`, `sample_hold`, `sar_comparator`, `sar_controller`, `binary_weighted_cdac`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `sar_adc_top` with positional electrical ports `vin, clk, rst, start, code_3, code_2, code_1, code_0, done, sample_dbg, dac_dbg`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `sample_hold(vin, clk, rst, sample_en, sample_o, sample_dbg)`; parameters: vss=0.0, vth=0.45, tr=200p.
- `sar_comparator(sample_i, dac_i, cmp_o)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `sar_controller(clk, rst, start, cmp_i, sample_en, trial_3, trial_2, trial_1, trial_0, code_3, code_2, code_1, code_0, done)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `binary_weighted_cdac(bit_3, bit_2, bit_1, bit_0, dac_o, dac_dbg)`; parameters: vss=0.0, vref=0.9, vth=0.45, tr=200p.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level and lower conversion endpoint.
- `vref = 0.9 V`: full-scale conversion reference.
- `vth = 0.45 V`: threshold for `clk`, `rst`, and `start`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the conversion state, code outputs, `done`, `sample_dbg`, and `dac_dbg`.
- A rising `start` request arms a new conversion; the next rising `clk` samples `vin` into `sample_hold`.
- The controller then resolves bits from `code_3` down to `code_0`, one bit per rising `clk` edge.
- For each trial code, `binary_weighted_cdac` produces `dac_dbg = vref * trial_code / 16.0`.
- `sar_comparator` keeps the active trial bit when the held sample is greater than or equal to `dac_dbg`; otherwise it clears that bit.
- After bit 0 is resolved, assert `done` high and hold the final output code until reset or the next armed conversion.
- Drive each code bit as `vdd` for logic 1 and `vss` for logic 0.
- `sample_dbg` must expose the held sample voltage used for the active conversion.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `sar_adc_top.va`
- `sample_hold.va`
- `sar_comparator.va`
- `sar_controller.va`
- `binary_weighted_cdac.va`
