# UVLO Brownout Detector

## Task Contract

Implement the requested Verilog-A artifact for `UVLO Brownout Detector`.
- Form: `dut`
- Level: `L1`
- Category: `bias_reference_power_management`
- Target artifact(s): `uvlo_brownout_detector.va`

Implement a clocked voltage-domain undervoltage-lockout and brownout detector. Return only the requested DUT artifact; do not generate the validation harness.

## Public Verilog-A Interface

```verilog
Declare module `uvlo_brownout_detector` with the positional ports listed below.
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
- Treat `vin` as the monitored supply voltage.
- Assert the power-good output `out` high only on a sampled clock update where `vin > 0.65 V`.
- Preserve the previous `out` state on sampled clock updates where `0.55 V <= vin <= 0.65 V`.
- Clear `out` low on reset or on a sampled clock update where `vin < 0.55 V`.
- Drive `metric` as a public status code: `0.1 V` when `out` is power-good high, and `0.9 V` when reset, undervoltage, or brownout is active.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `uvlo_brownout_detector.va`.
Do not include explanatory prose outside the source artifact contents.
