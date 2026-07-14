# Smooth Limiting Diffamp Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Smooth Limiting Diffamp` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `limiting_diffamp.va`:
  - Module `limiting_diffamp` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `limiting_diffamp` as `XDUT` with ordered public binding: sigin_p=sigin_p, sigin_n=sigin_n, sigout=sigout.

## Public Parameter Contract

- `limiting_diffamp.gain` defaults to `4.0`; valid range: finite; overrides gain.
- `limiting_diffamp.limit` defaults to `0.75 from (0:inf)`; valid range: finite; overrides limit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ODD_DIFFERENTIAL_POLARITY`: exercise and make observable: Compute `V(sigin_p, sigin_n)`, preserve polarity, and drive an odd differential transfer. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_SMALL_SIGNAL_GAIN`: exercise and make observable: Near zero differential input, drive approximately `gain * V(sigin_p, sigin_n)`. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.
- `P_SMOOTH_SYMMETRIC_LIMITING`: exercise and make observable: For large positive and negative differential inputs, smoothly approach `+limit` and `-limit` without a hard clamp. Required traces: `time`, `sigin_n`, `sigin_p`, `sigout`.

The required trace names are: `time`, `sigin_n`, `sigin_p`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
