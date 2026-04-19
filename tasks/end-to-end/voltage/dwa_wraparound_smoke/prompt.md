# Task: dwa_wraparound_smoke

Write a pure voltage-domain Verilog-A DWA pointer generator that rotates a
16-cell thermometer selection window by the input 4-bit code on every rising
clock edge.

The smoke test must stress pointer wraparound. Starting from pointer index 13,
the first non-reset update must wrap through cell 15 back to cell 0, and later
updates must include at least one more wraparound. The pointer output must be
one-hot after reset, and the active cell count must match the requested code on
each sampled cycle.

Constraints:

- Use only voltage-domain `electrical` ports.
- Use `@(cross(..., +1))` for clocked updates.
- Use `transition()` for output contributions.
- Do not use current contributions, `ddt()`, or `idt()`.

Return a DUT and minimal Spectre-compatible testbench that EVAS can run.
