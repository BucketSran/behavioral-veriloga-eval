# Weighted Decoder 7b5 Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Weighted Decoder 7b5` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `weighted_decoder_7b5.va`:
  - Module `weighted_decoder_7b5` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `d4` (input, electrical)
    - position 5: `d5` (input, electrical)
    - position 6: `d6` (input, electrical)
    - position 7: `d7` (input, electrical)
    - position 8: `d8` (input, electrical)
    - position 9: `aout7b` (output, electrical)
    - position 10: `aout7b5` (output, electrical)
    - position 11: `aout8b` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `weighted_decoder_7b5` as `XDUT` with ordered public binding: d0=d0, d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, d6=d6, d7=d7, d8=d8, aout7b=aout7b, aout7b5=aout7b5, aout8b=aout8b.

## Public Parameter Contract

- `weighted_decoder_7b5.vth` defaults to `0.5`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SHARED_272_DENOMINATOR`: exercise and make observable: All decoded outputs use the shared normalization denominator of 272.0, including the fixed reference basis. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `aout7b`, `aout7b5`, `aout8b`.
- `P_SEVEN_BIT_OUTPUT`: exercise and make observable: `aout7b` reports the 7-bit decoded analog output with the specified redundant SAR weights. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `aout7b`.
- `P_SEVEN_HALF_BIT_OUTPUT`: exercise and make observable: `aout7b5` preserves the half-bit redundant contribution and correct polarity. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `aout7b5`.
- `P_EIGHT_BIT_OUTPUT`: exercise and make observable: `aout8b` reports the full 8-bit weighted output with the correct amplitude. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `aout8b`.

The required trace names are: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `aout7b`, `aout7b5`, `aout8b`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
