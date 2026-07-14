# Calibration Affine Transform Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `calibration_affine_transform.va`:
  - Module `calibration_affine_transform` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `raw` (input, electrical)
    - position 3: `gain_ctrl` (input, electrical)
    - position 4: `offset_ctrl` (input, electrical)
    - position 5: `en` (input, electrical)
    - position 6: `out` (output, electrical)
    - position 7: `resid_metric` (output, electrical)

## Public Parameter Contract

- `calibration_affine_transform.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `calibration_affine_transform.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `calibration_affine_transform.center` defaults to `0.45`; valid range: finite; overrides center.
- `calibration_affine_transform.gain_base` defaults to `0.50`; valid range: finite; overrides gain_base.
- `calibration_affine_transform.gain_span` defaults to `1.00`; valid range: finite; overrides gain_span.
- `calibration_affine_transform.resid_fullscale` defaults to `0.45`; valid range: finite; overrides resid_fullscale.
- `calibration_affine_transform.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CLOCK_CROSSING_COMPUTE`: restore: On each rising clock crossing, compute a local affine calibration transform from raw, gain_ctrl, and offset_ctrl while reset is low and enable is high. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_MAP_GAIN_CTRL_TO_A_PUBLIC`: restore: Map gain_ctrl to a public gain range and offset_ctrl to a centered offset. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_CLEAR_OUTPUT_AND_METRIC_WHILE_RESET`: restore: Clear output and metric while reset is high or enable is low; otherwise clip the transformed output into the public voltage-coded range. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_EXPOSE_A_BOUNDED_RESIDUAL_METRIC_FOR`: restore: Expose a bounded residual metric for the transform magnitude. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: restore: Use local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `calibration_affine_transform.va`.
Every supplied `.va` file is editable; do not add or omit files.
