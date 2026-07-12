# Differential-pair gm Limiter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Differential-pair gm Limiter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `differential_pair_gm_limiter` as `XDUT` with ordered public binding: vinp=vinp, vinn=vinn, bias=bias, enable=enable, voutp=voutp, voutn=voutn, gm_metric=gm_metric, limit_flag=limit_flag.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_WHEN_DISABLED_DRIVE_BOTH_OUTPUTS_TO`: exercise and make observable: When disabled, drive both outputs to `vcm`, clear `gm_metric`, and clear `limit_flag`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_WHEN_ENABLED_CONVERT_THE_SAMPLED_DIFFERENTIAL`: exercise and make observable: When enabled, convert the sampled differential input into equal-and-opposite output deviations around `vcm`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_SCALE_SMALL_SIGNAL_OUTPUT_SEPARATION_BY`: exercise and make observable: Scale small-signal output separation by `gm_gain` and compress large differential inputs smoothly at `diff_limit`. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_DRIVE_GM_METRIC_AS_A_VOLTAGE`: exercise and make observable: Drive `gm_metric` as a voltage-coded estimate of the active transconductance region. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_ASSERT_LIMIT_FLAG_ONLY_WHEN_COMPRESSION`: exercise and make observable: Assert `limit_flag` only when compression is active. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.

The required trace names are: `time`, `vinp`, `vinn`, `bias`, `enable`, `voutp`, `voutn`, `gm_metric`, `limit_flag`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
