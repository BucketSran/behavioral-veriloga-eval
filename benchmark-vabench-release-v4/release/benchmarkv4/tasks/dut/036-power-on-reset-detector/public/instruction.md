# Power-On Reset Detector

## Task Contract

Implement the requested Verilog-A artifact for `Power On Reset Detector`.
- Form: `dut`
- Level: `L1`
- Category: `bias_reference_power_management`
- Target artifact(s): `power_on_reset_detector.va`

- Target artifact: `power_on_reset_detector.va`
- Implement only the requested Verilog-A DUT. Do not generate a testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

```verilog
module power_on_reset_detector(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: output transition rise/fall smoothing time.
- `vth = 0.45 V`: voltage-coded logic threshold for `clk` and `rst`.
- `vtrip = 0.62 V`: monitored supply-good threshold for `vin`.

## Required Behavior

- `clk` and `rst` are voltage-coded logic signals.
- Treat `vin` as the monitored supply ramp and brownout stimulus.
- `out` is an active-high reset voltage.
- Keep `out` reset-asserted high while reset input is high or `vin` is below the supply-good threshold.
- After `vin` is power-good and reset is released, wait four rising clock updates before deasserting `out` low.
- During the release delay, drive `metric` to an intermediate status level; after release, drive `metric` high.
- If the supply falls below `vtrip` or `rst` rises above `vth`, assert `out` high and clear the release delay immediately, independent of the next clock edge.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `power_on_reset_detector.va`.
Do not include explanatory prose outside the source artifact contents.
