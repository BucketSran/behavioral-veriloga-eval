# Time Diff Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Time Diff Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `time_diff_detector.va`:
  - Module `time_diff_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vinp` (input, electrical)
    - position 2: `vinn` (input, electrical)
    - position 3: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `time_diff_detector` as `XDUT` with ordered public binding: clk=clk, vinp=vinp, vinn=vinn, vout=vout.

## Public Parameter Contract

- `time_diff_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the symmetric positive and negative output clipping magnitude.
- `time_diff_detector.vth_clk` defaults to `0.45` V; valid range: finite real value; sets the rising clock threshold that reports and rearms each measurement window.
- `time_diff_detector.vth_in` defaults to `0.45` V; valid range: finite real value; sets the rising threshold independently used to timestamp vinp and vinn.
- `time_diff_detector.td` defaults to `0` s; valid range: td >= 0; sets output transition delay after a reported measurement.
- `time_diff_detector.tr` defaults to `1e-12` s; valid range: tr > 0; sets output transition smoothing.
- `time_diff_detector.scale` defaults to `1000000000.0` V/s; valid range: finite real value; multiplies the signed input edge-time difference before clipping.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FIRST_EDGE_CAPTURE`: exercise and make observable: Within each clock window, only the first rising vinp crossing and first rising vinn crossing through vth_in define the stored timing measurement. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_PREVIOUS_WINDOW_REPORT`: exercise and make observable: At each rising clk crossing through vth_clk, vout reports the edge-time difference captured in the preceding valid clock window; if either input edge was absent, vout holds its previous value. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_SIGNED_DIFFERENCE`: exercise and make observable: The reported value preserves the sign of the vinp first-edge time minus the vinn first-edge time and applies the public scale factor. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_OUTPUT_CLIP`: exercise and make observable: The scaled reported voltage is bounded to the closed interval from -vdd to +vdd. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_WINDOW_REARM`: exercise and make observable: Each reporting clock edge rearms both input-edge detectors so the next window is measured independently. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_OUTPUT_TRANSITION`: exercise and make observable: Reported output changes use the declared td delay and tr transition time. Required traces: `time`, `clk`, `vout`.

The required trace names are: `time`, `clk`, `vinp`, `vinn`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
