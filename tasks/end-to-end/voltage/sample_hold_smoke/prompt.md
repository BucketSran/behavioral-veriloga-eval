# Task: sample_hold_smoke

## Objective

Write a Verilog-A behavioral module for a **Sample-and-Hold (S&H) circuit**.

## Specification

- **Module name**: `sample_hold`
- **Ports**: `VDD` (inout), `VSS` (inout), `IN` (input), `CLK` (input), `OUT` (output) — all `electrical`
- **Parameters**:
  - `vth` (real, default 0.45): logic threshold in volts
  - `tedge` (real, default 100p): output transition time in seconds
- **Behavior**:
  - On the **rising edge** of `CLK` (when `V(CLK)` crosses `vth` upward), sample `V(IN)` and hold it.
  - `V(OUT)` reflects the held value via `transition()`.
  - Between clock edges, `V(OUT)` remains constant.
- **Output**: use `transition()` — do NOT use `idt()`, `ddt()`, or `I() <+`.

## Constraints

- Pure voltage-domain only (`V() <+`, `@(cross(...))`, `transition()`, `@(initial_step)`).
- No current-domain constructs.
- Initialize `held` to 0.0 in `@(initial_step)`.
- Use `$strobe` to log each sample event.

## Deliverable

A single `.va` file: `sample_hold.va`.
