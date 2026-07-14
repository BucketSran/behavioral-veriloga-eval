# Offset Gain Amplifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Offset Gain Amplifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `offset_gain_amplifier.va`:
  - Module `offset_gain_amplifier` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `offset_gain_amplifier` as `XDUT` with ordered public binding: sigin=sigin, sigout=sigout.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INPUT_OFFSET_SUBTRACTION`: exercise and make observable: Subtract 0.2 V from `V(sigin)` before applying gain. Required traces: `time`, `sigin`, `sigout`.
- `P_FIXED_GAIN_THREE`: exercise and make observable: Drive `sigout` to `3.0 * (V(sigin) - 0.2)`. Required traces: `time`, `sigin`, `sigout`.
- `P_DIRECT_MEMORYLESS_OUTPUT`: exercise and make observable: Use a direct memoryless voltage output without clipping, filtering, current output, or stimulus-specific behavior. Required traces: `time`, `sigin`, `sigout`.

The required trace names are: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
