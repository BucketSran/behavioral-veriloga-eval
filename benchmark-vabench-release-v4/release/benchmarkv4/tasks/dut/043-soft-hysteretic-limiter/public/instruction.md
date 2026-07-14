# Soft Hysteretic Limiter

## Task Contract

Implement the requested Verilog-A artifact for `Soft Hysteretic Limiter`.
- Form: `dut`
- Level: `L1`
- Category: `baseband_signal_conditioning`
- Target artifact(s): `soft_hysteretic_limiter.va`

Implement `soft_hysteretic_limiter.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `soft_hysteretic_limiter(clk, rst, vin, out, metric)`:

```verilog
Declare module `soft_hysteretic_limiter` with the positional ports listed below.
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

`clk` and `rst` are voltage-coded logic signals with low `0 V`, high `0.9 V`,
and threshold `0.45 V`. `vin` is the analog input. `out` is the conditioned
output voltage. `metric` is a voltage-coded hysteresis-state monitor.

## Public Parameter Contract

- `tr`: output transition smoothing time, default `100p`.
- `gain`: small-signal gain around the `0.45 V` common-mode level, default
  `1.8`.
- `hys_step`: signed hysteresis offset applied after upper/lower threshold
  excursions, default `0.08 V`.

## Required Behavior

- Implement a clocked soft limiter with hysteresis memory around the `0.45 V`
  common-mode level.
- Initialize the held output and state monitor to `0.45 V`, with neutral
  hysteresis offset `0 V`.
- On each rising `clk` crossing, update the held limiter state. While `rst` is
  active high, reset the output and hysteresis state to their neutral
  common-mode values.
- When reset is low, set the hysteresis offset to `+hys_step` after a sampled
  input above `0.62 V`, set it to `-hys_step` after a sampled input below
  `0.38 V`, and otherwise preserve the previous hysteresis offset.
- Compute the held output target as
  `gain * (vin - 0.45 V) + 0.45 V + hysteresis_offset`.
- Clamp the driven `out` voltage to `[0.10 V, 0.82 V]`.
- Drive `metric` as a voltage-coded state monitor:
  `0.45 V + 2.0 * hysteresis_offset`, so the default high- and low-memory
  states produce 0.61 V and 0.29 V respectively.

The public example harness is a public verification scenario for wiring and saved
observables. Do not hard-code its runtime horizon, waveform breakpoints, or
sample windows into the DUT.

## Modeling Constraints

Return only `soft_hysteretic_limiter.va`. Do not emit the validation harness,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, transistor-level
devices, AC/noise analysis, `ddt()`, or `idt()`. Use event-updated state and
`transition(...)` for smoothed voltage outputs.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `soft_hysteretic_limiter.va`. Do not include explanatory prose outside the source artifact contents.
