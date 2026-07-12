# CPPLL Tracking Reacquire Timer

## Task Contract

Implement the requested Verilog-A artifact for `CPPLL Tracking Reacquire Timer`.
- Form: `dut`
- Level: `L2`
- Category: `pll_clock_timing_systems`
- Target artifact(s): `cppll_timer_ref.va`, `ref_step_clk.va`

Implement the two-file DUT bundle in Verilog-A: `cppll_timer_ref.va` and
`ref_step_clk.va`.

## Public Verilog-A Interface

```verilog
module cppll_timer_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    output electrical fb_clk,
    output electrical dco_clk,
    output electrical vctrl_mon,
    output electrical lock
);
```

## Public Parameter Contract

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `div_ratio` | `8` | integer, `[1:inf)` | DCO rising-edge division ratio used to generate `fb_clk`. |
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
| `lock_count_target` | `6` | integer, `[1:inf)` | Number of consecutive in-tolerance events before asserting `lock`. |

Support legal overrides of these public `cppll_timer_ref` parameters.

The bundled reference-step clock module uses public defaults
`period_pre = 20 ns`, `period_post = 19.5 ns`, `t_switch = 2 us`, and
`tedge = 100 ps`. It is a required DUT-bundle artifact for this L2 system
flow, and the CPPLL model must work when a legal nearby reference cadence is
applied on `ref_clk`.

## Required Behavior

This task asks for a two-file DUT bundle: `cppll_timer_ref.va` and
`ref_step_clk.va`, not a Spectre testbench. Both files are scored DUT source
artifacts; preserve their interfaces and overrideable parameters when
returning the bundle.

Required observable behavior:

- Use `ref_clk` as the reference timing input.
- Generate a behavioral DCO clock on `dco_clk`.
- Generate `fb_clk` by dividing the DCO activity according to `div_ratio`.
- Update a bounded control-voltage monitor on `vctrl_mon`.
- Drive `lock` high after stable tracking, low or unstable during the
  reference-frequency disturbance, and high again after reacquisition.
- The late-window relation should show `fb_clk` tracking the new `ref_clk`
  cadence while `vctrl_mon` remains within the supply rails.

Use voltage-coded logic with a mid-supply decision threshold where applicable,
drive high logic outputs near `VDD` and low outputs near `VSS`, and keep the
model pure behavioral Verilog-A. Do not use transistor-level devices, AC/noise
analysis, validation logic, validation-only hooks, or simulator-specific side channels.

`cppll_timer_ref.va` is the primary loop implementation and `ref_step_clk.va`
is the bundled reference-step source used by the flow. Both files are required
source artifacts.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly the requested source artifact(s): `cppll_timer_ref.va`,
`ref_step_clk.va`. Do not include explanatory prose outside the source artifact
contents.
