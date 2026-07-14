# Amplifier Filter Chain

## Task Contract

Implement the requested Verilog-A artifact for `Amplifier Filter Chain`.
- Form: `dut`
- Level: `L2`
- Category: `baseband_signal_conditioning`
- Target artifact(s): `amplifier_filter_chain.va`

Implement `amplifier_filter_chain.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module amplifier_filter_chain(clk, rst, vin, out, metric, preamp_mon, filt1_mon, filt2_mon, settle_metric);
```

Declare `clk`, `rst`, and `vin` as inputs and `out`, `metric`,
`preamp_mon`, `filt1_mon`, `filt2_mon`, and `settle_metric` as outputs. All
ports are scalar electrical voltage-domain ports. `clk` and `rst` are
voltage-coded logic signals with a `0.45 V` threshold.

## Public Parameter Contract

- `tr`: output transition smoothing time, default `100p`.
- `gain`: pre-filter gain around the `0.45 V` common-mode level, default `1.8`.
- `alpha`: sampled low-pass update coefficient for each cascaded filter state,
  default `0.30`.

## Required Behavior

- Implement a composed baseband conditioning block: a bounded gain stage
  followed by two cascaded sampled low-pass states.
- Initialize the pre-filter target, both filter states, `out`, `metric`,
  `preamp_mon`, `filt1_mon`, and `filt2_mon` near `0.45 V`; initialize
  `settle_metric` low.
- On each rising `clk` crossing, update the chain. While `rst` is active high,
  reset the chain to the initial common-mode state.
- When reset is low, form a pre-filter target by amplifying `vin` around
  `0.45 V` as `target = gain * (vin - 0.45) + 0.45`, then clamp the target to
  `[0 V, 0.9 V]`.
- Drive `metric` and `preamp_mon` exactly from the bounded pre-filter target.
- Update the first sampled low-pass state as `s1_next = s1 + alpha * (target - s1)`.
- Update the second sampled low-pass state after the first update as
  `s2_next = s2 + alpha * (s1_next - s2)`.
- Drive `filt1_mon` and `filt2_mon` from those two cascaded low-pass states.
- Drive `out` from the second filtered state so it visibly lags the pre-filter
  target during large input changes.
- Drive `settle_metric` as a voltage-coded settled-status output: high when
  `abs(out - target) < 0.16 V` and low while the chain is still recovering.
  Use 0.9 V for the settled level and 0.1 V for the recovering level.

The validation scenario is a public verification scenario for wiring and saved
observables. Do not hard-code its transient stop time, waveform breakpoints, or
sample windows into the DUT.

## Modeling Constraints

Return only `amplifier_filter_chain.va`. Do not emit a testbench,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, transistor-level
devices, AC/noise analysis, `ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `amplifier_filter_chain.va`. Do not include explanatory prose outside the source artifact contents.
