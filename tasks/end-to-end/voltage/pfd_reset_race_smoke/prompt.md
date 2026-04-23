Write a Verilog-A module named `pfd_updn`.

# Task: pfd_reset_race_smoke

Write a pure voltage-domain Verilog-A PFD with `up` and `dn` outputs.

Requirements:

1. Ports must be `electrical`.
2. Rising edge of `ref` asserts `up`.
3. Rising edge of `div` asserts `dn`.
4. If both states become high, the detector must reset both outputs promptly.
5. The reference testbench will apply near-simultaneous `ref` / `div` edges, with the lead/lag relationship swapping during transient.

Expected behavior:
- up and dn pulses should fire when ref and div edges differ
- up and dn should NOT overlap significantly (avoid reset race)
- Each window should show proper pulse behavior
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `REF`: input electrical
- `DIV`: input electrical
- `UP`: output electrical
- `DN`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).
