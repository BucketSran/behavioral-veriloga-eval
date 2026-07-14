# Linear PFD Gain Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Linear PFD Gain` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `linear_pfd_gain.va`:
  - Module `linear_pfd_gain` (entry)
    - position 0: `in1` (input, electrical)
    - position 1: `in2` (input, electrical)
    - position 2: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `linear_pfd_gain` as `XDUT` with ordered public binding: in1=in1, in2=in2, out=out.

## Public Parameter Contract

- `linear_pfd_gain.kphi` defaults to `2.03`; valid range: finite; overrides kphi.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DIFFERENTIAL_INPUT_POLARITY`: exercise and make observable: `out` uses the input difference `in1 - in2`, preserving the specified differential polarity. Required traces: `time`, `in1`, `in2`, `out`.
- `P_KPHI_GAIN_SCALE`: exercise and make observable: `out` is scaled by the public gain coefficient `kphi` rather than unit gain or an alternate scale. Required traces: `time`, `in1`, `in2`, `out`.
- `P_CONTINUOUS_ANALOG_TRACKING`: exercise and make observable: `out` continuously tracks analog input changes without clocked state, clipping, or single-ended substitution. Required traces: `time`, `in1`, `in2`, `out`.

The required trace names are: `time`, `in1`, `in2`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
