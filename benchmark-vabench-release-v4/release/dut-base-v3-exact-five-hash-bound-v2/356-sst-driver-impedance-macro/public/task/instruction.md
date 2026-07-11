# SST Driver Impedance Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `sst_driver_macro.va`
- Public top module: `sst_driver_macro`
- Required public module: `sst_driver_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `sst_driver_macro` with positional electrical ports `data, enable, clk, rst, z_2, z_1, z_0, vout, swing_metric, z_metric`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high reference level.
- `vss = 0.0 V`: logic low reference level.
- `vcm = 0.45 V`: output common-mode.
- `vth = 0.45 V`: threshold for digital inputs.
- `swing_min = 0.15 V`: minimum single-ended swing around `vcm`.
- `swing_lsb = 25e-3 V`: swing increment per impedance-code step.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, drive `vout` to `vcm` and clear `swing_metric`.
- On rising `clk` edges while enabled, latch the input data level.
- Convert `z_2..z_0` to an unsigned trim code from 0 to 7.
- Map larger trim codes to larger voltage swing around `vcm` using `swing_min` and `swing_lsb`.
- Drive `vout` above `vcm` for data high and below `vcm` for data low.
- `swing_metric` must expose the selected swing magnitude in volts.
- `z_metric` must expose trim code `k` as `vss + (vdd - vss) * k / 7`, so
  codes 0 and 7 map to the public output rails.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `sst_driver_macro.va`
