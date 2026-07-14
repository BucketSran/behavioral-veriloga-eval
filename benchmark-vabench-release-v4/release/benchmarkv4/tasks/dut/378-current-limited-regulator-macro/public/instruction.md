# Current-limited Regulator Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `current_limited_regulator_macro.va`
- Public top module: `current_limited_regulator_macro`
- Required public module: `current_limited_regulator_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `current_limited_regulator_macro` with positional electrical ports `vin, load_demand, enable, rst, vout, limit_metric, regulation_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vref = 0.75 V`: regulated output target.
- `dropout = 0.08 V`: minimum headroom between `vin` and regulated target.
- `demand_limit = 0.65 V`: voltage-domain load-demand threshold where limit behavior begins.
- `vth = 0.45 V`: threshold for `enable` and `rst`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive `vout`, `limit_metric`, and `regulation_ok` low.
- When enabled with enough input headroom and load demand below `demand_limit`, drive `vout` toward `vref`.
- When input headroom is insufficient, clamp the target output below `V(vin) - dropout`.
- When `load_demand` exceeds `demand_limit`, reduce the target output in proportion to the overload and expose the overload amount on `limit_metric`.
- Assert `regulation_ok` only when the commanded target is within the normal regulation window and not current-limited.
- This is a voltage-domain macromodel; the load demand is a voltage-coded proxy and no branch-current oracle is required.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `current_limited_regulator_macro.va`
