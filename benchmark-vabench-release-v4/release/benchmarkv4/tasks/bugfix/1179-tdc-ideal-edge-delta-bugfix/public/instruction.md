# TDC Ideal Edge Delta Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `tdc_ideal_edge_delta.va`:
  - Module `tdc_ideal_edge_delta` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inn` (input, electrical)
    - position 2: `samp` (input, electrical)
    - position 3: `vout` (output, electrical)

## Public Parameter Contract

- `tdc_ideal_edge_delta.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `tdc_ideal_edge_delta.fullrange` defaults to `100p`; valid range: finite; overrides fullrange.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLE_REARMS_MEASUREMENT`: restore: At initialization and each rising `samp` crossing, input trigger flags clear while the previous output is retained until a new edge pair is measured. Required traces: `time`, `samp`, `inp`, `inn`, `vout`.
- `P_INPUT_EDGE_PAIR_CAPTURE`: restore: A measurement completes only after the required `inp` and `inn` rising-edge pair has been observed. Required traces: `time`, `inp`, `inn`, `samp`, `vout`.
- `P_SIGNED_DELTA_POLARITY`: restore: `vout` represents the `inp` minus `inn` edge-time delta with the specified polarity. Required traces: `time`, `inp`, `inn`, `vout`.
- `P_FULL_RANGE_SCALE`: restore: The reported timing delta uses the specified full-range scale rather than a half-range or alternate denominator. Required traces: `time`, `inp`, `inn`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `tdc_ideal_edge_delta.va`.
Every supplied `.va` file is editable; do not add or omit files.
