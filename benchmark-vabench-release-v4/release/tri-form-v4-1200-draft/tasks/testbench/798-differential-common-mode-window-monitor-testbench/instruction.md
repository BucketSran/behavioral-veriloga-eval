# Differential Common Mode Window Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Differential Common Mode Window Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `differential_common_mode_window_monitor` as `XDUT` with ordered public binding: vip=vip, vin=vin, vcm_ref=vcm_ref, en=en, diff_ok=diff_ok, cm_ok=cm_ok, valid=valid, diff_metric=diff_metric, cm_metric=cm_metric.

## Public Parameter Contract

- `differential_common_mode_window_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `differential_common_mode_window_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `differential_common_mode_window_monitor.diff_max` defaults to `0.30`; valid range: finite; overrides diff_max.
- `differential_common_mode_window_monitor.diff_fullscale` defaults to `0.45`; valid range: finite; overrides diff_fullscale.
- `differential_common_mode_window_monitor.cm_tol` defaults to `0.080`; valid range: finite; overrides cm_tol.
- `differential_common_mode_window_monitor.cm_fullscale` defaults to `0.160`; valid range: finite; overrides cm_fullscale.
- `differential_common_mode_window_monitor.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONTINUOUSLY_COMPUTE_VDIFF_V_VIP_V`: exercise and make observable: Continuously compute `vdiff = V(vip) - V(vin)` and `vcm = 0.5 * (V(vip) + V(vin))`. Drive `diff_ok` high only while `en` is high and `abs(vdiff)` is no larger than `diff_max`. Drive `cm_ok` high only while `en` is high and `abs(vcm - V(vcm_ref))` is no larger than `cm_tol`. Drive `valid` high only when both `diff_ok` and `cm_ok` would be high. Drive `diff_metric` as `vhi * clip(abs(vdiff) / diff_fullscale, 0, 1)` and `cm_metric` as `vhi * clip(abs(vcm - V(vcm_ref)) / cm_fullscale, 0, 1)`. Smooth the voltage-coded Boolean outputs with `transition()`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_BUILD_A_VOLTAGE_DOMAIN_INPUT_VALIDITY`: exercise and make observable: Build a voltage-domain input-validity monitor for a differential analog front-end. The module checks whether the differential input magnitude remains inside a public linear range, whether the instantaneous common-mode level stays near a reference, and whether the enabled input pair is valid for downstream behavioral processing. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `en`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_DIFF_MAX_0_30_V_MAXIMUM`: exercise and make observable: `diff_max = 0.30 V`: maximum allowed `abs(V(vip) - V(vin))`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.
- `P_DIFF_FULLSCALE_0_45_V_FULL`: exercise and make observable: `diff_fullscale = 0.45 V`: full-scale value for `diff_metric`. Required traces: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.

The required trace names are: `time`, `cm_metric`, `cm_ok`, `diff_metric`, `diff_ok`, `en`, `valid`, `vcm_ref`, `vin`, `vip`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
