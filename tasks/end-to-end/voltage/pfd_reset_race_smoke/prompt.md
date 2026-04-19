# Task: pfd_reset_race_smoke

Write a pure voltage-domain Verilog-A PFD with `up` and `dn` outputs.

Requirements:

1. Ports must be `electrical`.
2. Rising edge of `ref` asserts `up`.
3. Rising edge of `div` asserts `dn`.
4. If both states become high, the detector must reset both outputs promptly.
5. The reference testbench will apply near-simultaneous `ref` / `div` edges, with the lead/lag relationship swapping during transient.

Use `@(cross())` for edge detection and `transition()` for output waveforms.
