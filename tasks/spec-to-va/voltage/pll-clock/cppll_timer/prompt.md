Write a timer-based charge-pump style PLL (CPPLL) behavioral model in Verilog-A.

Module name: `cppll_timer_ref`.

Behavioral intent:

- one reference clock input `ref_clk`
- one divided feedback clock output `fb_clk`
- one oscillator clock output `dco_clk`
- one monitor output `vctrl_mon` that reflects the loop control voltage
- one lock indicator output `lock`
- a proportional-plus-integral style loop so the divided feedback frequency tracks the reference clock

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(timer(...))` for the DCO timing loop
- use `@(cross(...))` on the reference and feedback clocks to measure phase error
- drive `fb_clk`, `dco_clk`, and `lock` as voltage outputs using `transition(...)`
- keep `vctrl_mon` bounded by the supply rails

Minimum simulation goal for the reference testbench:

- 50 MHz reference clock
- divided feedback frequency matches the reference within a few percent in the late simulation window
- `vctrl_mon` stays within the supply range throughout the transient run

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref_clk`: input electrical
- `fb_clk`: output electrical
- `dco_clk`: output electrical
- `vctrl_mon`: output electrical
- `lock`: output electrical
