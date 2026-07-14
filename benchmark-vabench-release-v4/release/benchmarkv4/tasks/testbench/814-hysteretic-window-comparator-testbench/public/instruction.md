# Hysteretic Window Comparator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Hysteretic Window Comparator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `hysteretic_window_comparator` as `XDUT` with ordered public binding: vin=vin, rst=rst, enable=enable, low_trip=low_trip, high_trip=high_trip, inside_flag=inside_flag, state_metric=state_metric, toggled=toggled.

## Public Parameter Contract

- `hysteretic_window_comparator.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `hysteretic_window_comparator.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `hysteretic_window_comparator.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `hysteretic_window_comparator.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `hysteretic_window_comparator.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `hysteretic_window_comparator.hyst` defaults to `10e-3`; valid range: finite; overrides hyst.
- `hysteretic_window_comparator.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear `inside_flag`, `state_metric`, and `toggled`. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_USE_LOW_TRIP_AND_HIGH_TRIP`: exercise and make observable: Use `low_trip` and `high_trip` as public voltage thresholds. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_ASSERT_INSIDE_FLAG_WHEN_VIN_ENTERS`: exercise and make observable: Assert `inside_flag` when `vin` enters the window and keep it asserted until `vin` crosses outside the hysteresis margins. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_EXPOSE_THE_CURRENT_STATE_AS_STATE`: exercise and make observable: Expose the current state as `state_metric` and pulse `toggled` high on state changes. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.
- `P_DO_NOT_CHATTER_FOR_SMALL_INPUT`: exercise and make observable: Do not chatter for small input movement inside the hysteresis band. Required traces: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.

The required trace names are: `time`, `vin`, `rst`, `enable`, `low_trip`, `high_trip`, `inside_flag`, `state_metric`, `toggled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
