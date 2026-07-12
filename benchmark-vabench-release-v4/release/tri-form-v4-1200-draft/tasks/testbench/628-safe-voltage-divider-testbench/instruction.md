# Safe Voltage Divider Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Safe Voltage Divider` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `safe_voltage_divider.va`:
  - Module `safe_voltage_divider` (entry)
    - position 0: `signumer` (input, electrical)
    - position 1: `sigdenom` (input, electrical)
    - position 2: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `safe_voltage_divider` as `XDUT` with ordered public binding: signumer=signumer, sigdenom=sigdenom, sigout=sigout.

## Public Parameter Contract

- `safe_voltage_divider.gain` defaults to `1`; valid range: finite; overrides gain.
- `safe_voltage_divider.min_sigdenom` defaults to `1.0e-9 from (0:inf)`; valid range: finite; overrides min_sigdenom.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_GAINED_DIVISION`: exercise and make observable: Drive `sigout` to `gain * V(signumer) / guarded_denominator`. Required traces: `time`, `signumer`, `sigdenom`, `sigout`.
- `P_DENOMINATOR_MAGNITUDE_FLOOR`: exercise and make observable: When `abs(V(sigdenom)) < min_sigdenom`, use a denominator magnitude of `min_sigdenom`. Required traces: `time`, `sigdenom`, `sigout`.
- `P_DENOMINATOR_SIGN_PRESERVED`: exercise and make observable: Preserve the original denominator sign when applying the minimum denominator guard. Required traces: `time`, `signumer`, `sigdenom`, `sigout`.

The required trace names are: `time`, `sigdenom`, `signumer`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
