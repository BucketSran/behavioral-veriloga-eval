# Limiting Amplifier Frontend

## Task Contract

Implement the requested Verilog-A artifact for `Limiting Amplifier Frontend`.
- Form: `dut`
- Level: `L1`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `limiting_amplifier_frontend.va`

- Target artifact: `limiting_amplifier_frontend.va`
- Implement only the requested Verilog-A DUT. Do not generate a testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

Declare module `limiting_amplifier_frontend` with positional ports `clk, rst, vin, out, metric`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `vin` is the analog input around the common-mode level, `out` is the limited amplifier output, and `metric` reports limiting activity.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: output transition rise/fall smoothing time.
- `vth = 0.45 V`: logic threshold for `clk` and `rst`.

## Required Behavior

- Initialize `out` to `0.45 V` and `metric` to `0 V`.
- On each rising `clk` crossing through `vth`, sample `vin` unless reset is active.
- On a rising `clk` crossing where `rst` is above `vth`, reset `out` to `0.45 V` and clear `metric` to `0 V`; reset is sampled synchronously with `clk`.
- Treat `x = V(vin) - 0.45 V` as the signed input.
- In the central linear region, when `-0.09 V <= x <= 0.09 V`, drive `out = 0.45 + 1.7 * x` and `metric = 0 V`.
- In the positive limiting region, when `x > 0.09 V`, drive `out = 0.73 + 0.45 * (x - 0.09)` and `metric = 0.85 V`.
- In the negative limiting region, when `x < -0.09 V`, drive `out = 0.17 + 0.45 * (x + 0.09)` and `metric = 0.85 V`.
- Clamp the output to `[0.04 V, 0.86 V]`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `limiting_amplifier_frontend.va`. Do not include explanatory prose outside the source artifact contents.
