# Crossing Pulse Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `source_crossing_pulse_detector.va`:
  - Module `source_crossing_pulse_detector` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

## Public Parameter Contract

- `source_crossing_pulse_detector.pulse_width` defaults to `4e-09` s; valid range: pulse_width > 0; sets output high duration after each qualifying crossing.
- `source_crossing_pulse_detector.sigcrossing` defaults to `0.45` V; valid range: finite real; sets the bidirectional sigin detection threshold.
- `source_crossing_pulse_detector.vlogic_high` defaults to `0.9` V; valid range: finite real; sets the asserted output level.
- `source_crossing_pulse_detector.vlogic_low` defaults to `0.0` V; valid range: finite real; sets the deasserted output level.
- `source_crossing_pulse_detector.tdel` defaults to `1e-09` s; valid range: tdel >= 0; sets output transition delay.
- `source_crossing_pulse_detector.trise` defaults to `2e-11` s; valid range: trise > 0; sets sigout rise smoothing.
- `source_crossing_pulse_detector.tfall` defaults to `2e-11` s; valid range: tfall > 0; sets sigout fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_CROSS_PULSE`: restore: A rising sigin crossing through sigcrossing initiates a sigout pulse. Required traces: `time`, `sigin`, `sigout`.
- `P_FALLING_CROSS_PULSE`: restore: A falling sigin crossing through sigcrossing also initiates a sigout pulse. Required traces: `time`, `sigin`, `sigout`.
- `P_PULSE_WIDTH`: restore: After each qualifying crossing, the output target remains at vlogic_high for pulse_width before returning to vlogic_low. Required traces: `time`, `sigin`, `sigout`.
- `P_LOW_BETWEEN_EVENTS`: restore: Sigout returns to vlogic_low between sufficiently separated threshold crossings. Required traces: `time`, `sigin`, `sigout`.
- `P_REPEATABLE_BIDIRECTIONAL_EVENTS`: restore: Alternating rising and falling crossings each produce corresponding pulses rather than only the first event or one polarity. Required traces: `time`, `sigin`, `sigout`.
- `P_TRANSITION_TIMING`: restore: Sigout changes use tdel delay with trise and tfall smoothing. Required traces: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Use bidirectional threshold crossing detection and timer-controlled pulse state.
- Drive sigout with a smoothed voltage contribution using the public timing parameters.
- Do not use current contributions, ddt(), idt(), transistor-level devices, AC/noise analysis, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `source_crossing_pulse_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
