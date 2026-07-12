# Two-stage Pipeline ADC Mini Chain

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `pipeline_adc_top.va`, `stage1_quantizer.va`, `residue_amp.va`, `stage2_quantizer.va`, `code_aligner.va`
- Public top module: `pipeline_adc_top`
- Required public modules: `pipeline_adc_top`, `stage1_quantizer`, `residue_amp`, `stage2_quantizer`, `code_aligner`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `pipeline_adc_top` with positional electrical ports `vin, clk, rst, valid_i, code_3, code_2, code_1, code_0, valid_o, residue_dbg`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `stage1_quantizer(vin, clk, rst, valid_i, bit_1, bit_0, valid_o)`; parameters: vdd=0.9, vss=0.0, vref=0.9, vth=0.45, tr=200p.
- `residue_amp(vin, rst, s1_1, s1_0, residue_o, residue_dbg)`; parameters: vss=0.0, vref=0.9, vth=0.45, tr=200p.
- `stage2_quantizer(residue_i, clk, rst, valid_i, bit_1, bit_0, valid_o)`; parameters: vdd=0.9, vss=0.0, vref=0.9, vth=0.45, tr=200p.
- `code_aligner(clk, rst, s1_1, s1_0, s1_valid, s2_1, s2_0, s2_valid, code_3, code_2, code_1, code_0, valid_o)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vref = 0.9 V`: full-scale input reference.
- `vth = 0.45 V`: threshold for `clk`, `rst`, and `valid_i`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear both pipeline stages, all code outputs, `valid_o`, and `residue_dbg`.
- When `valid_i` is high on a rising `clk` edge, stage 1 samples `vin` and emits a 2-bit coarse code for four equal input ranges over `[vss, vref]`.
- `residue_amp` must compute a normalized residue for the sampled input after subtracting the stage-1 coarse level and multiplying by 4.
- On the next rising `clk` edge, stage 2 quantizes the residue into the lower two output bits.
- `code_aligner` must align the delayed stage-1 bits with the stage-2 bits and assert `valid_o` with the complete 4-bit code.
- Clamp out-of-range input voltages to the endpoint codes 0 and 15.
- `residue_dbg` must expose the stage-1 residue used by stage 2.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `pipeline_adc_top.va`
- `stage1_quantizer.va`
- `residue_amp.va`
- `stage2_quantizer.va`
- `code_aligner.va`
