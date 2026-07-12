# Comparator Offset Search Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `comparator_offset_search_ref.vos` defaults to `0.005` V; valid range: finite real; sets the input-referred differential decision threshold.
- `comparator_offset_search_ref.trf` defaults to `2e-11` s; valid range: trf > 0; sets decision and measurement-output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_MEASUREMENT_STATE`: restore: Before the first positive threshold crossing, valid, trip_v, and offset_est remain in the zero-measurement state. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_DECISION_THRESHOLD`: restore: Outp is high when V(inp,vss)-V(inn,vss) is above vos and low after that differential falls below vos. Required traces: `time`, `vdd`, `vss`, `inp`, `inn`, `outp`.
- `P_FIRST_POSITIVE_CAPTURE`: restore: The first positive crossing of the vos threshold captures the input trip voltage and measured differential offset and asserts valid. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_CAPTURE_HOLD`: restore: After valid asserts, trip_v, offset_est, and valid retain their first-measurement values despite later differential-input changes. Required traces: `time`, `inp`, `inn`, `trip_v`, `offset_est`, `valid`.
- `P_RAIL_REFERENCED_LOGIC`: restore: Outp and valid use the vdd-to-vss logic range with finite transition smoothing. Required traces: `time`, `vdd`, `vss`, `outp`, `valid`.

## Modeling Constraints

- Use deterministic crossing-event state for comparator decision and one-shot measurement capture.
- Drive voltage contributions outside event blocks with finite transition smoothing.
- Do not use current contributions, transistor-level devices, continuous-time operators, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `comparator_offset_search_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
