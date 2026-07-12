# Single Shot Pulse Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `source_single_shot.va`:
  - Module `source_single_shot` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- `source_single_shot.pulse_width` defaults to `1e-08` s; valid range: pulse_width > 0; sets output high duration after a qualifying rising crossing.
- `source_single_shot.vlogic_high` defaults to `0.9` V; valid range: finite real; sets the asserted output level.
- `source_single_shot.vlogic_low` defaults to `0.0` V; valid range: finite real; sets the deasserted output level.
- `source_single_shot.vtrans` defaults to `0.45` V; valid range: finite real; sets the rising vin trigger threshold.
- `source_single_shot.tdel` defaults to `1e-09` s; valid range: tdel >= 0; sets output transition delay.
- `source_single_shot.trise` defaults to `2e-11` s; valid range: trise > 0; sets vout rise smoothing.
- `source_single_shot.tfall` defaults to `2e-11` s; valid range: tfall > 0; sets vout fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_CROSS_TRIGGER`: restore: Each qualifying rising vin crossing through vtrans initiates an output pulse. Required traces: `time`, `vin`, `vout`.
- `P_NO_FALLING_TRIGGER`: restore: Falling vin crossings do not initiate pulses. Required traces: `time`, `vin`, `vout`.
- `P_PULSE_WIDTH`: restore: After a qualifying trigger, the output target remains high for pulse_width before returning low. Required traces: `time`, `vin`, `vout`.
- `P_OUTPUT_LEVELS`: restore: The deasserted and asserted targets are vlogic_low and vlogic_high respectively. Required traces: `time`, `vin`, `vout`.
- `P_REPEATABLE_ONE_SHOTS`: restore: Distinct qualifying rising edges produce corresponding pulses and vout returns low between sufficiently separated events. Required traces: `time`, `vin`, `vout`.
- `P_TRANSITION_TIMING`: restore: Output changes use tdel delay with trise and tfall smoothing without altering the logical pulse duration contract. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use a rising-threshold crossing event and timer-controlled pulse state.
- Drive vout with a smoothed voltage contribution using the public timing parameters.
- Do not use current contributions, ddt(), idt(), transistor-level devices, AC/noise analysis, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `source_single_shot.va`.
Every supplied `.va` file is editable; do not add or omit files.
