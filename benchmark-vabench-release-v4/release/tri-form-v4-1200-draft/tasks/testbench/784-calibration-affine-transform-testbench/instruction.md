# Calibration Affine Transform Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Calibration Affine Transform` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `calibration_affine_transform` as `XDUT` with ordered public binding: clk=clk, rst=rst, raw=raw, gain_ctrl=gain_ctrl, offset_ctrl=offset_ctrl, en=en, out=out, resid_metric=resid_metric.

## Public Parameter Contract

- `calibration_affine_transform.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `calibration_affine_transform.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `calibration_affine_transform.center` defaults to `0.45`; valid range: finite; overrides center.
- `calibration_affine_transform.gain_base` defaults to `0.50`; valid range: finite; overrides gain_base.
- `calibration_affine_transform.gain_span` defaults to `1.00`; valid range: finite; overrides gain_span.
- `calibration_affine_transform.resid_fullscale` defaults to `0.45`; valid range: finite; overrides resid_fullscale.
- `calibration_affine_transform.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CLOCK_CROSSING_COMPUTE`: exercise and make observable: On each rising clock crossing, compute a local affine calibration transform from raw, gain_ctrl, and offset_ctrl while reset is low and enable is high. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_MAP_GAIN_CTRL_TO_A_PUBLIC`: exercise and make observable: Map gain_ctrl to a public gain range and offset_ctrl to a centered offset. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_CLEAR_OUTPUT_AND_METRIC_WHILE_RESET`: exercise and make observable: Clear output and metric while reset is high or enable is low; otherwise clip the transformed output into the public voltage-coded range. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_EXPOSE_A_BOUNDED_RESIDUAL_METRIC_FOR`: exercise and make observable: Expose a bounded residual metric for the transform magnitude. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: exercise and make observable: Use local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.

The required trace names are: `time`, `clk`, `en`, `gain_ctrl`, `offset_ctrl`, `out`, `raw`, `resid_metric`, `rst`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
