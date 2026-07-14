# Source-follower Buffer Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `source_follower_buffer_macro.va`:
  - Module `source_follower_buffer_macro` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vbias` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `headroom_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

## Public Parameter Contract

- `source_follower_buffer_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `source_follower_buffer_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `source_follower_buffer_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `source_follower_buffer_macro.vgs_drop` defaults to `0.12`; valid range: finite; overrides vgs_drop.
- `source_follower_buffer_macro.min_headroom` defaults to `0.10`; valid range: finite; overrides min_headroom.
- `source_follower_buffer_macro.tr` defaults to `150p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_OR_LOW_ENABLE_DRIVES_THE`: restore: Reset or low `enable` drives the output and metrics low. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_WHEN_ENABLED_THE_OUTPUT_FOLLOWS_VIN`: restore: When enabled, the output follows `vin - vgs_drop`. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_CLAMP_THE_OUTPUT_BETWEEN_VSS_AND`: restore: Clamp the output between `vss` and `vbias - min_headroom`. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_HEADROOM_METRIC_REPORTS_THE_REMAINING_VBIAS`: restore: `headroom_metric` reports the remaining `vbias - vout` margin clipped to the nominal flag range. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_VALID_IS_HIGH_ONLY_WHEN_ENABLED`: restore: `valid` is high only when enabled, not reset, and the bias rail can support at least the minimum headroom. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `source_follower_buffer_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
