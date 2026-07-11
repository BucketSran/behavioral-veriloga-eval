# Level Shifter with Enable and Rail Tracking

## Task Contract

Implement one Verilog-A DUT artifact for `Level Shifter with Enable and Rail Tracking`.

- Target artifact: `level_shifter_enable_rail_tracking.va`
- Public top module: `level_shifter_enable_rail_tracking`
- Task level: `L1`
- Circuit category: `bias_reference_power_management`

## Public Verilog-A Interface

Declare module `level_shifter_enable_rail_tracking` with positional electrical ports `vin, enable, rst, vddl, vddh, vout, valid`. All ports are electrical.

`vin` is referenced to the low-voltage input rail `vddl`; `vddh` is the high-side output rail. `enable` and `rst` are voltage-coded controls.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vss = 0.0 V`: shared ground reference
- `vth_default = 0.45 V`: fallback threshold if `vddl` is too small
- `min_high_rail = 0.2 V`: minimum high-side rail for valid operation
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or low `enable` drives `vout` to `vss` and clears `valid`.
- When enabled, compare `vin` against half of the sensed low-side rail `vddl`.
- Drive `vout` to `vddh` for a high input and to `vss` for a low input.
- `valid` is high only when enabled, not reset, and the high-side rail is above the minimum valid rail.
- The output high level must track changes in `vddh`; it must not use a fixed internal high level.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, verification harnesses, simulation decks, generated result files, logs, reports, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `level_shifter_enable_rail_tracking.va`.
