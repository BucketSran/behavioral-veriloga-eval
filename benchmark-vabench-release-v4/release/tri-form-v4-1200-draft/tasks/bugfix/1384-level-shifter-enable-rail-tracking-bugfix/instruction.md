# Level Shifter with Enable and Rail Tracking Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `level_shifter_enable_rail_tracking.va`:
  - Module `level_shifter_enable_rail_tracking` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `enable` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `vddl` (input, electrical)
    - position 4: `vddh` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `valid` (output, electrical)

## Public Parameter Contract

- `level_shifter_enable_rail_tracking.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `level_shifter_enable_rail_tracking.vth_default` defaults to `0.45`; valid range: finite; overrides vth_default.
- `level_shifter_enable_rail_tracking.min_high_rail` defaults to `0.2`; valid range: finite; overrides min_high_rail.
- `level_shifter_enable_rail_tracking.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_LOW_ENABLE_DRIVES_VOUT`: restore: Reset or low `enable` drives `vout` to `vss` and clears `valid`. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_WHEN_ENABLED_COMPARE_VIN_AGAINST_HALF`: restore: When enabled, compare `vin` against half of the sensed low-side rail `vddl`. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_DRIVE_VOUT_TO_VDDH_FOR_A`: restore: Drive `vout` to `vddh` for a high input and to `vss` for a low input. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_VALID_IS_HIGH_ONLY_WHEN_ENABLED`: restore: `valid` is high only when enabled, not reset, and the high-side rail is above the minimum valid rail. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_THE_OUTPUT_HIGH_LEVEL_MUST_TRACK`: restore: The output high level must track changes in `vddh`; it must not use a fixed internal high level. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `level_shifter_enable_rail_tracking.va`.
Every supplied `.va` file is editable; do not add or omit files.
