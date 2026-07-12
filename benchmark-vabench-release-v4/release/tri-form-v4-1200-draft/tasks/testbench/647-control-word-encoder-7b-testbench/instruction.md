# Control Word Encoder 7b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Control Word Encoder 7b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `control_word_encoder_7b.va`:
  - Module `control_word_encoder_7b` (entry)
    - position 0: `d0` (output, electrical)
    - position 1: `d1` (output, electrical)
    - position 2: `d2` (output, electrical)
    - position 3: `d3` (output, electrical)
    - position 4: `d4` (output, electrical)
    - position 5: `d5` (output, electrical)
    - position 6: `d6` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `control_word_encoder_7b` as `XDUT` with ordered public binding: d0=d0, d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6.

## Public Parameter Contract

- `control_word_encoder_7b.ctrl` defaults to `85`; valid range: finite; overrides ctrl.
- `control_word_encoder_7b.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `control_word_encoder_7b.vlo` defaults to `0.0`; valid range: finite; overrides vlo.
- `control_word_encoder_7b.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SEVEN_BIT_DECODE`: exercise and make observable: `ctrl` is decoded LSB-first so `d0` carries bit 0 and `d6` carries bit 6. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.
- `P_BIT_POLARITY`: exercise and make observable: A decoded one drives its output high and a decoded zero drives its output low. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.
- `P_OUTPUT_RAIL_LEVELS`: exercise and make observable: Each output uses the declared `vhi` and `vlo` voltage levels for its decoded bit. Required traces: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.

The required trace names are: `time`, `d0_42`, `d0_85`, `d1_42`, `d1_85`, `d2_42`, `d2_85`, `d3_42`, `d3_85`, `d4_42`, `d4_85`, `d5_42`, `d5_85`, `d6_42`, `d6_85`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
