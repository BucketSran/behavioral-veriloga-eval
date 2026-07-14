# BBPD Data Edge Alignment

## Task Contract

Implement the requested Verilog-A artifact for `BBPD Data Edge Alignment`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing_systems`
- Target artifact(s): `bbpd_data_edge_alignment_ref.va`

Implement `bbpd_data_edge_alignment_ref.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module bbpd_data_edge_alignment_ref(vdd, vss, clk, data, up, dn, retimed_data);
```

## Public Parameter Contract

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `vth` | `0.45` | V | Logic threshold for `clk` and `data` relative to `vss`. |
| `trf` | `30 ps` | time, `(0:inf)` | Rise/fall smoothing for voltage-coded outputs. |
| `clk_period` | `20 ns` | time, `(0:inf)` | Nominal full clock period used to classify data-transition timing. |
| `clk_delay` | `10 ns` | time, `[0:inf)` | Initial phase reference for the clock timing model. |
| `deadzone` | `0.8 ns` | time, `[0:inf)` | Timing region around a clock edge where correction pulses are suppressed. |
| `pulse_w` | `1 ns` | time, `(0:inf)` | Width of each UP or DN correction pulse. |
| `poll_dt` | `50 ps` | time, `(0:inf)` | Timer cadence used to clear expired pulses. |

Support legal overrides of these public parameters.

## Required Behavior

This task asks for the `bbpd_data_edge_alignment_ref` behavioral module, not a
Spectre testbench. The module is a bang-bang phase detector front end that
compares data-transition timing against a voltage-coded clock and emits
short UP/DN correction pulses.

Required observable behavior:

- Use `clk` rising edges to retime the current `data` logic level onto
  `retimed_data`.
- Detect both rising and falling `data` transitions.
- Compare each data-transition time with the previous and next nominal clock
  edge.
- Assert an `up` pulse when the transition is closer to the upcoming clock edge
  and outside the dead zone.
- Assert a `dn` pulse when the transition is closer to the previous clock edge
  and outside the dead zone.
- Suppress both correction pulses for transitions inside the dead zone.
- Keep UP and DN mutually exclusive except for analog smoothing overlap.

Use voltage-coded logic referenced to `vdd` and `vss`, keep the model pure
behavioral Verilog-A, and do not use transistor-level devices, AC/noise
analysis, validation logic, validation-only hooks, or simulator-specific side
channels.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `bbpd_data_edge_alignment_ref.va`.
Companion support files are supplied by the verification harness for this task.
