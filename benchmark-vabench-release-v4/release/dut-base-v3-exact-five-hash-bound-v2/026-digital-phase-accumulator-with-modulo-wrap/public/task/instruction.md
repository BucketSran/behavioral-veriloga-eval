# Digital Phase Accumulator With Modulo Wrap

## Task Contract

Implement the requested Verilog-A artifact for `Digital Phase Accumulator With Modulo Wrap`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `phase_accumulator_timer_wrap_ref.va`

Implement `phase_accumulator_timer_wrap_ref.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module phase_accumulator_timer_wrap_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    output electrical clk_out,
    output electrical phase_out
);
```

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Unit / Range | Contract |
| --- | ---: | --- | --- |
| `dt` | `5 ns` | time, `(0:inf)` | Timer update interval for the phase accumulator. |
| `phase_step` | `0.25` | normalized phase, `(0:1)` | Phase increment per timer update. |
| `tedge` | `200 ps` | time, `(0:inf)` | Rise/fall smoothing for `clk_out` and `phase_out`. |

## Required Behavior

The module is an ADPLL/NCO phase-timing primitive that keeps a wrapped phase state and derives voltage-domain timing outputs.

- Maintain a normalized phase state in `[0, 1)`.
- Advance the phase by `phase_step` on each `dt` timer event.
- Manually wrap phase back into `[0, 1)` instead of letting it grow unbounded.
- Drive `phase_out` as the wrapped phase scaled by the rail voltage
  `V(VDD,VSS)`.
- Drive `clk_out` as a rail-referenced voltage-coded clock derived from the
  wrapped phase: high at `V(VDD,VSS)` when `phase < 0.5`, and low at 0 V when
  `phase >= 0.5`.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `phase_accumulator_timer_wrap_ref.va`.
