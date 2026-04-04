# Task: xor_pd_smoke

## Objective

Write a Verilog-A behavioral module for an **XOR Phase Detector**.

## Specification

- **Module name**: `xor_phase_detector`
- **Ports**: `VDD` (inout), `VSS` (inout), `REF` (input), `DIV` (input), `PD_OUT` (output) — all `electrical`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 50p)
- **Behavior**:
  - `PD_OUT` is HIGH when `REF` and `DIV` are at **different** logic levels (XOR logic).
  - Updates on every edge of both `REF` and `DIV`.
  - Average `PD_OUT` duty cycle is proportional to phase difference between the two clocks.
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Constraints

- Pure voltage-domain only.
- Track both REF and DIV state with integer variables updated on `@(cross(...))`.
- Use `$strobe` to log state changes.

## Deliverable

A single `.va` file: `xor_phase_detector.va`.
