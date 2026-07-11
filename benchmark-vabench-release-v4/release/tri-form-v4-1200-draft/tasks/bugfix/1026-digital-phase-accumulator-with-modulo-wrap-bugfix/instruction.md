# Digital Phase Accumulator With Modulo Wrap Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `phase_accumulator_timer_wrap_ref.va`:
  - Module `phase_accumulator_timer_wrap_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `clk_out` (output, electrical)
    - position 3: `phase_out` (output, electrical)

## Public Parameter Contract

- `phase_accumulator_timer_wrap_ref.dt` defaults to `5e-09` s; valid range: dt > 0; sets phase-state timer update interval.
- `phase_accumulator_timer_wrap_ref.phase_step` defaults to `0.25` normalized cycle; valid range: 0 < phase_step < 1; sets normalized phase increment per timer event.
- `phase_accumulator_timer_wrap_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TIMER_INCREMENT`: restore: On every dt timer event, normalized phase advances by phase_step. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_MODULO_WRAP`: restore: The phase state wraps modulo one and never grows unbounded. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_PHASE_RAIL_SCALING`: restore: Phase_out equals wrapped normalized phase scaled by the local VDD-minus-VSS rail span. Required traces: `time`, `phase_out`, `VDD`, `VSS`.
- `P_PHASE_DERIVED_CLOCK`: restore: Clk_out is rail-high while normalized phase is below 0.5 and low while phase is at or above 0.5. Required traces: `time`, `clk_out`, `phase_out`, `VDD`, `VSS`.
- `P_PARAMETERIZED_PERIOD`: restore: Changing dt or phase_step changes the observable phase and clock cadence according to the same update and wrap rules. Required traces: `time`, `clk_out`, `phase_out`, `VDD`, `VSS`.

## Modeling Constraints

- Use deterministic timer-updated normalized phase with manual modulo wrap.
- Use rail-referenced smoothed voltage contributions only.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `phase_accumulator_timer_wrap_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
