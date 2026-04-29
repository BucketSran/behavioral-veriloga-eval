Write exactly one EVAS/Spectre-compatible Verilog-A module named `adpll_timer_ref`.

Required module signature:

```verilog
module adpll_timer_ref (VDD, VSS, ref_clk, fb_clk, dco_clk, vctrl_mon, lock);
```

The reference testbench instantiates the DUT as:

```spectre
IDUT (vdd vss ref_clk fb_clk dco_clk vctrl_mon lock) adpll_timer_ref \
    div_ratio=8 f_center=760e6 freq_step_hz=5e6 f_min=500e6 f_max=1.2e9 \
    code_min=0 code_max=63 code_center=32 code_init=40 \
    tedge=1n lock_tol=12n lock_count_target=4
```

Interface requirements:

- Keep the exact module name `adpll_timer_ref`.
- Keep the exact port order: `VDD, VSS, ref_clk, fb_clk, dco_clk, vctrl_mon, lock`.
- Declare `VDD` and `VSS` as electrical supply/reference nodes.
- Declare `ref_clk` as an electrical input.
- Declare `fb_clk`, `dco_clk`, `vctrl_mon`, and `lock` as electrical outputs.
- Support these exact parameter names: `div_ratio`, `f_center`, `freq_step_hz`, `f_min`, `f_max`, `code_min`, `code_max`, `code_center`, `code_init`, `tedge`, `lock_tol`, and `lock_count_target`.

Behavioral intent:

- Implement a timer-based all-digital PLL behavioral model.
- Use a DCO timing loop based on `@(timer(t_next_toggle))`, not `idtmod()`.
- Toggle `dco_clk` from the DCO timer.
- Divide DCO rising edges by `div_ratio` to generate `fb_clk`.
-
- Make the divided feedback frequency converge toward the 50 MHz reference clock in the late simulation window.
- Assert `lock` during the transient run after enough consecutive phase errors fall within `lock_tol`.
- Drive `vctrl_mon` as a normalized voltage monitor of the digital control code.

Compatibility constraints:

- Use pure voltage-domain Verilog-A only.
- Put initialization inside `@(initial_step)` within an `analog begin` block.
- Use Spectre-compatible Verilog-A initialization and event syntax.
- Drive `fb_clk`, `dco_clk`, `vctrl_mon`, and `lock` using continuous voltage contributions.
- Keep output contributions Spectre-compatible and continuous in the main analog block.
- Clamp frequency and control-code values to their parameter bounds.

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
tran tran stop=5u maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `ref_clk`, `fb_clk`, `lock`, `vctrl_mon`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
