# ADPLL Ratio Hop Timer

## Task Contract

Implement the requested Verilog-A artifact for `ADPLL Ratio Hop Timer`.
- Form: `dut`
- Level: `L2`
- Category: `pll_clock_timing_systems`
- Target artifact(s): `adpll_ratio_hop_ref.va`

Implement `adpll_ratio_hop_ref.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module adpll_ratio_hop_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    input  electrical ratio_ctrl,
    output electrical fb_clk,
    output electrical vout,
    output electrical vctrl_mon,
    output electrical lock
);
```

## Public Parameter Contract

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `f_center` | `240.0e6` | Hz, `(0:inf)` | DCO center frequency near the nominal control code. |
| `freq_step_hz` | `5.0e6` | Hz/code, `(0:inf)` | DCO frequency change per control-code step. |
| `f_min` | `120.0e6` | Hz, `(0:inf)` | Lower clamp for the generated DCO frequency. |
| `f_max` | `420.0e6` | Hz, `(0:inf)` | Upper clamp for the generated DCO frequency. |
| `code_min` | `0` | integer, `[0:inf)` | Minimum loop-control code. |
| `code_max` | `63` | integer, `[1:inf)` | Maximum loop-control code. |
| `code_center` | `32` | integer, `[0:inf)` | Code corresponding to the nominal DCO center. |
| `code_init` | `24` | integer, `[0:inf)` | Initial loop-control code. |
| `ratio_min` | `2` | integer, `[1:inf)` | Minimum allowed feedback divide ratio. |
| `ratio_max` | `16` | integer, `[2:inf)` | Maximum allowed feedback divide ratio. |
| `tedge` | `200 ps` | time, `(0:inf)` | Rise/fall smoothing for voltage-coded outputs. |
| `lock_tol` | `2 ns` | time, `(0:inf)` | Timing-error tolerance used for lock qualification. |
| `lock_count_target` | `5` | integer, `[1:inf)` | Consecutive in-tolerance feedback events before asserting `lock`. |

Support legal overrides of these public parameters.

## Required Behavior

This task asks for the `adpll_ratio_hop_ref` behavioral module, not a Spectre
testbench. The module models an ADPLL timing loop that locks to a reference,
responds to a commanded divider-ratio hop, and reacquires lock after the hop.

Required observable behavior:

- Use `ref_clk` as the reference timing input.
- Interpret `ratio_ctrl` as a voltage-coded requested feedback divide ratio in
  volts: round `V(ratio_ctrl)` to the nearest integer with half-step boundaries,
  then clip the requested ratio to the inclusive `ratio_min` through `ratio_max`
  range. Legal overrides of `ratio_min` and `ratio_max` must extend this
  encoding rather than limiting it to the default 2-through-16 range.
- Generate a behavioral DCO clock on `vout`.
- Generate `fb_clk` by dividing the DCO activity according to the requested
  ratio.
- Adjust a bounded internal control code from reference/feedback timing error
  rather than driving `fb_clk` from an independent source.
- Drive `vctrl_mon` as a rail-referenced monitor of the bounded loop-control
  state.
- Assert `lock` after stable pre-hop tracking, deassert or lose qualification
  during a ratio hop, and assert again after reacquisition.
- Keep generated frequencies within `f_min` and `f_max`; use appropriate
  timestep guidance such as `$bound_step` for oscillator timing.

Use voltage-coded logic with a mid-supply decision threshold where applicable,
drive high logic outputs near `VDD` and low outputs near `VSS`, and keep the
model pure behavioral Verilog-A. Do not use transistor-level devices, AC/noise
analysis, validation logic, validation-only hooks, or simulator-specific side
channels.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `adpll_ratio_hop_ref.va`. Companion
support files are supplied by the verification harness for this task.
