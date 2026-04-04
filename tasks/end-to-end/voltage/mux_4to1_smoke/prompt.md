# Task: mux_4to1_smoke

## Objective

Write a Verilog-A behavioral module for a **4-to-1 Multiplexer**.

## Specification

- **Module name**: `mux_4to1`
- **Ports**: `VDD` (inout), `VSS` (inout), `D3`..`D0` (input), `SEL1` (input), `SEL0` (input), `Y` (output) — all `electrical`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Combinational: output `Y` passes the selected input.
  - `SEL = {SEL1, SEL0}`: 00→D0, 01→D1, 10→D2, 11→D3.
  - Updates whenever any of SEL1, SEL0, D3, D2, D1, D0 change.
- **Output**: use `transition()`. No `idt` or current-domain constructs.

## Constraints

- Pure voltage-domain.
- Use `@(cross(...))` on all inputs to detect changes.
- Use `$strobe` on each selection change.

## Deliverable

A single `.va` file: `mux_4to1.va`.
