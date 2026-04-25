Write a Verilog-A module named `differential_voltage_output_ref`.

# Task: differential_voltage_output_smoke

## Objective

Write a Verilog-A differential output source that drives a fixed common-mode low leg and a timer-controlled differential high leg using `V(outp, outn) <+ ...`.

## Specification

- **Module name**: `differential_voltage_output_ref`
- **Ports**: `VDD`, `VSS`, `outp`, `outn` - all `electrical`
- **Behavior**:
  - Keep `outn` at a fixed common-mode reference of `0.2 V` above `VSS`.
  - Drive the differential branch `V(outp, outn)` through `transition(...)`.
  - Start with a differential level of `0.1 V`.
  - At `20 ns`, switch the differential level to `0.5 V`.
  - At `40 ns`, switch it back to `0.1 V`.
- **Expected observable behavior**:
  - `outn` stays near `0.2 V` throughout.
  - `outp` should sit near `0.3 V`, then `0.7 V`, then `0.3 V`.
  - The case must rely on true differential contribution semantics rather than two separate single-ended outputs.

## Constraints

- Use `@(initial_step)`, `@(timer(...))`, `transition(...)`, and `V(outp, outn) <+ ...`.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `outp`: output electrical
- `outn`: output electrical

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
tran tran stop=60n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `outp`, `outn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`.
