Write a Verilog-A module named `parameter_type_override_ref`.

# Task: parameter_type_override_smoke

## Objective

Write a Verilog-A pulse source whose observable behavior depends on both a real-valued instance parameter override and an integer-valued instance parameter override from the Spectre testbench instance line.

## Specification

- **Module name**: `parameter_type_override_ref`
- **Ports**: `out`, `vss` - both `electrical`
- **Behavior**:
  - Declare a real parameter `vhi` with a default value that is not the final test value.
  - Declare an integer parameter `reps` with a default value that is not the final test value.
  - ..))` events to emit a finite pulse train.
  - The pulse amplitude must be controlled by `vhi`.
  - The number of emitted pulses must be controlled by `reps`.
- **Testbench override requirement**:
  - Override the DUT instance with `vhi=0.72` and `reps=4`.
- **Expected observable behavior**:
  - The output should produce four pulses.
  - The HIGH level should sit near `0.72 V`.
  - A design that ignores the instance overrides should fail the task because the default parameter values must produce a different pulse count and/or HIGH level.

## Constraints

- Use `parameter real`, `parameter integer`, `@(initial_step)`, `@(timer(...))`, and `transition(...)`.
- The parameter override must happen on the DUT instance line in the `.scs` testbench.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.

Ports:
- `out`: electrical
- `vss`: electrical (power rail)
- `vss`: inout electrical (power rail)


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=60n maxstep=200p
```

Required public waveform columns in `tran.csv`:

- `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vss`.
