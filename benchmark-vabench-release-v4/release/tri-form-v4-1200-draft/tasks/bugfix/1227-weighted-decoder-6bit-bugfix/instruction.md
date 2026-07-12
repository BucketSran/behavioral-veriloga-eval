# Weighted Decoder 6bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `weighted_decoder_6bit.va`:
  - Module `weighted_decoder_6bit` (entry)
    - position 0: `vd1` (input, electrical)
    - position 1: `vd2` (input, electrical)
    - position 2: `vd3` (input, electrical)
    - position 3: `vd4` (input, electrical)
    - position 4: `vd5` (input, electrical)
    - position 5: `vd6` (input, electrical)
    - position 6: `vout` (output, electrical)

## Public Parameter Contract

- `weighted_decoder_6bit.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `weighted_decoder_6bit.vref` defaults to `1.0`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TREAT_EACH_INPUT_AS_LOGIC_1`: restore: Treat each input as logic 1 when its voltage is greater than `vth`, otherwise logic 0. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_INTERPRET_VD1_VD6_AS_AN_UNSIGNED`: restore: Interpret `vd1..vd6` as an unsigned binary word with `vd1` as MSB and `vd6` as LSB. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_SCALE_THE_DECODED_CODE_BY_VREF`: restore: Scale the decoded code by `vref`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_MAP_ALL_ZERO_INPUT_TO_0`: restore: Map all-zero input to 0 V. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_MAP_ALL_ONES_INPUT_TO_VREF`: restore: Map all-ones input to `vref`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `weighted_decoder_6bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
