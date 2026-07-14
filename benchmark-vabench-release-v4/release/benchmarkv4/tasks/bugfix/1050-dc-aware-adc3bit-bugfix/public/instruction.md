# DC Aware ADC3bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dc_aware_adc3bit.va`:
  - Module `dc_aware_adc3bit` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `d2` (output, electrical)
    - position 2: `d1` (output, electrical)
    - position 3: `d0` (output, electrical)

## Public Parameter Contract

- `dc_aware_adc3bit.vref` defaults to `1` V; valid range: vref > 0; sets the analog full-scale reference and uniform quantization span.
- `dc_aware_adc3bit.vh` defaults to `0.9` V; valid range: vh > 0; sets the voltage-coded output high level.
- `dc_aware_adc3bit.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_STATIC_CONVERSION`: restore: The output code represents the current vin level without requiring a clock or prior transient event. Required traces: `time`, `vin`, `d2`, `d1`, `d0`.
- `P_UNIFORM_QUANTIZATION`: restore: The 0-to-vref input span is divided into eight ordered uniform code regions producing unsigned codes 0 through 7. Required traces: `time`, `vin`, `d2`, `d1`, `d0`.
- `P_INPUT_CLIPPING`: restore: Inputs at or below 0 V produce code 0, and inputs at or above vref produce code 7. Required traces: `time`, `vin`, `d2`, `d1`, `d0`.
- `P_BINARY_BIT_ORDER`: restore: d2 is the most significant output bit and d0 is the least significant output bit. Required traces: `time`, `d2`, `d1`, `d0`.
- `P_OUTPUT_LEVELS`: restore: Each output bit approaches 0 V for logic low and vh for logic high with finite transition smoothing. Required traces: `time`, `d2`, `d1`, `d0`.

## Modeling Constraints

- Use deterministic static voltage-domain quantization.
- Use smooth voltage contributions for all output bits.
- Do not introduce a clock, hidden state, current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dc_aware_adc3bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
