# TDC Ideal Edge Delta Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `TDC Ideal Edge Delta` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `tdc_ideal_edge_delta.va`:
  - Module `tdc_ideal_edge_delta` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inn` (input, electrical)
    - position 2: `samp` (input, electrical)
    - position 3: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `tdc_ideal_edge_delta` as `XDUT` with ordered public binding: inp=inp, inn=inn, samp=samp, vout=vout.

## Public Parameter Contract

- `tdc_ideal_edge_delta.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `tdc_ideal_edge_delta.fullrange` defaults to `100p`; valid range: finite; overrides fullrange.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLE_REARMS_MEASUREMENT`: exercise and make observable: At initialization and each rising `samp` crossing, input trigger flags clear while the previous output is retained until a new edge pair is measured. Required traces: `time`, `samp`, `inp`, `inn`, `vout`.
- `P_INPUT_EDGE_PAIR_CAPTURE`: exercise and make observable: A measurement completes only after the required `inp` and `inn` rising-edge pair has been observed. Required traces: `time`, `inp`, `inn`, `samp`, `vout`.
- `P_SIGNED_DELTA_POLARITY`: exercise and make observable: `vout` represents the `inp` minus `inn` edge-time delta with the specified polarity. Required traces: `time`, `inp`, `inn`, `vout`.
- `P_FULL_RANGE_SCALE`: exercise and make observable: The reported timing delta uses the specified full-range scale rather than a half-range or alternate denominator. Required traces: `time`, `inp`, `inn`, `vout`.

The required trace names are: `time`, `inp`, `inn`, `samp`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
