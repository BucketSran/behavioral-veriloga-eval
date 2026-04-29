Write a Verilog-A module named `final_step_file_metric_ref`.

# Task: final_step_file_metric_smoke

## Objective

Write a Verilog-A measurement helper that counts input edges, exposes the normalized count on a voltage output, and writes the final metric to a file during `@(final_step)`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref`: input electrical
- `metric_out`: output electrical

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `ref`, `metric_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `ref`.
