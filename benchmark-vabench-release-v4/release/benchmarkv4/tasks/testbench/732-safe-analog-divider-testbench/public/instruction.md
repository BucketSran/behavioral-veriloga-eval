# Safe Analog Divider Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Safe Analog Divider` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `safe_analog_divider.va`:
  - Module `safe_analog_divider` (entry)
    - position 0: `signumer` (input, electrical)
    - position 1: `sigdenom` (input, electrical)
    - position 2: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `safe_analog_divider` as `XDUT` with ordered public binding: signumer=signumer, sigdenom=sigdenom, sigout=sigout.

## Public Parameter Contract

- `safe_analog_divider.gain` defaults to `1.0`; valid range: finite; overrides gain.
- `safe_analog_divider.min_sigdenom` defaults to `0.2 from (0:inf)`; valid range: finite; overrides min_sigdenom.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_USE_V_SIGDENOM_DIRECTLY_WHEN_ITS`: exercise and make observable: For denominator magnitudes at least `min_sigdenom`, use `V(sigdenom)` directly in the divider transfer. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_POSITIVE_BUT`: exercise and make observable: For positive denominator magnitudes below `min_sigdenom`, use `+min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_EXACTLY_ZERO`: exercise and make observable: For exactly zero denominator, use `+min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_WHEN_V_SIGDENOM_IS_NEGATIVE_BUT`: exercise and make observable: For negative denominator magnitudes below `min_sigdenom`, use `-min_sigdenom` as the guarded denominator. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.
- `P_DRIVE_SIGOUT_TO_GAIN_V_SIGNUMER`: exercise and make observable: Drive `sigout` to the observable transfer `gain * V(signumer) / guarded_denominator`. Required traces: `time`, `sigdenom`, `signumer`, `sigout`.

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
