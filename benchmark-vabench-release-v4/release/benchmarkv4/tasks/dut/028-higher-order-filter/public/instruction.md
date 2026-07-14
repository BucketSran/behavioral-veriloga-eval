# Clocked Cascaded Two-Pole Filter

## Task Contract

Implement the requested Verilog-A artifact for `Clocked Cascaded Two-Pole Filter`.
- Form: `dut`
- Level: `L1`
- Category: `baseband_signal_conditioning`
- Target artifact(s): `higher_order_filter.va`

Implement `higher_order_filter.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `higher_order_filter(clk, rst, vin, out, metric)` with scalar
electrical voltage-domain ports. `clk` and `rst` are voltage-coded logic inputs
with a `0.45 V` threshold.

## Public Parameter Contract

- `tr`: output transition smoothing time, default `100p`.
- `gain`: input deviation gain around the `0.45 V` common-mode level, default
  `1.8`.
- `alpha`: sampled low-pass update coefficient for each cascaded state,
  default `0.18`.

## Required Behavior

- Initialize the two filter states, output state, and metric baseline near
  `0.45 V`.
- On each rising `clk` crossing, update the sampled filter state.
- Treat `rst` as active high when `V(rst) > 0.45`; while reset is active,
  return both filter states and `out` to the common-mode level.
- When reset is low, form a bounded target by amplifying `vin` around the
  `0.45 V` common-mode level, then drive two cascaded sampled low-pass states
  toward that bounded target.
- Drive `out` from the second filtered state, bounded to the signal rails.
- Drive `metric` as a voltage observable of the lag between the cascaded filter
  states, centered around the common-mode level, so the settling transient is
  visible without exposing validation-only sample windows.

The validation scenario is a public verification scenario for wiring and saved
observables. Do not hard-code its transient stop time, waveform breakpoints, or
sample windows into the DUT.

## Modeling Constraints

Return only `higher_order_filter.va`. Do not emit a testbench, validation harness
logic, validation-only hooks, or simulator-specific side channels. Use voltage
contributions only; do not use current contributions or `ddt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `higher_order_filter.va`. Do not include explanatory prose outside the source artifact contents.
