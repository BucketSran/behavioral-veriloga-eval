# Analog Multiplier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Analog Multiplier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `analog_multiplier_gain.va`:
  - Module `analog_multiplier_gain` (entry)
    - position 0: `sigin1` (input, electrical)
    - position 1: `sigin2` (input, electrical)
    - position 2: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `analog_multiplier_gain` as `XDUT` with ordered public binding: sigin1=sigin1, sigin2=sigin2, sigout=sigout.

## Public Parameter Contract

- `analog_multiplier_gain.gain` defaults to `1`; valid range: finite; overrides gain.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ANALOG_PRODUCT`: exercise and make observable: Drive `sigout` to `V(sigin1) * V(sigin2)` scaled by `gain`, preserving product sign. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.
- `P_GAIN_PARAMETER_APPLIED`: exercise and make observable: Apply the overridable `gain` parameter multiplicatively to the input product. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.
- `P_MULTIPLICATIVE_NOT_ADDITIVE`: exercise and make observable: The transfer must be multiplicative and must not replace the product with addition or a square of one input. Required traces: `time`, `sigin1`, `sigin2`, `sigout`.

The required trace names are: `time`, `sigin1`, `sigin2`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
