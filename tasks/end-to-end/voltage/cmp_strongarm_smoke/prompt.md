# Task: cmp_strongarm_smoke

## Objective

Write a Verilog-A behavioral model for a clocked StrongARM-style comparator that flips decision polarity when the differential input polarity swaps.

## Specification

- **Module name**: `cmp_strongarm`
- **Ports**: `CLK`, `VINN`, `VINP`, `DCMPN`, `DCMPP`, `LP`, `LM`, `VSS`, `VDD` - all `electrical`
- **Behavior**:
  - Detect the active clock edge and resolve a latched differential comparison.
  - When `VINP > VINN`, drive `DCMPP` HIGH and `DCMPN` LOW.
  - When `VINP < VINN`, drive `DCMPP` LOW and `DCMPN` HIGH.
  - Outputs should show finite transitions and nontrivial toggling over the transient.

## Constraints

- Pure voltage-domain only.
- Use `@(cross(...))`, `@(initial_step)`, and `transition()` where appropriate.
- Do not use current-domain operators such as `I() <+` or `ddt()`.
- Keep the model EVAS-compatible.

## Deliverable

A single `.va` file: `cmp_strongarm.va`.
