# Two-stage Op-amp Slew Macromodel Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Two-stage Op-amp Slew Macromodel` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `two_stage_opamp_slew_macromodel` as `XDUT` with ordered public binding: vinp=vinp, vinn=vinn, clk=clk, rst=rst, enable=enable, load_step=load_step, vout=vout, stage1_metric=stage1_metric, slew_metric=slew_metric, clamp_flag=clamp_flag, settled=settled.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_ENABLE_IS`: exercise and make observable: On reset or when `enable` is low, drive `vout` and `stage1_metric` to `vcm`, clear `slew_metric`, `clamp_flag`, and `settled`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_ON_EACH_RISING_CLK_EDGE_WHILE`: exercise and make observable: On each rising `clk` edge while enabled, sample the differential input `vinp - vinn`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_COMPUTE_A_FIRST_STAGE_METRIC_FROM`: exercise and make observable: Compute a first-stage metric from the sampled differential input, centered around `vcm` and limited to `[vss, vdd]`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_COMPUTE_AN_OUTPUT_TARGET_FROM_THE`: exercise and make observable: Compute an output target from the first-stage metric and `stage2_gain`; `load_step` may request a bounded target perturbation around the same common-mode reference. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_CLAMP_THE_OUTPUT_TARGET_TO_VSS`: exercise and make observable: Clamp the output target to `[vss, vdd]` and assert `clamp_flag` only when clamping occurs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_MOVE_VOUT_TOWARD_THE_CLAMPED_TARGET`: exercise and make observable: Move `vout` toward the clamped target by no more than `slew_step` per enabled clock edge. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.
- `P_ASSERT_SETTLED_ONLY_AFTER_TWO_CONSECUTIVE_UPDATES`: exercise and make observable: Assert `settled` only after the output error has remained within `settle_tol` for two consecutive enabled updates. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.

The required trace names are: `time`, `vinp`, `vinn`, `clk`, `rst`, `enable`, `load_step`, `vout`, `stage1_metric`, `slew_metric`, `clamp_flag`, `settled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
