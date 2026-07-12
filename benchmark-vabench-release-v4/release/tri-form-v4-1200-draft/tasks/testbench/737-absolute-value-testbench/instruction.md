# Smooth Absolute Value Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Smooth Absolute Value` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `absolute_value.va`:
  - Module `absolute_value` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `absolute_value` as `XDUT` with ordered public binding: sigin=sigin, sigout=sigout.

## Public Parameter Contract

- `absolute_value.smooth` defaults to `0.05 from (0:inf)`; valid range: finite; overrides smooth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SMOOTH_ABSOLUTE_TRANSFER`: exercise and make observable: Drive `sigout` as the smooth absolute-value transfer `V(sigin) * tanh(V(sigin) / smooth)`: even in input, nonnegative, deterministic, memoryless, rounded near zero, and asymptotically equal to input magnitude for large positive and negative inputs. Required traces: `time`, `sigin`, `sigout`.

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
