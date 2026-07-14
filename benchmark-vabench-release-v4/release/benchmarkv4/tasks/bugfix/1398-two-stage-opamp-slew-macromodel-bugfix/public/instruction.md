# Two-stage Op-amp Slew Macromodel Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `two_stage_opamp_slew_macromodel.va`:
  - Module `two_stage_opamp_slew_macromodel` (entry)
    - position 0: `vinp` (inout, electrical)
    - position 1: `vinn` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `load_step` (inout, electrical)
    - position 6: `vout` (inout, electrical)
    - position 7: `stage1_metric` (inout, electrical)
    - position 8: `slew_metric` (inout, electrical)
    - position 9: `clamp_flag` (inout, electrical)
    - position 10: `settled` (inout, electrical)

## Public Parameter Contract

- `two_stage_opamp_slew_macromodel.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `two_stage_opamp_slew_macromodel.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `two_stage_opamp_slew_macromodel.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `two_stage_opamp_slew_macromodel.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `two_stage_opamp_slew_macromodel.stage1_gain` defaults to `20.0`; valid range: finite; overrides stage1_gain.
- `two_stage_opamp_slew_macromodel.stage2_gain` defaults to `5.0`; valid range: finite; overrides stage2_gain.
- `two_stage_opamp_slew_macromodel.slew_step` defaults to `80e-3`; valid range: finite; overrides slew_step.
- `two_stage_opamp_slew_macromodel.settle_tol` defaults to `10e-3`; valid range: finite; overrides settle_tol.
- `two_stage_opamp_slew_macromodel.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `two_stage_opamp_slew_macromodel.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: restore: On reset or when `enable` is low, drive `vout` and `stage1_metric` to `vcm`, clear `slew_metric`, `clamp_flag`, and `settled`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: restore: On each rising `clk` edge while enabled, sample the differential input `vinp - vinn`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_COMPUTE_A_FIRST_STAGE_METRIC_FROM`: restore: Compute a first-stage metric from the sampled differential input, centered around `vcm` and limited to `[vss, vdd]`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_COMPUTE_AN_OUTPUT_TARGET_FROM_THE`: restore: Compute an output target from the first-stage metric and `stage2_gain`; `load_step` may request a bounded target perturbation around the same common-mode reference. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_CLAMP_THE_OUTPUT_TARGET_TO_VSS`: restore: Clamp the output target to `[vss, vdd]` and assert `clamp_flag` only when clamping occurs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_MOVE_VOUT_TOWARD_THE_CLAMPED_TARGET`: restore: Move `vout` toward the clamped target by no more than `slew_step` per enabled clock edge. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_ASSERT_SETTLED_ONLY_AFTER_TWO_CONSECUTIVE_UPDATES`: restore: Assert `settled` only after the output error has remained within `settle_tol` for two consecutive enabled updates. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `two_stage_opamp_slew_macromodel.va`.
Every supplied `.va` file is editable; do not add or omit files.
