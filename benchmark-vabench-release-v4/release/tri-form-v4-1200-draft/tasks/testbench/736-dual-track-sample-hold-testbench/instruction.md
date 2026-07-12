# Dual Track Sample Hold Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Dual Track Sample Hold` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dual_track_sample_hold.va`:
  - Module `dual_track_sample_hold` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `phase` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dual_track_sample_hold` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, clk=clk, vin=vin, vout=vout, phase=phase.

## Public Parameter Contract

- `dual_track_sample_hold.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `dual_track_sample_hold.tick` defaults to `0.5n from (0:inf)`; valid range: finite; overrides tick.
- `dual_track_sample_hold.alpha_in` defaults to `0.45 from (0:1]`; valid range: finite; overrides alpha_in.
- `dual_track_sample_hold.alpha_out` defaults to `0.55 from (0:1]`; valid range: finite; overrides alpha_out.
- `dual_track_sample_hold.tedge` defaults to `50p from (0:inf)`; valid range: finite; overrides tedge.
- `dual_track_sample_hold.vinit` defaults to `0.0`; valid range: finite; overrides vinit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_COMPLEMENTARY_TRACK_HOLD_SEQUENCE`: exercise and make observable: During low clock phase the input stage tracks `vin` while output holds; after the rising edge, the output stage tracks the retained input-stage value during high clock phase; after the falling edge, output holds until the next high phase. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.
- `P_FINITE_TRACKING_AND_HOLD`: exercise and make observable: Use finite acquisition updates and preserve held values between tracking windows rather than making the output continuously transparent or a single ideal edge sample. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.
- `P_PHASE_MONITOR_POLARITY`: exercise and make observable: Drive `phase` high only during output-stage tracking and low otherwise. Required traces: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.

The required trace names are: `time`, `clk`, `phase`, `vin`, `vout`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
