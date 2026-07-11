# Charge-pump Voltage Multiplier Controller

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `voltage_multiplier_top.va`, `phase_generator.va`, `pump_stage_model.va`, `regulation_comparator.va`
- Public top module: `voltage_multiplier_top`
- Required public modules: `voltage_multiplier_top`, `phase_generator`, `pump_stage_model`, `regulation_comparator`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `voltage_multiplier_top` with positional electrical ports `clk, rst, enable, target, vout, phase_a, phase_b, pump_en, regulation_error, ready`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `pump_step = 40e-3 V`: voltage-domain output increment per active pump phase.
- `leak_step = 5e-3 V`: voltage-domain decay per disabled update.
- `ready_tol = 25e-3 V`: regulation tolerance around `target`.
- `vout_max = 1.8 V`: maximum modeled multiplier output.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear pump phases, `pump_en`, `ready`, `regulation_error`, and drive `vout` to `vss`.
- `phase_generator` must generate non-overlapping `phase_a` and `phase_b` updates from rising `clk` edges while enabled.
- `regulation_comparator` asserts `pump_en` when `vout` is below `target - ready_tol` and deasserts it when above `target + ready_tol`.
- `pump_stage_model` updates `vout` as a voltage-domain state: it rises by `pump_step` on active pump phases while `pump_en` is high and decays by `leak_step` when disabled.
- Clamp `vout` between `vss` and `vout_max`.
- `regulation_error` must expose `target - vout` as a voltage metric.
- Assert `ready` after three consecutive phase updates within the regulation tolerance.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `voltage_multiplier_top.va`
- `phase_generator.va`
- `pump_stage_model.va`
- `regulation_comparator.va`
