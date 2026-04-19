# Task: comparator_hysteresis_smoke

## Objective

Write a Verilog-A behavioral model for a differential comparator with hysteresis so that the switching threshold depends on the previous output state.

## Specification

- **Module name**: `cmp_hysteresis`
- **Ports**: `VINN`, `VINP`, `OUTN`, `OUTP`, `VSS`, `VDD` - all `electrical`
- **Parameters**:
  - `vhys` (real, default `10e-3`)
  - `tedge` (real, default `50p`)
- **Behavior**:
  - When `VINP - VINN` rises above `+vhys/2`, drive `OUTP` HIGH and `OUTN` LOW.
  - When `VINP - VINN` falls below `-vhys/2`, drive `OUTP` LOW and `OUTN` HIGH.
  - Between those two thresholds, hold the previous decision.
  - Outputs must use finite transitions and show a clear hysteresis window on a ramped input.

## Constraints

- Pure voltage-domain only.
- Use `@(cross(...))`, `@(initial_step)`, and `transition()`.
- Do not use current-domain operators such as `I() <+`, `ddt()`, or `idt()`.
- Keep the model EVAS-compatible.

## Deliverable

A single `.va` file: `cmp_hysteresis.va`.
