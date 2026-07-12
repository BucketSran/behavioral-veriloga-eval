# 2-tap DFE Receiver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dfe_rx_top.va`:
  - Module `dfe_rx_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `tap1_1` (input, electrical)
    - position 4: `tap1_0` (input, electrical)
    - position 5: `tap2_1` (input, electrical)
    - position 6: `tap2_0` (input, electrical)
    - position 7: `decision` (output, electrical)
    - position 8: `fb_metric` (output, electrical)
    - position 9: `slicer_in_dbg` (output, electrical)
- Artifact `slicer.va`:
  - Module `slicer` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `fb_metric` (input, electrical)
    - position 3: `decision_raw` (output, electrical)
    - position 4: `slicer_in_dbg` (output, electrical)
- Artifact `feedback_filter.va`:
  - Module `feedback_filter` (required_submodule)
    - position 0: `tap1_1` (input, electrical)
    - position 1: `tap1_0` (input, electrical)
    - position 2: `tap2_1` (input, electrical)
    - position 3: `tap2_0` (input, electrical)
    - position 4: `hist1` (input, electrical)
    - position 5: `hist2` (input, electrical)
    - position 6: `fb_metric` (output, electrical)
- Artifact `decision_latch.va`:
  - Module `decision_latch` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `slicer_in_dbg` (input, electrical)
    - position 3: `decision` (output, electrical)
    - position 4: `hist1` (output, electrical)
    - position 5: `hist2` (output, electrical)

## Public Parameter Contract

- `dfe_rx_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module dfe_rx_top.
- `dfe_rx_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module dfe_rx_top.
- `dfe_rx_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module dfe_rx_top.
- `dfe_rx_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module dfe_rx_top.
- `dfe_rx_top.tap_lsb` defaults to `20e-3`; valid range: finite; overrides tap_lsb for module dfe_rx_top.
- `dfe_rx_top.tr` defaults to `200e-12`; valid range: finite; overrides tr for module dfe_rx_top.
- `slicer.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module slicer.
- `slicer.vss` defaults to `0.0`; valid range: finite; overrides vss for module slicer.
- `slicer.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module slicer.
- `slicer.vth` defaults to `0.45`; valid range: finite; overrides vth for module slicer.
- `slicer.tr` defaults to `200e-12`; valid range: finite; overrides tr for module slicer.
- `feedback_filter.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module feedback_filter.
- `feedback_filter.vss` defaults to `0.0`; valid range: finite; overrides vss for module feedback_filter.
- `feedback_filter.vth` defaults to `0.45`; valid range: finite; overrides vth for module feedback_filter.
- `feedback_filter.tap_lsb` defaults to `20e-3`; valid range: finite; overrides tap_lsb for module feedback_filter.
- `feedback_filter.tr` defaults to `200e-12`; valid range: finite; overrides tr for module feedback_filter.
- `decision_latch.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module decision_latch.
- `decision_latch.vss` defaults to `0.0`; valid range: finite; overrides vss for module decision_latch.
- `decision_latch.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module decision_latch.
- `decision_latch.vth` defaults to `0.45`; valid range: finite; overrides vth for module decision_latch.
- `decision_latch.tr` defaults to `200e-12`; valid range: finite; overrides tr for module decision_latch.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_CLEAR`: restore: Reset clears the decision history and all public outputs. Required traces: `time`, `rst`, `decision`, `fb_metric`, `slicer_in_dbg`.
- `P_TWO_TAP_FEEDBACK`: restore: The feedback metric uses both configured taps and the previous two decisions. Required traces: `time`, `clk`, `rst`, `tap1_1`, `tap1_0`, `tap2_1`, `tap2_0`, `decision`, `fb_metric`.
- `P_CORRECTED_INPUT`: restore: The debug slicer input equals VIN minus the active signed feedback correction. Required traces: `time`, `vin`, `clk`, `rst`, `fb_metric`, `slicer_in_dbg`.
- `P_CLOCKED_DECISION`: restore: Each rising clock edge latches the threshold decision derived from the corrected input. Required traces: `time`, `vin`, `clk`, `rst`, `decision`, `slicer_in_dbg`.
- `P_HISTORY_ORDER`: restore: Feedback for a decision is based only on decisions from preceding clock edges. Required traces: `time`, `vin`, `clk`, `rst`, `decision`, `fb_metric`, `slicer_in_dbg`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Preserve the declared module graph, port order, parameter override behavior, and public trace observability.
- Do not hard-code evaluator stimulus, stop times, sample windows, checker tolerances, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dfe_rx_top.va`, `slicer.va`, `feedback_filter.va`, `decision_latch.va`.
Every supplied `.va` file is editable; do not add or omit files.
