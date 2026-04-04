# Task: gray_counter_4b_smoke

## Objective

Write a Verilog-A behavioral module for a **4-bit Gray Code Counter**.

## Specification

- **Module name**: `gray_counter_4b`
- **Ports**: `VDD` (inout), `VSS` (inout), `CLK` (input), `EN` (input), `RSTB` (input), `G3`..`G0` (output) — all `electrical`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - On each rising `CLK` edge, if `EN=1` and `RSTB=1`, increment a 4-bit binary counter (mod 16).
  - Convert binary to Gray code: `gray = bin ^ (bin >> 1)`.
  - Drive `G3..G0` with the Gray-coded output.
  - `RSTB` low (active-low reset) resets counter to 0 synchronously or asynchronously.
- **Output**: use `transition()` only. No `idt` or current domain.

## Constraints

- Pure voltage-domain. One `integer` for binary counter, one for gray value.
- Use `$strobe` on each clock event.

## Deliverable

A single `.va` file: `gray_counter_4b.va`.
