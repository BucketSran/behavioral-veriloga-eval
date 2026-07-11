# RF Mixer Downconverter Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `rf_mixer_downconverter_macro.va`:
  - Module `rf_mixer_downconverter_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `rf_mixer_downconverter_macro.tr` defaults to `8e-11` s; valid range: tr > 0; sets smoothing for discontinuous output and metric target changes.
- `rf_mixer_downconverter_macro.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets rst logic threshold and LO polarity decision threshold.
- `rf_mixer_downconverter_macro.conv_gain` defaults to `1.25`; valid range: conv_gain > 0; sets conversion gain applied to the input deviation about 0.45 V.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_COMMON_MODE`: restore: Active reset drives out to 0.45 V common mode and metric low. Required traces: `time`, `rst`, `out`, `metric`.
- `P_LO_POLARITY`: restore: With reset inactive, clk above vth selects LO coefficient +1 and clk at or below vth selects coefficient -1. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_DOWNCONVERSION_TRANSFER`: restore: The baseband target is 0.45 V plus conv_gain times vin minus 0.45 V times the selected LO coefficient. Required traces: `time`, `clk`, `vin`, `out`.
- `P_ACTIVE_METRIC`: restore: Metric is 0.9 V while reset is inactive and conversion is active, and low during reset. Required traces: `time`, `rst`, `metric`.
- `P_OUTPUT_CLAMP`: restore: Out is clamped to 0.02 V through 0.88 V and changes with finite smoothing. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain behavior and smooth discontinuous target changes.
- Do not use current contributions, transistor-level devices, S-parameters, AC/noise behavior, or link-level decoding.
- Do not add validation logic, hard-coded sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `rf_mixer_downconverter_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
