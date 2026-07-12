# Weighted Decoder 6bit Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Weighted Decoder 6bit` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `weighted_decoder_6bit.va`:
  - Module `weighted_decoder_6bit` (entry)
    - position 0: `vd1` (input, electrical)
    - position 1: `vd2` (input, electrical)
    - position 2: `vd3` (input, electrical)
    - position 3: `vd4` (input, electrical)
    - position 4: `vd5` (input, electrical)
    - position 5: `vd6` (input, electrical)
    - position 6: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `weighted_decoder_6bit` as `XDUT` with ordered public binding: vd1=vd1, vd2=vd2, vd3=vd3, vd4=vd4, vd5=vd5, vd6=vd6, vout=vout.

## Public Parameter Contract

- `weighted_decoder_6bit.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `weighted_decoder_6bit.vref` defaults to `1.0`; valid range: finite; overrides vref.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TREAT_EACH_INPUT_AS_LOGIC_1`: exercise and make observable: Treat each input as logic 1 when its voltage is greater than `vth`, otherwise logic 0. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_INTERPRET_VD1_VD6_AS_AN_UNSIGNED`: exercise and make observable: Interpret `vd1..vd6` as an unsigned binary word with `vd1` as MSB and `vd6` as LSB. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_SCALE_THE_DECODED_CODE_BY_VREF`: exercise and make observable: Scale the decoded code by `vref`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_MAP_ALL_ZERO_INPUT_TO_0`: exercise and make observable: Map all-zero input to 0 V. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.
- `P_MAP_ALL_ONES_INPUT_TO_VREF`: exercise and make observable: Map all-ones input to `vref`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.

The required trace names are: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
