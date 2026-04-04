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
