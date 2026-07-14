# PAM4 Transmitter Driver

## Task Contract

Implement a Verilog-A DUT source package for a multi-module mixed-signal behavioral system.

- Target artifacts: `pam4_tx_top.va`, `gray_mapper.va`, `level_dac.va`, `preemphasis_driver.va`
- Public top module: `pam4_tx_top`
- Required public modules: `pam4_tx_top`, `gray_mapper`, `level_dac`, `preemphasis_driver`

The submitted package may include helper modules, but it must include the target artifacts and public modules listed above. The public top module is the only module instantiated by the evaluator; helper modules must be part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `pam4_tx_top` with positional electrical ports `bit_msb, bit_lsb, clk, rst, emph_en, vout, level_1, level_0, delta_dbg`. All top-level ports are electrical.

Each required public helper module must be declared in one of the returned source artifacts. The helper modules may use implementation-local ports chosen by the solver, but the top module must expose exactly the public top-level port order above.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for bits, clock, reset, and emphasis enable.
- `level_step = 0.3 V`: spacing between adjacent PAM4 levels.
- `emph_step = 60e-3 V`: one-symbol transition emphasis magnitude.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset, clear the previous symbol, level outputs, `delta_dbg`, and drive `vout` to `vss`.
- On each rising `clk` edge, `gray_mapper` maps input bits to PAM4 levels in Gray order: 00, 01, 11, 10 correspond to levels 0, 1, 2, 3.
- `level_dac` converts the mapped level to a voltage from `vss` to `vss + 3 * level_step`.
- When `emph_en` is high, `preemphasis_driver` adds one-symbol emphasis with polarity matching the transition from the previous mapped level to the current level.
- Clamp the final output to the range `vss` through `vdd`.
- `level_1..level_0` must expose the mapped level as voltage-coded bits.
- `delta_dbg` must expose the signed transition delta used for emphasis.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a modular DUT task: keep the required helper-module boundaries meaningful rather than collapsing all behavior into a single monolithic top module. The evaluator may use static checks to confirm that the required public modules are present, and behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `pam4_tx_top.va`
- `gray_mapper.va`
- `level_dac.va`
- `preemphasis_driver.va`
