# Trim Ctrl 4bit Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Trim Ctrl 4bit` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `trim_ctrl_4bit.va`:
  - Module `trim_ctrl_4bit` (entry)
    - position 0: `ain` (input, electrical)
    - position 1: `dout0` (output, electrical)
    - position 2: `dout1` (output, electrical)
    - position 3: `dout2` (output, electrical)
    - position 4: `dout3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `trim_ctrl_4bit` as `XDUT` with ordered public binding: ain=ain, dout0=dout0, dout1=dout1, dout2=dout2, dout3=dout3.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ANALOG_INPUT_ROUNDING`: exercise and make observable: Round `ain` to the nearest integer code level rather than truncating. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_LOW_FOUR_BIT_MAPPING`: exercise and make observable: Emit the low four bits of the rounded code on `dout0..dout3` in the declared bit order. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_CONTINUOUS_CODE_UPDATE`: exercise and make observable: Update deterministically as `ain` changes without requiring hidden state or clocks. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.
- `P_TRIM_OUTPUT_LEVELS`: exercise and make observable: All trim outputs are voltage-coded at valid low/high levels. Required traces: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.

The required trace names are: `time`, `ain`, `dout0`, `dout1`, `dout2`, `dout3`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
