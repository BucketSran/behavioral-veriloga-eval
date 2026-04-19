# Task: pfd_deadzone_smoke

## Objective

Write a Verilog-A behavioral module for a phase-frequency detector whose UP/DN outputs remain well-behaved even when the REF/DIV phase offset is very small.

## Specification

- **Module name**: `pfd_updn`
- **Ports**: `VDD`, `VSS`, `REF`, `DIV`, `UP`, `DN` - all `electrical`
- **Parameters**:
  - `vth` (real, default `0.45`)
  - `tedge` (real, default `20p`)
- **Behavior**:
  - Rising edge of `REF` sets `UP` high.
  - Rising edge of `DIV` sets `DN` high.
  - When both states are high, reset both to 0.
  - For a very small phase offset, pulses should remain short and should not produce sustained UP/DN overlap.

## Constraints

- Pure voltage-domain only.
- Use `integer` state, `@(cross(..., +1))`, and `transition()`.
- Do not use current-domain operators such as `I() <+`, `ddt()`, or `idt()`.
- Keep the model EVAS-compatible.

## Deliverable

A single `.va` file: `pfd_updn.va`.
