Write a Verilog-A module named `adpll_va_idtmod`.

Create a voltage-domain all-digital PLL (ADPLL) behavioral model in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke
simulation.

Behavioral intent:

- one reference clock input `ref_clk`
- one divided feedback clock output `fb_clk`
- one oscillator clock output `dco_clk`
- one monitor node `vctrl_mon` that reflects the digital control code or its
  normalized analog equivalent
- one lock indicator output `lock`
- the loop should use bang-bang style phase/frequency correction so that the
  divided feedback frequency converges toward the reference frequency

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- `fb_clk`, `dco_clk`, and `lock` should be driven as voltage outputs
- `ref_clk`, `fb_clk`, `lock`, and `vctrl_mon` must appear in the waveform CSV
- either `@(timer(...))` or `idtmod()` is acceptable for the DCO, as long as
  the model is EVAS-compatible and the closed loop locks in simulation

Minimum simulation goal:

- the generated testbench should stimulate a 50 MHz reference clock
- the late-window `fb_clk` edge rate should match `ref_clk` within a small
  tolerance
- `lock` should assert during the transient run

Expected behavior:
- ADPLL should lock to reference clock
- fb_clk frequency should match ref_clk frequency when locked
- lock signal should go high after lock achieved
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref_clk`: input electrical
- `fb_clk`: output electrical
- `dco_clk`: output electrical
- `vctrl_mon`: output electrical
- `lock`: output electrical
