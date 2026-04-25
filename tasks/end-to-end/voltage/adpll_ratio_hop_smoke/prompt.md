Write a Verilog-A module named `adpll_ratio_hop_ref`.

# Task: adpll_ratio_hop_smoke

Write a pure voltage-domain Verilog-A behavioral ADPLL that uses a timer-driven DCO and a programmable feedback divider.

Requirements:

1. Ports must be `electrical` only.
2. The module must take a reference clock input and an analog `ratio_ctrl` input whose rounded value sets the divider ratio in the range 2 to 16.
3. The DCO frequency must be adjusted by an internal digital control code so the divided feedback clock tracks the reference.
4. Expose:
   - `vout` as the DCO clock output
   - `fb_clk` as the divided feedback clock
   - `vctrl_mon` as a normalized monitor of the control code
   - `lock` as a streak-based lock indicator
5. The reference testbench will step `ratio_ctrl` from 4 to 6 during transient.

Expected behavior:
- When ratio_ctrl ≈ 4V: vout frequency / ref_clk frequency ≈ 4.0 (ratio = divider setting)
- When ratio_ctrl ≈ 6V: vout frequency / ref_clk frequency ≈ 6.0 after ratio hop
- lock signal should be ≥ 80% high before and after the ratio change
- vctrl_mon should stay within [0, 1.2V] range
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref_clk`: input electrical
- `ratio_ctrl`: input electrical
- `fb_clk`: output electrical
- `vout`: output electrical
- `vctrl_mon`: output electrical
- `lock`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=5u maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `ref_clk`, `vout`, `lock`, `vctrl_mon`, `ratio_ctrl`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `ref_clk`, `fb_clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `ref_clk`, `ratio_ctrl`.
