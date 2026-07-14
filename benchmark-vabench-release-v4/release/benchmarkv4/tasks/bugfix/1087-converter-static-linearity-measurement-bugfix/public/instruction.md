# Converter Static Linearity Measurement Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `converter_static_linearity_measurement_flow.va`:
  - Module `converter_static_linearity_measurement_flow` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `code` (output, electrical)
    - position 4: `recon` (output, electrical)
    - position 5: `dnl` (output, electrical)
    - position 6: `inl` (output, electrical)

## Public Parameter Contract

- `converter_static_linearity_measurement_flow.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.
- `converter_static_linearity_measurement_flow.vfs` defaults to `0.9` V; valid range: vfs > 0; sets the full-scale input and code-output range.
- `converter_static_linearity_measurement_flow.tr` defaults to `1.2e-10` s; valid range: tr > 0; sets metric-output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_STATE`: restore: Active-high reset clears the retained conversion and previous-step state to the public reset values. Required traces: `time`, `clk`, `rst`, `code`, `recon`, `dnl`, `inl`.
- `P_FOUR_BIT_QUANTIZATION`: restore: On each non-reset rising clk edge, vin clips to 0 through vfs and quantizes monotonically to one of 16 codes represented as code_index times vfs/15. Required traces: `time`, `clk`, `rst`, `vin`, `code`.
- `P_PUBLIC_RECONSTRUCTION_TABLE`: restore: For each code 0 through 15, recon equals the corresponding value in the public monotonic non-ideal reconstruction table, with default table voltages scaled by vfs/0.9 for legal vfs overrides. Required traces: `time`, `clk`, `code`, `recon`.
- `P_INL_METRIC`: restore: INL encodes reconstruction error from the vfs/15-per-code ideal ramp using the public gain and 0.05 V through 0.85 V clamp. Required traces: `time`, `code`, `recon`, `inl`.
- `P_DNL_INCREASING_STEP`: restore: For a valid increasing code step, dnl encodes actual reconstruction-step error relative to vfs/15 per code step with the public scaling and clamp. Required traces: `time`, `clk`, `code`, `recon`, `dnl`.
- `P_DNL_NO_STEP_BASELINE`: restore: Before a valid increasing step, or when code does not increase, dnl is held at the 0.45 V baseline. Required traces: `time`, `clk`, `code`, `recon`, `dnl`.

## Modeling Constraints

- Use deterministic rising-edge sampled quantization and retained previous-step state.
- Use only the public reconstruction table and smoothed voltage outputs.
- Do not hard-code validation sweeps or use current contributions, transistor-level devices, continuous-time operators, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `converter_static_linearity_measurement_flow.va`.
Every supplied `.va` file is editable; do not add or omit files.
