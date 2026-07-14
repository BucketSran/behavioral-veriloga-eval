# Bias Voltage Generator With Enable/Trim

## Task Contract

Implement the requested Verilog-A artifact for `Bias Voltage Generator With Enable Trim`.
- Form: `dut`
- Level: `L1`
- Category: `bias_reference_power_management`
- Target artifact(s): `bias_voltage_generator_with_enable_trim.va`

- Target artifact: `bias_voltage_generator_with_enable_trim.va`
- Implement only the requested Verilog-A DUT. Do not generate the validation harness, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

```verilog
Declare module `bias_voltage_generator_with_enable_trim` with the positional ports listed below.
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

## Public Parameter Contract

Starter parameter declarations are part of the public contract:

| Parameter | Default | Contract |
| --- | ---: | --- |
| `tr` | `100p` | Output transition rise/fall time. |
| `vth` | `0.45` | Voltage-coded clock/reset logic threshold. |

## Required Behavior

- `clk` and `rst` are voltage-coded logic signals, low near 0 V and high near 0.9 V.
- Treat `vin` as a combined enable/trim request voltage.
- Update the bias state on rising `clk` crossings through `vth`.
- A high `rst` or `vin < 0.25 V` disables the bias generator: reset `out` to 0 V and drive `metric` to 0 V.
- When enabled, compute the bias target as `0.28 + 0.55 * ((vin - 0.25) / 0.65)` and clamp it to `[0.28 V, 0.82 V]`.
- On each enabled clock update, move the output state toward the target with `out_next = out_prev + 0.45 * (target - out_prev)` instead of jumping directly to the target.
- Higher trim/control voltage should increase `out` monotonically.
- Drive `metric` to 0.9 V while the bias generator is enabled and to 0 V while disabled.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `bias_voltage_generator_with_enable_trim.va`.
Do not include explanatory prose outside the source artifact contents.
