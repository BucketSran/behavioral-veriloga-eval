Write a Verilog-A module named `lfsr`.

Create a voltage-domain 31-bit Linear Feedback Shift Register (LFSR) in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- one input clock `clk`, one active-low reset `rstb`, one enable `en`, power rails `vdd` / `vss`
- one digital output node `dpn` driven from the MSB of the shift register
- on reset (rstb low), initialize the register from a `seed` parameter
- on each rising edge of `clk` with `rstb` high, advance the LFSR using the
  maximal-length polynomial for n=31: taps at positions 31, 21, 1, 0
- `dpn` should follow the MSB of the register via a voltage-level transition

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock and reset edge detection
- use `transition(...)` to drive `dpn`
- `clk`, `dpn`, and `rstb` must appear in the waveform CSV

Minimum simulation goal:

- seed=123, clock 1 GHz, reset deasserts at ~101 ns, run for 500 ns
- after reset, `dpn` must toggle at least 10 times (not stuck HIGH or LOW)
- high fraction of `dpn` must be between 5% and 95%

Ports:
- `DPN`: output electrical
- `VDD`: inout electrical
- `VSS`: inout electrical
- `CLK`: input electrical
- `EN`: input electrical
- `RSTB`: input electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=500n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `dpn`, `rstb`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rstb` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Enable-like input(s) `en`, `enable` must be in the enabled state during the post-reset checking window unless the task explicitly asks for disabled intervals.
- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `rstb`, `en`.
