Write a Verilog-A module named `clk_burst_gen`.

Create a voltage-domain clock burst generator in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- one input clock `CLK`, one active-low reset `RST_N`, one output clock `CLK_OUT`
- parameter `div` (integer, ≥ 3) sets the burst period in input clock cycles
- on each burst period, `CLK_OUT` mirrors `CLK` for only the first 2 cycles,
  then stays low until the period resets
- active-low reset restarts the counter and suppresses output

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock rising and falling edge detection
- use `transition(...)` to drive `CLK_OUT`
- `CLK`, `RST_N`, and `CLK_OUT` must appear in the waveform CSV

Minimum simulation goal:

- input clock 100 ns period, div=8, reset deasserts at ~235 ns, run for 3000 ns
- after reset, `CLK_OUT` must be present (max voltage > 0.8 V)
- `CLK_OUT` high fraction over the active window must be less than 50%
  (burst mode: only 2 out of 8 cycles pass through)

Ports:
- `CLK`: input electrical
- `RST_N`: input electrical
- `CLK_OUT`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=3000n maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `CLK`, `RST_N`, `CLK_OUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `RST_N` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `CLK`, `RST_N`.
