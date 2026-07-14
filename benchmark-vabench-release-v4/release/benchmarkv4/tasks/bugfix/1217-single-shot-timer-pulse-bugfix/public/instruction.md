# Single Shot Timer Pulse Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `single_shot_timer_pulse.va`:
  - Module `single_shot_timer_pulse` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- `single_shot_timer_pulse.pulse_width` defaults to `2n`; valid range: finite; overrides pulse_width.
- `single_shot_timer_pulse.vlogic_high` defaults to `0.9`; valid range: finite; overrides vlogic_high.
- `single_shot_timer_pulse.vlogic_low` defaults to `0.0`; valid range: finite; overrides vlogic_low.
- `single_shot_timer_pulse.vtrans` defaults to `0.45`; valid range: finite; overrides vtrans.
- `single_shot_timer_pulse.tdel` defaults to `100p`; valid range: finite; overrides tdel.
- `single_shot_timer_pulse.trise` defaults to `10p`; valid range: finite; overrides trise.
- `single_shot_timer_pulse.tfall` defaults to `10p`; valid range: finite; overrides tfall.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DETECT_RISING_VIN_CROSSINGS_AT_VTRANS`: restore: Detect rising `vin` crossings at `vtrans`. Required traces: `time`, `vin`, `vout`.
- `P_ON_EACH_QUALIFYING_RISING_EDGE_DRIVE`: restore: On each qualifying rising edge, drive `vout` high after the configured transition delay. Required traces: `time`, `vin`, `vout`.
- `P_USE_A_TIMER_TO_SCHEDULE_THE`: restore: Use a timer to schedule the low-going state update at `edge_time + pulse_width + trise`, where `edge_time` is the qualifying rising input edge time. The voltage contribution still uses the public `tdel`, `trise`, and `tfall` transition parameters. Required traces: `time`, `vin`, `vout`.
- `P_GENERATE_ONE_OUTPUT_PULSE_PER_INPUT`: restore: Generate one output pulse per input rising edge. Required traces: `time`, `vin`, `vout`.
- `P_HOLD_THE_LOW_OUTPUT_LEVEL_BETWEEN`: restore: Hold the low output level between pulses. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `single_shot_timer_pulse.va`.
Every supplied `.va` file is editable; do not add or omit files.
