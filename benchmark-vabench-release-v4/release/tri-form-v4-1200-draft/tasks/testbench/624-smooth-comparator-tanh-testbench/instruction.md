# Smooth Comparator Tanh Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Smooth Comparator Tanh` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `smooth_comparator_tanh.va`:
  - Module `smooth_comparator_tanh` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigref` (input, electrical)
    - position 2: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `smooth_comparator_tanh` as `XDUT` with ordered public binding: sigin=sigin, sigref=sigref, sigout=sigout.

## Public Parameter Contract

- `smooth_comparator_tanh.high` defaults to `1`; valid range: finite; overrides high.
- `smooth_comparator_tanh.low` defaults to `-1`; valid range: finite; overrides low.
- `smooth_comparator_tanh.offset` defaults to `0`; valid range: finite; overrides offset.
- `smooth_comparator_tanh.comp_slope` defaults to `1000`; valid range: finite; overrides comp_slope.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TANH_TRANSFER`: exercise and make observable: Drive `sigout` as `0.5 * (high - low) * tanh(comp_slope * (V(sigin, sigref) - offset)) + 0.5 * (high + low)`. Required traces: `time`, `sigin`, `sigref`, `sigout`.
- `P_INPUT_POLARITY`: exercise and make observable: A larger `V(sigin, sigref)` must move the output toward `high`, not toward `low`. Required traces: `time`, `sigin`, `sigref`, `sigout`.
- `P_SMOOTH_TRANSITION`: exercise and make observable: The output must transition smoothly between `low` and `high` according to the tanh slope, not as a hard switch. Required traces: `time`, `sigin`, `sigref`, `sigout`.

The required trace names are: `time`, `sigin`, `sigout`, `sigref`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
