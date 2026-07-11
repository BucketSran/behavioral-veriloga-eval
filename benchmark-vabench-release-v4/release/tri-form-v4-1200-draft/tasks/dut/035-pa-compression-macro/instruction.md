# PA Compression Macro

## Task Contract

Implement the requested Verilog-A artifact for `PA Compression Macro`.
- Form: `dut`
- Level: `L1`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `pa_compression_macro.va`

Implement `pa_compression_macro.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `pa_compression_macro(clk, rst, vin, out, metric)`:

```verilog
module pa_compression_macro(
    clk, rst, vin, out, metric
);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

`clk` and `rst` are voltage-coded logic signals with low `0 V`, high `0.9 V`,
and threshold `0.45 V`. `vin` is a PA drive voltage around `0.45 V` common
mode. `out` is the amplified output with large-signal compression. `metric`
marks compression or limiting operation.

## Public Parameter Contract

- `tr`: output transition time, default `100p`.
- `vth`: logic threshold, default `0.45`.
- `gain`: moderate-drive voltage gain, default `3.0`.

## Required Behavior

- Initialize `out` to the 0.45 V common-mode level and `metric` to `0 V`.
- Update the held output state on rising `clk` crossings through `vth`.
- When `rst` is high, return the output to common mode and clear `metric`.
- Treat `x = V(vin) - 0.45 V` as the signed drive and compute `drive = 0.45 + gain * x`.
- In the moderate-drive region, `0.12 V <= drive <= 0.78 V`, drive `out = drive` and `metric = 0.1 V`.
- For high-side compression, when `drive > 0.78 V`, drive `out = 0.78 + 0.18 * (drive - 0.78)` and `metric = 0.85 V`.
- For low-side compression, when `drive < 0.12 V`, drive `out = 0.12 + 0.18 * (drive - 0.12)` and `metric = 0.85 V`.
- Clamp the output to `[0.02 V, 0.88 V]`.

The visible testbench is a public verification scenario for wiring and saved
observables. Do not hard-code its transient stop time, waveform breakpoints, or
sample windows into the DUT.

## Modeling Constraints

Return only `pa_compression_macro.va`. Do not emit a Spectre testbench, validation harness
logic, validation-only hooks, or simulator-specific side channels. Use voltage
contributions only; do not use current contributions, transistor-level devices,
RF S-parameters, AC/noise analysis, or KCL/KVL assumptions. Use a clocked state
update and drive output voltages through `transition(...)`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `pa_compression_macro.va`. Do not include explanatory prose outside the source artifact contents.
