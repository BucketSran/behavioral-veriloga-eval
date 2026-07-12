# Differential-pair gm Limiter Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_pair_gm_limiter.va`:
  - Module `differential_pair_gm_limiter` (entry)
    - position 0: `vinp` (inout, electrical)
    - position 1: `vinn` (inout, electrical)
    - position 2: `bias` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `voutp` (inout, electrical)
    - position 5: `voutn` (inout, electrical)
    - position 6: `gm_metric` (inout, electrical)
    - position 7: `limit_flag` (inout, electrical)

## Public Parameter Contract

- `differential_pair_gm_limiter.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `differential_pair_gm_limiter.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `differential_pair_gm_limiter.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `differential_pair_gm_limiter.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `differential_pair_gm_limiter.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `differential_pair_gm_limiter.gm_gain` defaults to `4.0`; valid range: finite; overrides gm_gain.
- `differential_pair_gm_limiter.diff_limit` defaults to `120e-3 from (0:inf)`; valid range: finite; overrides diff_limit.
- `differential_pair_gm_limiter.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_WHEN_DISABLED_DRIVE_BOTH_OUTPUTS_TO`: restore: When disabled, drive both outputs to `vcm`, clear `gm_metric`, and clear `limit_flag`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_WHEN_ENABLED_CONVERT_THE_SAMPLED_DIFFERENTIAL`: restore: When enabled, convert the sampled differential input into equal-and-opposite output deviations around `vcm`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_SCALE_SMALL_SIGNAL_OUTPUT_SEPARATION_BY`: restore: Scale small-signal output separation by `gm_gain` and compress large differential inputs smoothly at `diff_limit`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_DRIVE_GM_METRIC_AS_A_VOLTAGE`: restore: Drive `gm_metric` as a voltage-coded estimate of the active transconductance region. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_ASSERT_LIMIT_FLAG_ONLY_WHEN_COMPRESSION`: restore: Assert `limit_flag` only when compression is active. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_pair_gm_limiter.va`.
Every supplied `.va` file is editable; do not add or omit files.
