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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=300n maxstep=10p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `ref`, `div`, `up`, `dn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `ref`, `div`.
