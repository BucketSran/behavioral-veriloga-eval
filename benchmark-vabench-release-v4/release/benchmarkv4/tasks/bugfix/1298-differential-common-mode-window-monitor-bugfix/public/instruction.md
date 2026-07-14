# Differential Common Mode Window Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_common_mode_window_monitor.va`:
  - Module `differential_common_mode_window_monitor` (entry)
    - position 0: `vip` (input, electrical)
    - position 1: `vin` (input, electrical)
    - position 2: `vcm_ref` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `diff_ok` (output, electrical)
    - position 5: `cm_ok` (output, electrical)
    - position 6: `valid` (output, electrical)
    - position 7: `diff_metric` (output, electrical)
    - position 8: `cm_metric` (output, electrical)

## Public Parameter Contract

- `differential_common_mode_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `differential_common_mode_window_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `differential_common_mode_window_monitor.diff_max` defaults to `0.30`; valid range: finite; overrides diff_max.
- `differential_common_mode_window_monitor.diff_fullscale` defaults to `0.45`; valid range: finite; overrides diff_fullscale.
- `differential_common_mode_window_monitor.cm_tol` defaults to `0.080`; valid range: finite; overrides cm_tol.
- `differential_common_mode_window_monitor.cm_fullscale` defaults to `0.160`; valid range: finite; overrides cm_fullscale.
- `differential_common_mode_window_monitor.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONTINUOUSLY_COMPUTE_VDIFF_V_VIP_V`: restore: Continuously compute `vdiff = V(vip) - V(vin)` and `vcm = 0.5 * (V(vip) + V(vin))`. Drive `diff_ok` high only while `en` is high and `abs(vdiff)` is no larger than `diff_max`. Drive `cm_ok` high only while `en` is high and `abs(vcm - V(vcm_ref))` is no larger than `cm_tol`. Drive `valid` high only when both `diff_ok` and `cm_ok` would be high. Drive `diff_metric` as `vhi * clip(abs(vdiff) / diff_fullscale, 0, 1)` and `cm_metric` as `vhi * clip(abs(vcm - V(vcm_ref)) / cm_fullscale, 0, 1)`. Smooth the voltage-coded Boolean outputs with `transition()`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_BUILD_A_VOLTAGE_DOMAIN_INPUT_VALIDITY`: restore: Build a voltage-domain input-validity monitor for a differential analog front-end. The module checks whether the differential input magnitude remains inside a public linear range, whether the instantaneous common-mode level stays near a reference, and whether the enabled input pair is valid for downstream behavioral processing. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: restore: `vth = 0.45 V`: logic threshold for `en`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_VHI_0_9_V_HIGH_LEVEL`: restore: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_DIFF_MAX_0_30_V_MAXIMUM`: restore: `diff_max = 0.30 V`: maximum allowed `abs(V(vip) - V(vin))`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_DIFF_FULLSCALE_0_45_V_FULL`: restore: `diff_fullscale = 0.45 V`: full-scale value for `diff_metric`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_common_mode_window_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
