# Control Word Encoder 7b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `control_word_encoder_7b.va`:
  - Module `control_word_encoder_7b` (entry)
    - position 0: `d0` (output, electrical)
    - position 1: `d1` (output, electrical)
    - position 2: `d2` (output, electrical)
    - position 3: `d3` (output, electrical)
    - position 4: `d4` (output, electrical)
    - position 5: `d5` (output, electrical)
    - position 6: `d6` (output, electrical)

## Public Parameter Contract

- `control_word_encoder_7b.ctrl` defaults to `85`; valid range: finite; overrides ctrl.
- `control_word_encoder_7b.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `control_word_encoder_7b.vlo` defaults to `0.0`; valid range: finite; overrides vlo.
- `control_word_encoder_7b.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SEVEN_BIT_DECODE`: restore: `ctrl` is decoded LSB-first so `d0` carries bit 0 and `d6` carries bit 6. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.
- `P_BIT_POLARITY`: restore: A decoded one drives its output high and a decoded zero drives its output low. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.
- `P_OUTPUT_RAIL_LEVELS`: restore: Each output uses the declared `vhi` and `vlo` voltage levels for its decoded bit. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `control_word_encoder_7b.va`.
Every supplied `.va` file is editable; do not add or omit files.
