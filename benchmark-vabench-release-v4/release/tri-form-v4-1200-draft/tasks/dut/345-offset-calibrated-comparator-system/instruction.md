# Offset-calibrated Comparator System

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `calibrated_comparator_top.va`, `comparator_core.va`, `offset_dac.va`, `calibration_fsm.va`
- Public top module: `calibrated_comparator_top`
- Required public modules: `calibrated_comparator_top`, `comparator_core`, `offset_dac`, `calibration_fsm`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `calibrated_comparator_top` with positional electrical ports `vinp, vinn, clk, rst, cal_en, cal_ref, decision, ready, offset_3, offset_2, offset_1, offset_0, threshold_dbg`. All top-level ports are electrical.

Each required public module has a fixed ordered electrical interface and parameter contract; these are part of the submitted artifact contract:

- `comparator_core(vinp, vinn, threshold_i, rst, decision)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.
- `offset_dac(offset_3, offset_2, offset_1, offset_0, rst, threshold_dbg)`; parameters: offset_lsb=5e-3, vss=0.0, vth=0.45, tr=200p.
- `calibration_fsm(clk, rst, cal_en, cal_ref, ready, offset_3, offset_2, offset_1, offset_0)`; parameters: vdd=0.9, vss=0.0, vth=0.45, tr=200p.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clocked control inputs.
- `offset_lsb = 5e-3 V`: voltage represented by one offset-code step.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the offset code, `decision`, `ready`, and `threshold_dbg`.
- While `cal_en` is high, `calibration_fsm` updates the signed offset code once per rising `clk` edge using `cal_ref` as the calibration error input.
- When `cal_ref` is above `vth`, increment the offset code by one step up to code 15; otherwise decrement by one step down to code 0.
- After four calibration updates with `cal_en` high, assert `ready` and hold the final offset code until reset or another calibration window.
- `offset_dac` must convert the 4-bit offset code to `threshold_dbg = (offset_code - 8) * offset_lsb`.
- `comparator_core` must drive `decision` high when `V(vinp) - V(vinn) + threshold_dbg >= 0`, otherwise low.
- Drive `offset_3..offset_0` as voltage-coded copies of the current offset code.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `calibrated_comparator_top.va`
- `comparator_core.va`
- `offset_dac.va`
- `calibration_fsm.va`
