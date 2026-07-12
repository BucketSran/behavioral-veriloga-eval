# Trim Ctrl 4bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `trim_ctrl_4bit.va`:
  - Module `trim_ctrl_4bit` (entry)
    - position 0: `ain` (input, electrical)
    - position 1: `dout0` (output, electrical)
    - position 2: `dout1` (output, electrical)
    - position 3: `dout2` (output, electrical)
    - position 4: `dout3` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ANALOG_INPUT_ROUNDING`: restore: Round `ain` to the nearest integer code level rather than truncating. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_LOW_FOUR_BIT_MAPPING`: restore: Emit the low four bits of the rounded code on `dout0..dout3` in the declared bit order. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_CONTINUOUS_CODE_UPDATE`: restore: Update deterministically as `ain` changes without requiring hidden state or clocks. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_TRIM_OUTPUT_LEVELS`: restore: All trim outputs are voltage-coded at valid low/high levels. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `trim_ctrl_4bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
