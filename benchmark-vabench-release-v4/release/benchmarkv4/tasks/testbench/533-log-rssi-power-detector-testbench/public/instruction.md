# Log RSSI Power Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Log RSSI Power Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `log_rssi_power_detector.va`:
  - Module `log_rssi_power_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `log_rssi_power_detector` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `log_rssi_power_detector.tr` defaults to `1e-10` s; valid range: tr > 0; sets rise and fall smoothing for out and metric.
- `log_rssi_power_detector.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets the voltage-coded clk and rst decision threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_BASELINE`: exercise and make observable: Initialization or active reset drives out to 0.12 V and metric to 0 V. Required traces: `time`, `rst`, `out`, `metric`.
- `P_CLOCKED_MAGNITUDE_SAMPLE`: exercise and make observable: Each rising clk crossing while reset is inactive samples the magnitude abs(vin - 0.45 V); the held outputs do not track vin between samples. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_RSSI_BINS`: exercise and make observable: Sampled magnitudes below 0.035 V, from 0.035 V to below 0.11 V, from 0.11 V to below 0.22 V, and at least 0.22 V map to out levels 0.12 V, 0.30 V, 0.54 V, and 0.72 V respectively. Required traces: `time`, `clk`, `vin`, `out`.
- `P_AMPLITUDE_METRIC`: exercise and make observable: Metric equals three times the sampled magnitude, clamped to the 0 V to 0.9 V range. Required traces: `time`, `clk`, `vin`, `metric`.
- `P_OUTPUT_BOUNDS`: exercise and make observable: Out remains within the public 0.08 V to 0.82 V clamp range with finite transition smoothing. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
