# Dual Track Sample Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dual_track_sample_hold.va`:
  - Module `dual_track_sample_hold` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `phase` (output, electrical)

## Public Parameter Contract

- `dual_track_sample_hold.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dual_track_sample_hold.tick` defaults to `0.5n from (0:inf)`; valid range: finite; overrides tick.
- `dual_track_sample_hold.alpha_in` defaults to `0.45 from (0:1]`; valid range: finite; overrides alpha_in.
- `dual_track_sample_hold.alpha_out` defaults to `0.55 from (0:1]`; valid range: finite; overrides alpha_out.
- `dual_track_sample_hold.tedge` defaults to `50p from (0:inf)`; valid range: finite; overrides tedge.
- `dual_track_sample_hold.vinit` defaults to `0.0`; valid range: finite; overrides vinit.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_COMPLEMENTARY_TRACK_HOLD_SEQUENCE`: restore: During low clock phase the input stage tracks `vin` while output holds; after the rising edge, the output stage tracks the retained input-stage value during high clock phase; after the falling edge, output holds until the next high phase. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.
- `P_FINITE_TRACKING_AND_HOLD`: restore: Use finite acquisition updates and preserve held values between tracking windows rather than making the output continuously transparent or a single ideal edge sample. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.
- `P_PHASE_MONITOR_POLARITY`: restore: Drive `phase` high only during output-stage tracking and low otherwise. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dual_track_sample_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
