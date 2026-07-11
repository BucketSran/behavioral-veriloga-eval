# PAM4 Slicer and Gray Decoder

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `pam4_slicer_gray_decoder.va`
- Public top module: `pam4_slicer_gray_decoder`
- Required public module: `pam4_slicer_gray_decoder`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `pam4_slicer_gray_decoder` with positional electrical ports `vin, clk, rst, enable, bit_msb, bit_lsb, level_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock, reset, and enable.
- `t0 = 0.225 V`: lower PAM4 slicing threshold.
- `t1 = 0.45 V`: middle PAM4 slicing threshold.
- `t2 = 0.675 V`: upper PAM4 slicing threshold.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear output bits, `level_metric`, and `valid`.
- On each rising `clk` edge while enabled, slice `vin` into four ordered PAM4 levels using `t0`, `t1`, and `t2`.
- Encode the sliced level with Gray ordering: level 0 -> 00, level 1 -> 01, level 2 -> 11, level 3 -> 10.
- `level_metric` must expose sliced level `k` as
  `vss + (vdd - vss) * k / 3`, for `k` from 0 through 3.
- Assert `valid` after each enabled sample.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `pam4_slicer_gray_decoder.va`
