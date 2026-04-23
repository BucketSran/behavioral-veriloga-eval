Write a Verilog-A module named `cross_hysteresis_window_ref`.

# Task: cross_hysteresis_window_smoke

## Objective

Write a Verilog-A hysteresis element that uses directional `cross()` events to switch HIGH and LOW at different thresholds.

## Specification

- **Module name**: `cross_hysteresis_window_ref`
- **Ports**: `vin`, `out`, `VDD`, `VSS` - all `electrical`
- **Behavior**:
  - Output starts LOW.
  - When `vin` rises above `0.6 V`, output becomes HIGH.
  - When `vin` falls below `0.3 V`, output becomes LOW.
  - Between thresholds, hold the previous state.
  - Drive output with `transition(...)`.

## Constraints

- .., +1))`, `@(cross(..., -1))`, and `@(initial_step)`.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vin`: input electrical
- `out`: output electrical
