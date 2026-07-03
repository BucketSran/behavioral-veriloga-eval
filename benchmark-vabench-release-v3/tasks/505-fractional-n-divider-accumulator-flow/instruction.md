# Fractional-N Divider Accumulator Flow

Implement `fracn_pll_timer_ref.va` in Verilog-A.

## Interface

```verilog
module fracn_pll_timer_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    output electrical fb_clk,
    output electrical dco_clk,
    output electrical vctrl_mon,
    output electrical lock
);
```

## Required Behavior

This task asks for the `fracn_pll_timer_ref` behavioral module, not a Spectre
testbench. The harness supplies a reference-step clock source and instantiates
your module in a fractional-N PLL tracking/reacquire scenario.

This is a behavioral continuous-time task. Do not use `I(...)`, `ddt(...)`, or
`idt(...)`. Use voltage contributions only.

Support these public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `div_int` | `8` | integer, `[1:inf)` | Base integer division ratio. |
| `frac_word` | `3` | integer, `[0:acc_modulus)` | Fractional accumulator increment per feedback edge. Must be strictly less than `acc_modulus`; out-of-range overrides are clamped into `[0, acc_modulus)` so the swallow-one-per-overflow pattern stays well-defined. |
| `acc_modulus` | `8` | integer, `[1:inf)` | Fractional accumulator modulus. The effective average divide ratio is `div_int - frac_word/acc_modulus` (e.g. `8 - 3/8 = 7.625` with the defaults); this only holds for `0 <= frac_word < acc_modulus`. |
| `f_center` | `800.0e6` | Hz, `(0:inf)` | DCO center frequency at the common-mode control voltage. |
| `kvco_hz_per_v` | `350.0e6` | Hz/V, `(0:inf)` | DCO frequency sensitivity to `vctrl_mon`. |
| `f_min` | `300.0e6` | Hz, `(0:inf)` | Lower clamp for generated DCO frequency. |
| `f_max` | `1.6e9` | Hz, `(0:inf)` | Upper clamp for generated DCO frequency. |
| `kp` | `8.0e6` | nonnegative loop scale, `[0:inf)` | Proportional phase-error correction scale. |
| `ki` | `1.2e5` | nonnegative loop scale, `[0:inf)` | Accumulated phase-error correction scale. |
| `integ_min` | `-0.45` | V-equivalent correction | Lower bound for the integral correction state. |
| `integ_max` | `0.45` | V-equivalent correction | Upper bound for the integral correction state. |
| `vctrl_init` | `0.45` | V | Initial control-voltage monitor value before tracking settles. |
| `tedge` | `20 ps` | time, `(0:inf)` | Rise/fall smoothing for voltage-coded outputs. |
| `lock_tol` | `0.4 ns` | time, `(0:inf)` | Phase-error tolerance for counting lock streaks. |
| `lock_count_target` | `6` | integer, `[1:inf)` | Consecutive in-tolerance events before asserting `lock`. |

Required observable behavior:

- Use `ref_clk` as the reference timing input.
- Generate a behavioral DCO clock on `dco_clk`.
- Generate `fb_clk` by dividing the DCO with an effective ratio that is dithered
  by a fractional accumulator: maintain an accumulator that increments by
  `frac_word` on each feedback edge; on overflow (modulo `acc_modulus`) swallow
  one DCO cycle so the **next** divide count is `div_int - 1` (the swallow takes
  effect on the feedback cycle *after* the overflow edge), otherwise `div_int`.
  The long-run average DCO-to-fb divide ratio is `div_int - frac_word/acc_modulus`
  and is checked behaviorally in the late window (after the reference step).
- Update a bounded control-voltage monitor on `vctrl_mon` from the PFD phase
  error (proportional + bounded integral).
- Drive `lock` high after stable tracking, low or unstable during the
  reference-frequency disturbance, and high again after reacquisition.

Use voltage-coded logic with a mid-supply decision threshold where applicable,
drive high logic outputs near `VDD` and low outputs near `VSS`. Keep the model
pure behavioral Verilog-A. Do not use transistor-level devices or AC/noise
analysis.

## Support clock (`ref_step_clk.va`)

This task supplies a companion support artifact `ref_step_clk.va` that generates
the reference clock with a frequency step; the harness authors it and you do
not. Its public contract is:

```verilog
module ref_step_clk (inout VDD, inout VSS, output CLK);
    parameter real period_pre  = 20n   from (0:inf);
    parameter real period_post = 19.5n from (0:inf);
    parameter real t_switch    = 2u    from (0:inf);
    parameter real tedge       = 100p  from (0:inf);
endmodule
```

`CLK` is a square wave swinging `VSS..VDD` whose half-period is `0.5*period_pre`
before `t_switch` and `0.5*period_post` afterwards. The candidate DUT must
operate correctly for any legal overrides with `period_pre != period_post`.
