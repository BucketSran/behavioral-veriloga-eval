# Bandgap Startup and Trim System Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bandgap_trim_top.va`:
  - Module `bandgap_trim_top` (entry)
    - position 0: `vdd_sense` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `trim_req` (inout, electrical)
    - position 4: `temp_proxy` (inout, electrical)
    - position 5: `vref` (inout, electrical)
    - position 6: `trim_3` (inout, electrical)
    - position 7: `trim_2` (inout, electrical)
    - position 8: `trim_1` (inout, electrical)
    - position 9: `trim_0` (inout, electrical)
    - position 10: `ready` (inout, electrical)
    - position 11: `error_metric` (inout, electrical)
- Artifact `startup_detector.va`:
  - Module `startup_detector` (required_submodule)
    - position 0: `vdd_sense` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `startup_en` (inout, electrical)
- Artifact `ptat_ctat_core.va`:
  - Module `ptat_ctat_core` (required_submodule)
    - position 0: `temp_proxy` (inout, electrical)
    - position 1: `startup_en` (inout, electrical)
    - position 2: `core_ref` (inout, electrical)
- Artifact `trim_controller.va`:
  - Module `trim_controller` (required_submodule)
    - position 0: `clk` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `trim_req` (inout, electrical)
    - position 3: `startup_en` (inout, electrical)
    - position 4: `core_ref` (inout, electrical)
    - position 5: `trim_3` (inout, electrical)
    - position 6: `trim_2` (inout, electrical)
    - position 7: `trim_1` (inout, electrical)
    - position 8: `trim_0` (inout, electrical)
    - position 9: `trim_corr` (inout, electrical)
    - position 10: `ready` (inout, electrical)
    - position 11: `error_metric` (inout, electrical)

## Public Parameter Contract

- `bandgap_trim_top.vhi` defaults to `0.9` V; valid range: finite; overrides logic high and upper clamp.
- `bandgap_trim_top.vlo` defaults to `0.0` V; valid range: finite; overrides logic low and lower clamp.
- `bandgap_trim_top.vpor` defaults to `0.72` V; valid range: finite; overrides startup threshold.
- `bandgap_trim_top.vref_nom` defaults to `0.6` V; valid range: finite; overrides nominal reference target.
- `bandgap_trim_top.trim_lsb` defaults to `2e-3` V; valid range: finite positive; overrides reference correction per trim-code step.
- `bandgap_trim_top.ready_tol` defaults to `5e-3` V; valid range: finite positive; overrides ready tolerance around reference target.
- `bandgap_trim_top.vth` defaults to `0.45` V; valid range: finite; overrides clock/reset/trim threshold.
- `bandgap_trim_top.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `startup_detector.vhi` defaults to `0.9` V; valid range: finite; overrides logic high output level.
- `startup_detector.vlo` defaults to `0.0` V; valid range: finite; overrides logic low output level.
- `startup_detector.vpor` defaults to `0.72` V; valid range: finite; overrides startup threshold.
- `startup_detector.vth` defaults to `0.45` V; valid range: finite; overrides clock/reset threshold.
- `startup_detector.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `ptat_ctat_core.vhi` defaults to `0.9` V; valid range: finite; overrides upper reference clamp.
- `ptat_ctat_core.vlo` defaults to `0.0` V; valid range: finite; overrides lower reference clamp.
- `ptat_ctat_core.vref_nom` defaults to `0.6` V; valid range: finite; overrides nominal reference target.
- `ptat_ctat_core.vth` defaults to `0.45` V; valid range: finite; overrides startup enable threshold.
- `ptat_ctat_core.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.
- `trim_controller.vhi` defaults to `0.9` V; valid range: finite; overrides logic high output level.
- `trim_controller.vlo` defaults to `0.0` V; valid range: finite; overrides logic low output level.
- `trim_controller.vref_nom` defaults to `0.6` V; valid range: finite; overrides nominal reference target.
- `trim_controller.trim_lsb` defaults to `2e-3` V; valid range: finite positive; overrides reference correction per trim-code step.
- `trim_controller.ready_tol` defaults to `5e-3` V; valid range: finite positive; overrides ready tolerance around reference target.
- `trim_controller.vth` defaults to `0.45` V; valid range: finite; overrides clock/reset/trim threshold.
- `trim_controller.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides output transition smoothing time.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_BROWNOUT_CLEAR`: restore: On reset or brownout below POR, clear trim code, ready, error metric, and drive vref low. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `trim_req`, `temp_proxy`, `vref`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `ready`, `error_metric`.
- `P_POR_STARTUP`: restore: Enable the reference only after vdd_sense remains above vpor for two consecutive rising clock edges. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `trim_req`, `temp_proxy`, `vref`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `ready`, `error_metric`.
- `P_CORE_REFERENCE`: restore: Generate a behavioral PTAT/CTAT reference metric from temp_proxy around vref_nom. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `trim_req`, `temp_proxy`, `vref`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `ready`, `error_metric`.
- `P_TRIM_SEARCH`: restore: When trim_req is high, update the 4-bit trim code once per rising clock edge to reduce reference error. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `trim_req`, `temp_proxy`, `vref`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `ready`, `error_metric`.
- `P_READY_QUALIFICATION`: restore: Assert ready only after three consecutive enabled updates with error magnitude within ready_tol. Required traces: `time`, `vdd_sense`, `clk`, `rst`, `trim_req`, `temp_proxy`, `vref`, `trim_3`, `trim_2`, `trim_1`, `trim_0`, `ready`, `error_metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Use voltage contributions for public electrical outputs.
- Do not instantiate transistor-level devices or add testbench, checker, pass/fail, or debug-only ports.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bandgap_trim_top.va`, `startup_detector.va`, `ptat_ctat_core.va`, `trim_controller.va`.
Every supplied `.va` file is editable; do not add or omit files.
