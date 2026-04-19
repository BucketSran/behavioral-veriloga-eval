# Task: cmp_delay_smoke

## Objective

Write a Verilog-A behavioral model for a clocked comparator whose regeneration delay increases as the differential input magnitude shrinks.

## Specification

- **Module name**: `cmp_delay`
- **Ports**: `CLK`, `VINN`, `VINP`, `DCMPN`, `DCMPP`, `LP`, `LM`, `VSS`, `VDD` - all `electrical`
- **Behavior**:
  - Detect the rising edge of `CLK`.
  - Compare `VINP` and `VINN`.
  - Drive `DCMPP`/`DCMPN` to rail-referenced logic outputs using `transition()`.
  - The positive-output decision must still resolve HIGH in all four positive-polarity phases.
  - The effective decision delay should grow monotonically as `|VINP - VINN|` shrinks from `10 mV` to `0.01 mV`.

## Constraints

- Pure voltage-domain only.
- Use event-driven constructs such as `@(cross(...))`, `@(initial_step)`, and `transition()`.
- Do not use `I() <+`, `ddt()`, or other current-domain operators.
- Keep the implementation EVAS-compatible.

## Deliverable

A single `.va` file: `cmp_delay.va`.
