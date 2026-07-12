# Level Shifter with Enable and Rail Tracking Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Level Shifter with Enable and Rail Tracking` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `level_shifter_enable_rail_tracking.va`:
  - Module `level_shifter_enable_rail_tracking` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `enable` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `vddl` (input, electrical)
    - position 4: `vddh` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `level_shifter_enable_rail_tracking` as `XDUT` with ordered public binding: vin=vin, enable=enable, rst=rst, vddl=vddl, vddh=vddh, vout=vout, valid=valid.

## Public Parameter Contract

- `level_shifter_enable_rail_tracking.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `level_shifter_enable_rail_tracking.vth_default` defaults to `0.45`; valid range: finite; overrides vth_default.
- `level_shifter_enable_rail_tracking.min_high_rail` defaults to `0.2`; valid range: finite; overrides min_high_rail.
- `level_shifter_enable_rail_tracking.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_LOW_ENABLE_DRIVES_VOUT`: exercise and make observable: Reset or low `enable` drives `vout` to `vss` and clears `valid`. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_WHEN_ENABLED_COMPARE_VIN_AGAINST_HALF`: exercise and make observable: When enabled, compare `vin` against half of the sensed low-side rail `vddl`. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_DRIVE_VOUT_TO_VDDH_FOR_A`: exercise and make observable: Drive `vout` to `vddh` for a high input and to `vss` for a low input. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_VALID_IS_HIGH_ONLY_WHEN_ENABLED`: exercise and make observable: `valid` is high only when enabled, not reset, and the high-side rail is above the minimum valid rail. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.
- `P_THE_OUTPUT_HIGH_LEVEL_MUST_TRACK`: exercise and make observable: The output high level must track changes in `vddh`; it must not use a fixed internal high level. Required traces: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.

The required trace names are: `time`, `vin`, `enable`, `rst`, `vddl`, `vddh`, `vout`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
