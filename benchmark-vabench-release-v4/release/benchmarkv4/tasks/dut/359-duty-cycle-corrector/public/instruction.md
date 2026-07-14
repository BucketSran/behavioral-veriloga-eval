# Duty-cycle Corrector

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `dcc_top.va`, `duty_meter.va`, `trim_controller.va`, `delay_pair.va`
- Public top module: `dcc_top`
- Required public modules: `dcc_top`, `duty_meter`, `trim_controller`, `delay_pair`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `dcc_top` with positional electrical ports `clk_in, rst, enable, clk_out, trim_3, trim_2, trim_1, trim_0, duty_metric, locked`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `target_duty = 0.5`: desired high-time fraction.
- `duty_tol = 0.03`: lock tolerance around `target_duty`.
- `trim_step = 5e-12 s`: falling-edge delay added by one trim-code step.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, clear the trim code, `duty_metric`, `locked`, and drive `clk_out` low.
- `duty_meter` measures high-time fraction over complete input-clock cycles.
- `trim_controller` increments the trim code when measured duty is below `target_duty - duty_tol` and decrements it when above `target_duty + duty_tol`.
- `delay_pair` passes each rising input edge without intentional delay and delays its corresponding falling edge by `trim_code * trim_step`, using the trim code latched at that rising edge. A trim update must not retime an already active output pulse.
- Clamp the trim code to 0 through 15 and drive `trim_3..trim_0` as voltage-coded bits.
- Assert `locked` after three consecutive completed cycles within tolerance.
- `duty_metric` must expose the latest measured duty fraction directly as a voltage, so a measured fraction of 0.5 is reported as 0.5 V. Reset or low `enable` cancels a pending falling edge and drives `clk_out` low.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `dcc_top.va`
- `duty_meter.va`
- `trim_controller.va`
- `delay_pair.va`
