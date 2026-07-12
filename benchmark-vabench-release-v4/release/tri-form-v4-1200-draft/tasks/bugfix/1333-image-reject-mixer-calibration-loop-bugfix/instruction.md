# Image-reject Mixer Calibration Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear outputs, image metric, and `calibrated`. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, sample RF and quadrature LO inputs as voltage-domain mixer proxies. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_GENERATE_I_AND_Q_OUTPUTS_USING`: restore: Generate I and Q outputs using opposite LO polarities. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_UPDATE_A_SIMPLE_GAIN_PHASE_CORRECTION`: restore: Update a simple gain/phase correction state to reduce the image metric. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.
- `P_ASSERT_CALIBRATED_AFTER_THREE_CONSECUTIVE_UPDA`: restore: Assert `calibrated` after three consecutive updates with image metric below `image_tol`. Required traces: `time`, `rf_in`, `lo_i`, `lo_q`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `image_metric`, `calibrated`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `image_reject_mixer_cal_loop_top.va`, `quadrature_mixer_proxy.va`, `image_cal_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
