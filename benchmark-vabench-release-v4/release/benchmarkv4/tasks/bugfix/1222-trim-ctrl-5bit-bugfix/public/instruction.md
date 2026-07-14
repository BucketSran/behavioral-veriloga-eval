# Trim Ctrl 5bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `trim_ctrl_5bit.va`:
  - Module `trim_ctrl_5bit` (entry)
    - position 0: `ain` (input, electrical)
    - position 1: `dout0` (output, electrical)
    - position 2: `dout1` (output, electrical)
    - position 3: `dout2` (output, electrical)
    - position 4: `dout3` (output, electrical)
    - position 5: `dout4` (output, electrical)

## Public Parameter Contract

- `trim_ctrl_5bit.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `trim_ctrl_5bit.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONVERT_V_AIN_TO_THE_NEAREST`: restore: Convert `V(ain)` to the nearest integer code using half-up rounding. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`.
- `P_CLAMP_THE_CODE_TO_THE_VALID`: restore: Clamp the code to the valid 5-bit trim range `0..31`. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`.
- `P_DRIVE_DOUT0_DOUT4_FROM_THE_CLAMPED`: restore: Drive `dout0..dout4` from the clamped binary code, LSB first. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`.
- `P_DRIVE_HIGH_BITS_NEAR_VH_AND`: restore: Drive high bits near `vh` and low bits near 0 V. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`.
- `P_UPDATE_DETERMINISTICALLY_AS_THE_ANALOG_INPUT`: restore: Update deterministically as the analog input changes. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `trim_ctrl_5bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
