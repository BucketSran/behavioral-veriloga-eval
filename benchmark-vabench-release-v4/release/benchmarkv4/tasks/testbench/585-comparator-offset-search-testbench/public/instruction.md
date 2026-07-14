# Comparator Offset Search Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Comparator Offset Search` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `comparator_offset_search_ref.va`:
  - Module `comparator_offset_search_ref` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `inp` (input, electrical)
    - position 3: `inn` (input, electrical)
    - position 4: `outp` (output, electrical)
    - position 5: `trip_v` (output, electrical)
    - position 6: `offset_est` (output, electrical)
    - position 7: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `comparator_offset_search_ref` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, inp=inp, inn=inn, outp=outp, trip_v=trip_v, offset_est=offset_est, valid=valid.

## Public Parameter Contract

- `comparator_offset_search_ref.vos` defaults to `0.005` V; valid range: finite real; sets the input-referred differential decision threshold.
- `comparator_offset_search_ref.trf` defaults to `2e-11` s; valid range: trf > 0; sets decision and measurement-output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_MEASUREMENT_STATE`: exercise and make observable: Before the first positive threshold crossing, valid, trip_v, and offset_est remain in the zero-measurement state. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_DECISION_THRESHOLD`: exercise and make observable: Outp is high when V(inp,vss)-V(inn,vss) is above vos and low after that differential falls below vos. Required traces: `time`, `vdd`, `vss`, `inp`, `inn`, `outp`.
- `P_FIRST_POSITIVE_CAPTURE`: exercise and make observable: The first positive crossing of the vos threshold captures the input trip voltage and measured differential offset and asserts valid. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_CAPTURE_HOLD`: exercise and make observable: After valid asserts, trip_v, offset_est, and valid retain their first-measurement values despite later differential-input changes. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_RAIL_REFERENCED_LOGIC`: exercise and make observable: Outp and valid use the vdd-to-vss logic range with finite transition smoothing. Required traces: `time`, `vdd`, `vss`, `outp`, `valid`.

The required trace names are: `time`, `vdd`, `vss`, `inp`, `inn`, `outp`, `trip_v`, `offset_est`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
