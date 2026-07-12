# Image-reject Mixer Calibration Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Image-reject Mixer Calibration Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `image_reject_mixer_cal_loop_top.va`:
  - Module `image_reject_mixer_cal_loop_top` (entry)
    - position 0: `rf_in` (inout, electrical)
    - position 1: `lo_i` (inout, electrical)
    - position 2: `lo_q` (inout, electrical)
    - position 3: `clk` (inout, electrical)
    - position 4: `rst` (inout, electrical)
    - position 5: `enable` (inout, electrical)
    - position 6: `i_out` (inout, electrical)
    - position 7: `q_out` (inout, electrical)
    - position 8: `image_metric` (inout, electrical)
    - position 9: `calibrated` (inout, electrical)
- Artifact `quadrature_mixer_proxy.va`:
  - Module `quadrature_mixer_proxy` (required_submodule)
    - position 0: `rf_in` (inout, electrical)
    - position 1: `lo_i` (inout, electrical)
    - position 2: `lo_q` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `gain_trim` (inout, electrical)
    - position 6: `phase_trim` (inout, electrical)
    - position 7: `i_out` (inout, electrical)
    - position 8: `q_out` (inout, electrical)
    - position 9: `raw_image_metric` (inout, electrical)
- Artifact `image_cal_controller.va`:
  - Module `image_cal_controller` (required_submodule)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `raw_image_metric` (inout, electrical)
    - position 4: `gain_trim` (inout, electrical)
    - position 5: `phase_trim` (inout, electrical)
    - position 6: `image_metric` (inout, electrical)
    - position 7: `calibrated` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `image_reject_mixer_cal_loop_top` as `XDUT` with ordered public binding: rf_in=rf_in, lo_i=lo_i, lo_q=lo_q, clk=clk, rst=rst, enable=enable, i_out=i_out, q_out=q_out, image_metric=image_metric, calibrated=calibrated.

## Public Parameter Contract

- `image_reject_mixer_cal_loop_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `image_reject_mixer_cal_loop_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `image_reject_mixer_cal_loop_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `image_reject_mixer_cal_loop_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `image_reject_mixer_cal_loop_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `image_reject_mixer_cal_loop_top.image_tol` defaults to `40e-3`; valid range: finite; overrides image_tol.
- `quadrature_mixer_proxy.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `quadrature_mixer_proxy.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `quadrature_mixer_proxy.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `quadrature_mixer_proxy.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `quadrature_mixer_proxy.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `image_cal_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `image_cal_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `image_cal_controller.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `image_cal_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `image_cal_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `image_cal_controller.image_tol` defaults to `40e-3`; valid range: finite; overrides image_tol.
- `image_cal_controller.step` defaults to `18e-3`; valid range: finite; overrides step.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear outputs, image metric, and `calibrated`. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, sample RF and quadrature LO inputs as voltage-domain mixer proxies. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_GENERATE_I_AND_Q_OUTPUTS_USING`: exercise and make observable: Generate I and Q outputs using opposite LO polarities. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_UPDATE_A_SIMPLE_GAIN_PHASE_CORRECTION`: exercise and make observable: Update a simple gain/phase correction state to reduce the image metric. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_ASSERT_CALIBRATED_AFTER_THREE_CONSECUTIVE_UPDA`: exercise and make observable: Assert `calibrated` after three consecutive updates with image metric below `image_tol`. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.

The required trace names are: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
