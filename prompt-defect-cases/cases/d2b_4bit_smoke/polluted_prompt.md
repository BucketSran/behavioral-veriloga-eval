Write a Verilog-A module named `d2b_4bit`.

Create a 4-bit static analog-to-binary converter in Verilog-A, then produce a
minimal EVAS testbench and run a smoke simulation.

Behavioral intent:

- continuous tracking, no clock
- analog input over the VSS-to-VDD range
- 4-bit digital output bus
- output code should increase as input voltage increases

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VIN`: input electrical
- `DOUT3`: output electrical
- `DOUT2`: output electrical
- `DOUT1`: output electrical
- `DOUT0`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=100n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `vin`, `DOUT3`, `DOUT2`, `DOUT1`, `DOUT0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `vin`.
