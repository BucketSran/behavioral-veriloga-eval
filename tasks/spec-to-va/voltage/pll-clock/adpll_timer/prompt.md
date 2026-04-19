Write a timer-based all-digital PLL (ADPLL) behavioral model in Verilog-A.

Behavioral intent:

- one reference clock input `ref_clk`
- one divided feedback clock output `fb_clk`
- one oscillator clock output `dco_clk`
- one monitor output `vctrl_mon` that reflects the digital control code or its normalized analog equivalent
- one lock indicator output `lock`
- a bang-bang style correction loop so the divided feedback frequency converges toward the reference clock

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(timer(...))` for the DCO timing loop, not `idtmod()`
- `fb_clk`, `dco_clk`, and `lock` should be driven as voltage outputs using `transition(...)`
- use `@(cross(...))` on the reference and feedback clocks to update the control state

Minimum simulation goal for the reference testbench:

- 50 MHz reference clock
- divided feedback frequency matches the reference in the late simulation window
- `lock` asserts during the transient run
