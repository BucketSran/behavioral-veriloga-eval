# Task: serializer_8b_smoke

## Objective

Write a Verilog-A behavioral module for an **8-bit Parallel-to-Serial Converter**.

## Specification

- **Module name**: `serializer_8b`
- **Ports**: `VDD` (inout), `VSS` (inout), `D7`..`D0` (input), `LOAD` (input), `CLK` (input), `SOUT` (output) — all `electrical`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Rising edge of `LOAD`: latch `D7..D0` into an internal 8-bit shift register, MSB first. Reset bit counter to 0. Drive `SOUT` with the MSB.
  - Rising edge of `CLK` (when `LOAD=0`): shift register left by 1; output next bit (MSB of shifted register) on `SOUT`.
  - After 8 CLK cycles, all bits have been serialized. Behavior is undefined until next LOAD.
- **Output**: use `transition()` only.

## Constraints

- Pure voltage-domain. One `integer` for the shift register value (8-bit), one for bit counter.
- Use `$strobe` on LOAD and each SHIFT event.

## Deliverable

A single `.va` file: `serializer_8b.va`.
