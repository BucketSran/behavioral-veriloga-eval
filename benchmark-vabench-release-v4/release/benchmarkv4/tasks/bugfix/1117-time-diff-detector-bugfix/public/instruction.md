# Time Diff Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `time_diff_detector.va`:
  - Module `time_diff_detector` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vinp` (input, electrical)
    - position 2: `vinn` (input, electrical)
    - position 3: `vout` (output, electrical)

## Public Parameter Contract

- `time_diff_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the symmetric positive and negative output clipping magnitude.
- `time_diff_detector.vth_clk` defaults to `0.45` V; valid range: finite real value; sets the rising clock threshold that reports and rearms each measurement window.
- `time_diff_detector.vth_in` defaults to `0.45` V; valid range: finite real value; sets the rising threshold independently used to timestamp vinp and vinn.
- `time_diff_detector.td` defaults to `0` s; valid range: td >= 0; sets output transition delay after a reported measurement.
- `time_diff_detector.tr` defaults to `1e-12` s; valid range: tr > 0; sets output transition smoothing.
- `time_diff_detector.scale` defaults to `1000000000.0` V/s; valid range: finite real value; multiplies the signed input edge-time difference before clipping.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FIRST_EDGE_CAPTURE`: restore: Within each clock window, only the first rising vinp crossing and first rising vinn crossing through vth_in define the stored timing measurement. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_PREVIOUS_WINDOW_REPORT`: restore: At each rising clk crossing through vth_clk, vout reports the edge-time difference captured in the preceding valid clock window; if either input edge was absent, vout holds its previous value. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_SIGNED_DIFFERENCE`: restore: The reported value preserves the sign of the vinp first-edge time minus the vinn first-edge time and applies the public scale factor. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_OUTPUT_CLIP`: restore: The scaled reported voltage is bounded to the closed interval from -vdd to +vdd. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_WINDOW_REARM`: restore: Each reporting clock edge rearms both input-edge detectors so the next window is measured independently. Required traces: `time`, `clk`, `vinp`, `vinn`, `vout`.
- `P_OUTPUT_TRANSITION`: restore: Reported output changes use the declared td delay and tr transition time. Required traces: `time`, `clk`, `vout`.

## Modeling Constraints

- Use deterministic threshold-crossing event detection and per-window state.
- Capture no more than one rising edge per input in each clock window.
- Do not use fixed stimulus timestamps, current contributions, or validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `time_diff_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
