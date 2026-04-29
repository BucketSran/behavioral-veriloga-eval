Write a Verilog-A module named `comparator`.

Create a voltage-domain comparator in Verilog-A, then produce a minimal EVAS
testbench and run a smoke simulation.

Behavioral intent:

- differential comparison
- output toggles high/low with supply-referenced logic levels
- finite output edge transition
- threshold crossing should be visible in the waveform

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VINP`: input electrical
- `VINN`: input electrical
- `OUT_P`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=30n maxstep=0.5n
```

Required public waveform columns in `tran.csv`:

- `vinp`, `vinn`, `out_p`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `vinp`, `vinn`.
