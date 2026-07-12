# Crossing Pulse Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Crossing Pulse Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `source_crossing_pulse_detector.va`:
  - Module `source_crossing_pulse_detector` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `source_crossing_pulse_detector` as `XDUT` with ordered public binding: sigin=sigin, sigout=sigout.

## Public Parameter Contract

- `source_crossing_pulse_detector.pulse_width` defaults to `4e-09` s; valid range: pulse_width > 0; sets output high duration after each qualifying crossing.
- `source_crossing_pulse_detector.sigcrossing` defaults to `0.45` V; valid range: finite real; sets the bidirectional sigin detection threshold.
- `source_crossing_pulse_detector.vlogic_high` defaults to `0.9` V; valid range: finite real; sets the asserted output level.
- `source_crossing_pulse_detector.vlogic_low` defaults to `0.0` V; valid range: finite real; sets the deasserted output level.
- `source_crossing_pulse_detector.tdel` defaults to `1e-09` s; valid range: tdel >= 0; sets output transition delay.
- `source_crossing_pulse_detector.trise` defaults to `2e-11` s; valid range: trise > 0; sets sigout rise smoothing.
- `source_crossing_pulse_detector.tfall` defaults to `2e-11` s; valid range: tfall > 0; sets sigout fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RISING_CROSS_PULSE`: exercise and make observable: A rising sigin crossing through sigcrossing initiates a sigout pulse. Required traces: `time`, `sigin`, `sigout`.
- `P_FALLING_CROSS_PULSE`: exercise and make observable: A falling sigin crossing through sigcrossing also initiates a sigout pulse. Required traces: `time`, `sigin`, `sigout`.
- `P_PULSE_WIDTH`: exercise and make observable: After each qualifying crossing, the output target remains at vlogic_high for pulse_width before returning to vlogic_low. Required traces: `time`, `sigin`, `sigout`.
- `P_LOW_BETWEEN_EVENTS`: exercise and make observable: Sigout returns to vlogic_low between sufficiently separated threshold crossings. Required traces: `time`, `sigin`, `sigout`.
- `P_REPEATABLE_BIDIRECTIONAL_EVENTS`: exercise and make observable: Alternating rising and falling crossings each produce corresponding pulses rather than only the first event or one polarity. Required traces: `time`, `sigin`, `sigout`.
- `P_TRANSITION_TIMING`: exercise and make observable: Sigout changes use tdel delay with trise and tfall smoothing. Required traces: `time`, `sigin`, `sigout`.

The required trace names are: `time`, `sigin`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
