# Task: pfd_updn_smoke

## Objective

Write a Verilog-A behavioral module for a **Phase-Frequency Detector (PFD)** with UP/DN digital outputs.

## Specification

- **Module name**: `pfd_updn`
- **Ports**: `VDD` (inout), `VSS` (inout), `REF` (input), `DIV` (input), `UP` (output), `DN` (output) — all `electrical`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 50p)
- **Behavior**:
  - Rising edge of `REF` sets `UP` high.
  - Rising edge of `DIV` sets `DN` high.
  - When both `UP` and `DN` are high, both are immediately reset to 0 (combinational reset).
  - `UP` dominant when REF leads DIV; `DN` dominant when DIV leads REF.
- **Output**: use `transition()` only.

## Constraints

- Pure voltage-domain. No `idt`, `ddt`, or current contributions.
- Use `integer` variables for state; update on `@(cross(..., +1))`.
- Use `$strobe` to log each edge event.

## Deliverable

A single `.va` file: `pfd_updn.va`.
