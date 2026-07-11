# LNA Gain Compression Macro

## Task Contract

Implement the requested Verilog-A artifact for `LNA Gain Compression Macro`.
- Form: `dut`
- Level: `L1`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `lna_gain_compression_macro.va`

Implement `lna_gain_compression_macro.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `lna_gain_compression_macro(clk, rst, vin, out, metric)`:

```verilog
module lna_gain_compression_macro(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

`clk` and `rst` are voltage-coded logic signals with low `0 V`, high `0.9 V`,
and threshold `0.45 V`. `vin` is a receiver front-end input around `0.45 V`
common mode. `out` is the amplified/compressed voltage. `metric` indicates
whether the macro is operating in compression.

## Public Parameter Contract

- `tr`: output transition time, default `100p`.
- `vth`: logic threshold, default `0.45`.
- `gain`: small-signal voltage gain, default `2.2`.

## Required Behavior

- Initialize `out` to the 0.45 V common-mode level and `metric` low.
- Update the held output state on rising `clk` crossings.
- On a rising `clk` crossing where `rst` is high, return the output to common mode and clear `metric`; reset is sampled synchronously with `clk`.
- Compute the small-signal value as `linear = 0.45 + gain * (V(vin) - 0.45)`.
- In the linear region `0.14 <= linear <= 0.76`, drive `out = linear` and
  drive `metric = 0.1`.
- For positive compression, when `linear > 0.76`, drive
  `out = 0.76 + 0.28 * (linear - 0.76)` and drive `metric = 0.8`.
- For negative compression, when `linear < 0.14`, drive
  `out = 0.14 + 0.28 * (linear - 0.14)` and drive `metric = 0.8`.
- Clamp the final output to the public range `0.04 V <= out <= 0.86 V`.

The visible testbench is a public verification scenario for wiring and saved
observables. Do not hard-code its transient stop time, waveform breakpoints, or
sample windows into the DUT.

## Modeling Constraints

Return only `lna_gain_compression_macro.va`. Do not emit a Spectre testbench,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, transistor-level
devices, AC/noise analysis, or KCL/KVL assumptions. Use a clocked state update
and drive output voltages through `transition(...)`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `lna_gain_compression_macro.va`. Do not include explanatory prose outside the source artifact contents.
