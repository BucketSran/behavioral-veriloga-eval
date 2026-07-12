# Event Counter Windowed 16b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `event_counter_windowed_16b.va`:
  - Module `event_counter_windowed_16b` (entry)
    - position 0: `gate` (input, electrical)
    - position 1: `event_in` (input, electrical)
    - position 2: `done` (output, electrical)
    - position 3: `count0` (output, electrical)
    - position 4: `count1` (output, electrical)
    - position 5: `count2` (output, electrical)
    - position 6: `count3` (output, electrical)
    - position 7: `count4` (output, electrical)
    - position 8: `count5` (output, electrical)
    - position 9: `count6` (output, electrical)
    - position 10: `count7` (output, electrical)
    - position 11: `count8` (output, electrical)
    - position 12: `count9` (output, electrical)
    - position 13: `count10` (output, electrical)
    - position 14: `count11` (output, electrical)
    - position 15: `count12` (output, electrical)
    - position 16: `count13` (output, electrical)
    - position 17: `count14` (output, electrical)
    - position 18: `count15` (output, electrical)

## Public Parameter Contract

- `event_counter_windowed_16b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded count and done high level.
- `event_counter_windowed_16b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the gate and event edge threshold.
- `event_counter_windowed_16b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_WINDOW_OPEN`: restore: A rising gate crossing clears the count, opens a new measurement window, and drives done low. Required traces: `time`, `gate`, `event`, `done`, `count0`, `count1`, `count2`, `count3`, `count4`, `count5`, `count6`, `count7`, `count8`, `count9`, `count10`, `count11`, `count12`, `count13`, `count14`, `count15`.
- `P_IN_WINDOW_COUNT`: restore: Each rising event crossing increments the count exactly once only while the window is active and gate is high. Required traces: `time`, `gate`, `event`, `count0`, `count1`, `count2`, `count3`, `count4`, `count5`, `count6`, `count7`, `count8`, `count9`, `count10`, `count11`, `count12`, `count13`, `count14`, `count15`.
- `P_OUT_OF_WINDOW_IGNORE`: restore: Event crossings before a window opens or after it closes do not change the held result. Required traces: `time`, `gate`, `event`, `count0`, `count1`, `count2`, `count3`, `count4`, `count5`, `count6`, `count7`, `count8`, `count9`, `count10`, `count11`, `count12`, `count13`, `count14`, `count15`.
- `P_WINDOW_CLOSE_HOLD`: restore: A falling gate crossing closes the window, preserves the final count, and asserts done. Required traces: `time`, `gate`, `event`, `done`, `count0`, `count1`, `count2`, `count3`, `count4`, `count5`, `count6`, `count7`, `count8`, `count9`, `count10`, `count11`, `count12`, `count13`, `count14`, `count15`.
- `P_BIT_ORDER_AND_LEVELS`: restore: count0 is the least significant bit and count15 is the most significant bit; asserted outputs use vdd and inactive outputs use 0 V. Required traces: `time`, `done`, `count0`, `count1`, `count2`, `count3`, `count4`, `count5`, `count6`, `count7`, `count8`, `count9`, `count10`, `count11`, `count12`, `count13`, `count14`, `count15`.

## Modeling Constraints

- AMS role: windowed event-rate/count measurement block for timing, readout, and calibration instrumentation.
- Use deterministic event state for window activity, count, and done.
- Count rising event crossings only within an explicitly opened gate window.
- Use smooth voltage contributions for all outputs.
- Do not embed stimulus timing, validation hooks, debug outputs, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `event_counter_windowed_16b.va`.
Every supplied `.va` file is editable; do not add or omit files.
