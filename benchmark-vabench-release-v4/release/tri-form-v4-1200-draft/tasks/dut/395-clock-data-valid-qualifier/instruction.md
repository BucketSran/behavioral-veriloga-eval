# Clock-and-data Valid Qualifier

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `clock_data_valid_qualifier.va`
- Public top module: `clock_data_valid_qualifier`
- Required public module: `clock_data_valid_qualifier`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `clock_data_valid_qualifier` with positional electrical ports `clk, data, rst, enable, valid_out, edge_age_metric, qualified`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for digital-voltage inputs.
- `max_age_cycles = 3`: maximum allowed data-edge age in clock cycles.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear `valid_out`, `edge_age_metric`, and `qualified`.
- A rising or falling data crossing sets the age counter to zero. Each later
  rising `clk` edge increments the counter before evaluating qualification.
- Assert `qualified` when the resulting age is from 1 through
  `max_age_cycles`, inclusive, and the qualifier is enabled.
- `edge_age_metric` must expose the age as
  `vss + (vdd - vss) * min(age, max_age_cycles) / max_age_cycles`.
- `valid_out` must be a registered copy of the qualified condition on rising `clk` edges.
- This is an AMS-tied timing qualifier, not a bare DFF task.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `clock_data_valid_qualifier.va`
