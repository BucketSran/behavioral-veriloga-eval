# Track/Hold with Droop and Aperture Metric Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `track_hold_aperture.va`:
  - Module `track_hold_aperture` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `track` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `vhold` (output, electrical)
    - position 5: `aperture_metric` (output, electrical)
    - position 6: `droop_metric` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `track_hold_aperture.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `track_hold_aperture.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `track_hold_aperture.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `track_hold_aperture.tick` defaults to `1n from (0:inf)`; valid range: finite; overrides tick.
- `track_hold_aperture.droop_per_tick` defaults to `0.015 from [0:inf)`; valid range: finite; overrides droop_per_tick.
- `track_hold_aperture.aperture_gain` defaults to `0.6 from [0:inf)`; valid range: finite; overrides aperture_gain.
- `track_hold_aperture.tr` defaults to `100p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or a low `enable` clears `vhold`, `aperture_metric`, `droop_metric`, and `valid`. Required traces: `time`, `vin`, `track`, `rst`, `enable`, `vhold`, `aperture_metric`, `droop_metric`, `valid`.
- `P_TRACK_MODE_FOLLOWS_INPUT`: restore: While `track` is high and the DUT is enabled, the held state follows `vin` at the internal update cadence and `valid` remains low. Required traces: `time`, `vin`, `track`, `rst`, `enable`, `vhold`, `valid`.
- `P_FALLING_TRACK_SAMPLE_APERTURE`: restore: A falling `track` edge samples `vin`, asserts `valid`, and reports an aperture metric proportional to the step from the previous tracked value. Required traces: `time`, `vin`, `track`, `enable`, `vhold`, `aperture_metric`, `valid`.
- `P_HOLD_MODE_DROOP`: restore: During hold mode, `vhold` droops downward by `droop_per_tick` on each update tick without going below `vss`. Required traces: `time`, `track`, `enable`, `vhold`, `droop_metric`.
- `P_DROOP_METRIC_ACCUMULATION`: restore: `droop_metric` accumulates total hold-mode droop and clears on a new sample, reset, or disable. Required traces: `time`, `track`, `rst`, `enable`, `droop_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `track_hold_aperture.va`.
Every supplied `.va` file is editable; do not add or omit files.
