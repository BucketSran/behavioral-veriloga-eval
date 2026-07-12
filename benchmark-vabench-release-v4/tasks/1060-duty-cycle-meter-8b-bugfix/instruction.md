# Duty Cycle Meter 8b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `duty_cycle_meter_8b.va`:
  - Module `duty_cycle_meter_8b` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `valid` (output, electrical)
    - position 2: `duty0` (output, electrical)
    - position 3: `duty1` (output, electrical)
    - position 4: `duty2` (output, electrical)
    - position 5: `duty3` (output, electrical)
    - position 6: `duty4` (output, electrical)
    - position 7: `duty5` (output, electrical)
    - position 8: `duty6` (output, electrical)
    - position 9: `duty7` (output, electrical)

## Public Parameter Contract

- `duty_cycle_meter_8b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded duty-code and valid high level.
- `duty_cycle_meter_8b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock rising and falling threshold.
- `duty_cycle_meter_8b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_COMPLETE_CYCLE_MEASUREMENT`: restore: A new duty result is produced only after observing a rising edge, one intervening falling edge, and the next rising edge. Required traces: `time`, `clk_in`, `valid`, `duty0`, `duty1`, `duty2`, `duty3`, `duty4`, `duty5`, `duty6`, `duty7`.
- `P_HIGH_FRACTION_CODE`: restore: For each complete cycle, the unsigned code is the rounded value of 255 times high time divided by period. Required traces: `time`, `clk_in`, `duty0`, `duty1`, `duty2`, `duty3`, `duty4`, `duty5`, `duty6`, `duty7`.
- `P_CODE_SATURATION`: restore: The reported duty code is saturated to the inclusive range 0 through 255. Required traces: `time`, `clk_in`, `duty0`, `duty1`, `duty2`, `duty3`, `duty4`, `duty5`, `duty6`, `duty7`.
- `P_VALID_HOLD`: restore: valid remains low before the first complete measurement and asserts and holds high after a duty result is available. Required traces: `time`, `clk_in`, `valid`.
- `P_BIT_ORDER_AND_LEVELS`: restore: duty0 is the least significant bit and duty7 is the most significant bit; asserted outputs use vdd and inactive outputs use 0 V. Required traces: `time`, `valid`, `duty0`, `duty1`, `duty2`, `duty3`, `duty4`, `duty5`, `duty6`, `duty7`.

## Modeling Constraints

- Use deterministic edge-time state for cycle and high-time measurement.
- Measure complete cycles only; do not infer duty from a partial waveform.
- Use smooth voltage contributions for all outputs.
- Do not hard-code waveform periods, sample windows, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `duty_cycle_meter_8b.va`.
Every supplied `.va` file is editable; do not add or omit files.
