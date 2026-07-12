# Tool 4bit SAR Signed DAC Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `tool_4bit_sar_signed_dac.va`:
  - Module `tool_4bit_sar_signed_dac` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `sh` (input, electrical)
    - position 5: `aout` (output, electrical)

## Public Parameter Contract

- `tool_4bit_sar_signed_dac.vth` defaults to `0.9`; valid range: finite; overrides vth.
- `tool_4bit_sar_signed_dac.gain` defaults to `1.8 / 16.0`; valid range: finite; overrides gain.
- `tool_4bit_sar_signed_dac.tr` defaults to `1p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CROSSING_OF_SH`: restore: On each rising crossing of `sh` through `vth`, evaluate bits `d3..d0` with weights `8, 4, 2, 1`. A high bit contributes the positive weight and a low bit contributes the negative weight. Drive `aout` to the signed weighted sum multiplied by `gain` and hold it until the next sample trigger. Required traces: `time`, `aout`, `d0`, `d1`, `d2`, `d3`, `sh`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `tool_4bit_sar_signed_dac.va`.
Every supplied `.va` file is editable; do not add or omit files.
