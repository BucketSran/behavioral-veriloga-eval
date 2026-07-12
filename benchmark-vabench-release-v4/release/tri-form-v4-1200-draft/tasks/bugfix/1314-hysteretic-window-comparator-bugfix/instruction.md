# Hysteretic Window Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `hysteretic_window_comparator.va`:
  - Module `hysteretic_window_comparator` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `low_trip` (input, electrical)
    - position 4: `high_trip` (input, electrical)
    - position 5: `inside_flag` (output, electrical)
    - position 6: `state_metric` (output, electrical)
    - position 7: `toggled` (output, electrical)

## Public Parameter Contract

- `hysteretic_window_comparator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `hysteretic_window_comparator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `hysteretic_window_comparator.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `hysteretic_window_comparator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `hysteretic_window_comparator.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `hysteretic_window_comparator.hyst` defaults to `10e-3`; valid range: finite; overrides hyst.
- `hysteretic_window_comparator.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear `inside_flag`, `state_metric`, and `toggled`. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_USE_LOW_TRIP_AND_HIGH_TRIP`: restore: Use `low_trip` and `high_trip` as public voltage thresholds. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_ASSERT_INSIDE_FLAG_WHEN_VIN_ENTERS`: restore: Assert `inside_flag` when `vin` enters the window and keep it asserted until `vin` crosses outside the hysteresis margins. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_EXPOSE_THE_CURRENT_STATE_AS_STATE`: restore: Expose the current state as `state_metric` and pulse `toggled` high on state changes. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_DO_NOT_CHATTER_FOR_SMALL_INPUT`: restore: Do not chatter for small input movement inside the hysteresis band. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `hysteretic_window_comparator.va`.
Every supplied `.va` file is editable; do not add or omit files.
