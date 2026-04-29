Write a Verilog-A module named `cppll_timer_ref`.

Create a timer-based voltage-domain charge-pump style PLL (CPPLL) behavioral
model in Verilog-A, then produce a minimal EVAS-compatible Spectre testbench
and run a smoke simulation.

Behavioral intent:

- one reference clock input `ref_clk`
- one divided feedback clock output `fb_clk`
- one oscillator clock output `dco_clk`
- one monitor node `vctrl_mon` that reflects the loop control voltage
- one lock indicator output `lock`
- the loop should use proportional-plus-integral style phase correction so that
  the divided feedback frequency tracks the reference clock

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(timer(...))` for the DCO timing loop
- `fb_clk`, `dco_clk`, and `lock` should be driven as voltage outputs
- `ref_clk`, `fb_clk`, `lock`, and `vctrl_mon` must appear in the waveform CSV

Minimum simulation goal:

- the generated testbench should stimulate a 50 MHz reference clock
- the late-window `fb_clk` frequency should match the reference within a few
  percent
- `vctrl_mon` should stay bounded by the supply rails throughout the transient

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref_clk`: input electrical
- `fb_clk`: output electrical
- `dco_clk`: output electrical
- `vctrl_mon`: output electrical
- `lock`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=5u errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `ref_clk`, `fb_clk`, `lock`, `vctrl_mon`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `ref_clk`, `dco_clk`, `fb_clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `ref_clk`.
