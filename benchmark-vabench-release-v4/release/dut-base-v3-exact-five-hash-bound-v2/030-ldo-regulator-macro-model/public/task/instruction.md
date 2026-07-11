# LDO Regulator Macro Model

## Task Contract

Implement the requested Verilog-A artifact for `LDO Regulator Macro Model`.
- Form: `dut`
- Level: `L1`
- Category: `bias_reference_power_management`
- Target artifact(s): `ldo_regulator_macro_model.va`

- Target artifact: `ldo_regulator_macro_model.va`
- Implement only the requested Verilog-A DUT. Do not generate a Spectre testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

```verilog
module ldo_regulator_macro_model(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: output transition rise/fall smoothing time.
- `vth = 0.45 V`: voltage-coded logic threshold for `clk` and `rst`.

## Required Behavior

- `clk` and `rst` are voltage-coded logic signals.
- Treat `vin` as a bounded load/disturbance-control voltage, not as the regulator supply rail.
- Initialize and reset the regulated state to `out = 0.60 V` and `metric = 0.9 V`.
- On each rising `clk` crossing through `vth`, clamp `load = V(vin)` to `[0 V, 0.9 V]` and compute the regulation target as `target = 0.62 - 0.055 * load`.
- Update the regulated output state as `out_next = out_prev + 0.35 * (target - out_prev)`.
- Clamp the regulated output state to `[0.25 V, 0.75 V]` before driving `out`.
- Drive `metric = 0.9 - 4.0 * abs(out - target)`, clamped to `[0 V, 0.9 V]`, so regulation error lowers the metric during droop and recovery.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `ldo_regulator_macro_model.va`.
Do not include explanatory prose outside the source artifact contents.
