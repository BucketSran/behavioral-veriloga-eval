# Task: dwa_ptr_gen_no_overlap_smoke

## Objective

Write a Verilog-A behavioral model for a DWA pointer generator whose consecutive activation windows do not overlap.

## Specification

- **Module name**: `dwa_ptr_gen_no_overlap`
- **Behavior**:
  - Sample a 4-bit input code on clock edges.
  - Maintain a rotating pointer across 16 cells.
  - Produce `cell_en_*` outputs that activate cells according to the sampled code.
  - Consecutive cycles must not reuse the same enabled cell set.
  - Expose `ptr_*` outputs so the pointer state is observable in transient simulation.

## Constraints

- Pure voltage-domain only.
- Use EVAS-compatible event-driven logic such as `@(cross(...))`, `@(initial_step)`, and `transition()`.
- Do not use current-domain constructs.
- Keep reset behavior explicit and deterministic.

## Deliverable

A single `.va` file: `dwa_ptr_gen_no_overlap.va`.
