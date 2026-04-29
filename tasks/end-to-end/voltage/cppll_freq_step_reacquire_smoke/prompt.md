Write a Verilog-A module named `cppll_timer_ref`.

Create a timer-based voltage-domain charge-pump style PLL (CPPLL) behavioral
model in Verilog-A, then produce a minimal EVAS-compatible Spectre testbench
that demonstrates unlock and reacquire behavior after a reference-frequency
step.

Return code blocks only. Do not include explanations or design discussion
outside the code blocks.

Return exactly two fenced code blocks:

1. A `verilog-a` block for `cppll_timer_ref.va`
2. A `spectre` block for `tb_cppll_freq_step_reacquire.scs`

Keep the code compact enough that both required blocks are emitted completely.

Behavioral intent:

- one reference clock input `ref_clk`
- one divided feedback clock output `fb_clk`
- one oscillator clock output `dco_clk`
- one monitor node `vctrl_mon` that reflects the loop control voltage
- one lock indicator output `lock`
- the loop should first lock to an initial reference, lose lock after a
  moderate reference-frequency change, then reacquire and track the new late
  frequency

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(timer(...))` for the DCO timing loop
- `fb_clk`, `dco_clk`, and `lock` should be driven as voltage outputs
- `ref_clk`, `fb_clk`, `lock`, and `vctrl_mon` must appear in the waveform CSV

Minimum simulation goal:

- the generated testbench should step the reference clock from 50 MHz to about
  51.28 MHz during the transient
- `lock` should show a pre-step lock event and at least one post-step relock
  event after the disturbance
- the late-window `fb_clk` frequency should match the stepped reference within a
  few percent
- `vctrl_mon` should stay bounded by the supply rails throughout the transient

Expected behavior:
- PLL should achieve lock before disturbance (lock goes high)
- After disturbance, PLL should re-lock within reasonable time
- Late frequency ratio (ref_period/fb_period) should be close to 1.0 when locked
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
tran tran stop=6u maxstep=5n errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `ref_clk`, `fb_clk`, `lock`, `vctrl_mon`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `ref_clk`, `dco_clk`, `fb_clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`.
