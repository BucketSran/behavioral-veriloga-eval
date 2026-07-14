# Coarse QTZ 3bit Residue Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `coarse_qtz_3bit_residue.va`:
  - Module `coarse_qtz_3bit_residue` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `d0` (output, electrical)
    - position 2: `d1` (output, electrical)
    - position 3: `d2` (output, electrical)
    - position 4: `vres` (output, electrical)

## Public Parameter Contract

- `coarse_qtz_3bit_residue.vref` defaults to `1.0`; valid range: finite; overrides vref.
- `coarse_qtz_3bit_residue.vdd` defaults to `1.0`; valid range: finite; overrides vdd.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLIP_VIN_TO_THE_RANGE_FROM`: restore: Clip `vin` to the range from `-vref` to `+vref`. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.
- `P_QUANTIZE_THE_CLIPPED_VALUE_INTO_EIGHT`: restore: Quantize the clipped value into eight 3-bit codes using round-to-nearest behavior. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.
- `P_SATURATE_THE_CODE_AT_THE_ENDPOINTS`: restore: Saturate the code at the endpoints. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.
- `P_USE_UNIFORMLY_SPACED_QUANTIZATION_LEVELS_START`: restore: Use uniformly spaced quantization levels starting at `-vref`, with one LSB equal to one eighth of the full input span. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.
- `P_DRIVE_D0_D1_AND_D2_AS`: restore: Drive `d0`, `d1`, and `d2` as LSB-to-MSB voltage-coded bits. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.
- `P_DRIVE_VRES_AS_THE_CLIPPED_INPUT`: restore: Drive `vres` as the clipped input minus the selected quantized analog level. Required traces: `time`, `d0`, `d1`, `d2`, `vin`, `vres`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `coarse_qtz_3bit_residue.va`.
Every supplied `.va` file is editable; do not add or omit files.
