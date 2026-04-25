Write a Verilog-A module named `ramp_gen`.

Create a voltage-domain ramp generator in Verilog-A, then produce a minimal EVAS
testbench and run a smoke simulation.

Behavioral intent:

- resettable ramp code generator
- synchronous to a digital clock
- monotonic increasing code
- output as a 4-bit digital bus

Ports:
- `clk_in`: input electrical
- `rst_n`: input electrical
- `code_3`: output electrical
- `code_2`: output electrical
- `code_1`: output electrical
- `code_0`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=200n maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `clk_in`, `rst_n`, `code_3`, `code_2`, `code_1`, `code_0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `rst_n` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `clk_in`, `rst_n`.
