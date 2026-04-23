Write a Verilog-A module named `above_threshold_startup_ref`.

# Task: above_threshold_startup_smoke

## Objective

Write a Verilog-A startup latch that uses `@(above(...))` to recognize a threshold that is already satisfied at `t=0`.

## Specification

- **Module name**: `above_threshold_startup_ref`
- **Ports**: `VDD`, `VSS`, `vin`, `out` - all `electrical`
- **Behavior**:
  - Output starts LOW by default.
  - If `vin` is above `0.45 V`, an `@(above(V(vin) - 0.45))` event should set the internal state HIGH.
  - Once HIGH, keep the state latched HIGH for the rest of the run.
  - Drive the output with `transition(...)`.
- **Startup intent**:
  - The supplied testbench drives `vin=0.9 V` from `t=0` onward.
  - This task is specifically checking that `above()` startup semantics are honored even when the condition is already true at the initial time.

## Constraints

- Use `@(above(...))` and `transition(...)`.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.
- Do not rewrite the behavior as `initial_step or above(...)`; the point is to test pure `above()` startup behavior.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vin`: input electrical
- `out`: output electrical
