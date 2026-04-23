Write a Verilog-A module named `bound_step_period_guard_ref`.

# Task: bound_step_period_guard_smoke

## Objective

Write a Verilog-A timing guard that uses `$bound_step()` to keep a narrow periodic observation window visible even when the external transient step is much coarser than the target pulse width.

## Specification

- **Module name**: `bound_step_period_guard_ref`
- **Ports**: `VDD`, `VSS`, `guard_out`, `phase_out` - all `electrical`
- **Behavior**:
  - Track an internal cycle boundary every `8 ns` using `@(timer(next_cycle))`.
  - Request `$bound_step(period / 16)` continuously.
  - Drive `guard_out` HIGH only during the first `1.5 ns` of each cycle, then LOW for the rest of the period.
  - Drive `phase_out` as a normalized `0..VDD` ramp within each cycle so resets are externally visible.
- **Testbench intent**:
  - The supplied testbench uses a coarse `tran maxstep=20n`.
  - The DUT should rely on `$bound_step()` rather than the outer `tran` step to preserve the periodic guard windows.

## Constraints

- Use `@(initial_step)`, `@(timer(...))`, `$bound_step(...)`, and `transition(...)`.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.
- Do not claim solver-level equivalence beyond bounded-step event consistency.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `guard_out`: output electrical
- `phase_out`: output electrical
