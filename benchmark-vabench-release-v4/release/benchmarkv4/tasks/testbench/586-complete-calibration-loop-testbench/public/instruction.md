# Complete Calibration Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Complete Calibration Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `complete_calibration_loop.va`:
  - Module `complete_calibration_loop` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `trim_mon` (output, electrical)
    - position 6: `residual_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `complete_calibration_loop` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric, trim_mon=trim_mon, residual_mon=residual_mon.

## Public Parameter Contract

- `complete_calibration_loop.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `complete_calibration_loop.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.
- `complete_calibration_loop.target` defaults to `0.45` V; valid range: vmin <= target <= vmax; sets the calibration common-mode target.
- `complete_calibration_loop.loop_gain` defaults to `0.4`; valid range: loop_gain >= 0; sets correction applied to residual error per update.
- `complete_calibration_loop.plant_alpha` defaults to `0.35`; valid range: 0 < plant_alpha <= 1; sets first-order corrected-plant update factor.
- `complete_calibration_loop.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets lower clamp for bounded analog states.
- `complete_calibration_loop.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets upper clamp for bounded analog states.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_TO_TARGET`: exercise and make observable: Active-high reset initializes out, trim_mon, residual_mon, and metric to their target-state values. Required traces: `time`, `rst`, `out`, `metric`, `trim_mon`, `residual_mon`.
- `P_CLOCKED_LOOP_UPDATE`: exercise and make observable: After reset releases, calibration state updates on rising clk crossings and holds between updates. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `trim_mon`, `residual_mon`.
- `P_RESIDUAL_OBSERVATION`: exercise and make observable: Residual_mon exposes clamp(target + raw_error + (trim_mon_next - target), vmin, vmax), where raw_error is V(vin)-target and trim_mon_next is the current edge's bounded negative-feedback trim update. Required traces: `time`, `clk`, `vin`, `trim_mon`, `residual_mon`.
- `P_NEGATIVE_FEEDBACK_DIRECTION`: exercise and make observable: The trim correction uses trim_mon_next = clamp(trim_mon - loop_gain * residual_before_update, vmin, vmax), so positive residual decreases trim and negative residual increases trim. Required traces: `time`, `clk`, `vin`, `out`, `trim_mon`, `residual_mon`.
- `P_PLANT_CONVERGENCE`: exercise and make observable: Out follows out_next = clamp(out + plant_alpha * (residual_mon_next - out), vmin, vmax) on each non-reset update. Required traces: `time`, `clk`, `vin`, `out`, `residual_mon`.
- `P_BOUNDS_AND_METRIC`: exercise and make observable: Bounded analog states remain within vmin through vmax, while metric equals clamp(0.9 - 1.5 * abs(out-target), 0.0, 0.9) after each update. Required traces: `time`, `out`, `metric`, `trim_mon`, `residual_mon`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`, `trim_mon`, `residual_mon`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
