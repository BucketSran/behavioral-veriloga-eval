# Digital Phase Accumulator With Modulo Wrap Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Digital Phase Accumulator With Modulo Wrap` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `phase_accumulator_timer_wrap_ref.va`:
  - Module `phase_accumulator_timer_wrap_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `clk_out` (output, electrical)
    - position 3: `phase_out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `phase_accumulator_timer_wrap_ref` as `XDUT` with ordered public binding: VDD=VDD, VSS=VSS, clk_out=clk_out, phase_out=phase_out.

## Public Parameter Contract

- `phase_accumulator_timer_wrap_ref.dt` defaults to `5e-09` s; valid range: dt > 0; sets phase-state timer update interval.
- `phase_accumulator_timer_wrap_ref.phase_step` defaults to `0.25` normalized cycle; valid range: 0 < phase_step < 1; sets normalized phase increment per timer event.
- `phase_accumulator_timer_wrap_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TIMER_INCREMENT`: exercise and make observable: On every dt timer event, normalized phase advances by phase_step. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_MODULO_WRAP`: exercise and make observable: The phase state wraps modulo one and never grows unbounded. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_PHASE_RAIL_SCALING`: exercise and make observable: Phase_out equals wrapped normalized phase scaled by the local VDD-minus-VSS rail span. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_PHASE_DERIVED_CLOCK`: exercise and make observable: Clk_out is rail-high while normalized phase is below 0.5 and low while phase is at or above 0.5. Required traces: `time`, `clk_out`, `phase_out`, `VDD`, `VSS`.
- `P_PARAMETERIZED_PERIOD`: exercise and make observable: Changing dt or phase_step changes the observable phase and clock cadence according to the same update and wrap rules. Required traces: `time`, `clk_out`, `phase_out`, `VDD`, `VSS`.

The required trace names are: `time`, `VDD`, `VSS`, `clk_out`, `phase_out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
