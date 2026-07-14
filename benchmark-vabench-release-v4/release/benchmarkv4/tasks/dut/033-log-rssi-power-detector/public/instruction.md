# Log RSSI Power Detector

## Task Contract

Implement the requested Verilog-A artifact for `Log RSSI Power Detector`.
- Form: `dut`
- Level: `L1`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `log_rssi_power_detector.va`

- Target artifact: `log_rssi_power_detector.va`
- Implement only the requested Verilog-A DUT. Do not generate a testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

Declare module `log_rssi_power_detector` with positional ports `clk, rst, vin, out, metric`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `vin` is the analog input around the common-mode level, `out` is the RSSI voltage, and `metric` is an amplitude-related observable.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: output transition rise/fall smoothing time.
- `vth = 0.45 V`: logic threshold for `clk` and `rst`.

## Required Behavior

- Initialize and reset RSSI output to `0.12 V` and `metric` to `0 V`.
- On each rising `clk` crossing through `vth`, sample the input magnitude unless reset is active.
- Measure input magnitude as `amp = abs(V(vin) - 0.45 V)`.
- Map `amp < 0.035 V` to `out = 0.12 V`.
- Map `0.035 V <= amp < 0.11 V` to `out = 0.30 V`.
- Map `0.11 V <= amp < 0.22 V` to `out = 0.54 V`.
- Map `amp >= 0.22 V` to `out = 0.72 V`.
- Clamp the RSSI output to `[0.08 V, 0.82 V]`.
- Drive `metric = 3.0 * amp`, clamped to `[0 V, 0.9 V]`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `log_rssi_power_detector.va`. Do not include explanatory prose outside the source artifact contents.
