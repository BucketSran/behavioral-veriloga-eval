# CPPLL Tracking Reacquire Timer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cppll_timer_ref.va`:
  - Module `cppll_timer_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `ref_clk` (input, electrical)
    - position 3: `fb_clk` (output, electrical)
    - position 4: `dco_clk` (output, electrical)
    - position 5: `vctrl_mon` (output, electrical)
    - position 6: `lock` (output, electrical)
- Artifact `ref_step_clk.va`:
  - Module `ref_step_clk` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `CLK` (output, electrical)

## Public Parameter Contract

- `cppll_timer_ref.div_ratio` defaults to `8` ratio; valid range: div_ratio >= 1; sets DCO rising-edge division ratio for fb_clk.
- `cppll_timer_ref.f_center` defaults to `800000000.0` Hz; valid range: f_center > 0; sets DCO frequency at common-mode control.
- `cppll_timer_ref.kvco_hz_per_v` defaults to `350000000.0` Hz/V; valid range: kvco_hz_per_v > 0; sets DCO frequency sensitivity to vctrl_mon.
- `cppll_timer_ref.f_min` defaults to `300000000.0` Hz; valid range: f_min > 0 and f_min <= f_max; sets lower DCO frequency clamp.
- `cppll_timer_ref.f_max` defaults to `1600000000.0` Hz; valid range: f_max > 0 and f_max >= f_min; sets upper DCO frequency clamp.
- `cppll_timer_ref.kp` defaults to `8000000.0` loop scale; valid range: kp >= 0; sets proportional phase-error correction scale.
- `cppll_timer_ref.ki` defaults to `120000.0` loop scale; valid range: ki >= 0; sets accumulated phase-error correction scale.
- `cppll_timer_ref.integ_min` defaults to `-0.45` V-equivalent; valid range: integ_min < integ_max; sets lower integral-state bound.
- `cppll_timer_ref.integ_max` defaults to `0.45` V-equivalent; valid range: integ_max > integ_min; sets upper integral-state bound.
- `cppll_timer_ref.vctrl_init` defaults to `0.45` V; valid range: finite real within the intended supply range; sets initial control-voltage monitor.
- `cppll_timer_ref.tedge` defaults to `2e-11` s; valid range: tedge > 0; sets voltage-coded output transition smoothing.
- `cppll_timer_ref.lock_tol` defaults to `4e-10` s; valid range: lock_tol > 0; sets phase-error tolerance for lock streaks.
- `cppll_timer_ref.lock_count_target` defaults to `6` events; valid range: lock_count_target >= 1; sets consecutive in-tolerance events required for lock.
- `ref_step_clk.period_pre` defaults to `2e-08` s; valid range: period_pre > 0; sets reference-clock period before t_switch.
- `ref_step_clk.period_post` defaults to `1.95e-08` s; valid range: period_post > 0; sets reference-clock period after t_switch.
- `ref_step_clk.t_switch` defaults to `2e-06` s; valid range: t_switch >= 0; sets time of the reference-cadence step.
- `ref_step_clk.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets reference-clock transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_REFERENCE_PERIOD_STEP`: restore: The bundled reference-step clock produces the configured period_pre cadence before t_switch and period_post cadence afterwards, with rail-referenced levels. Required traces: `time`, `vdd`, `vss`, `ref_clk`.
- `P_DCO_FREQUENCY_CONTROL`: restore: Dco_clk frequency responds to bounded vctrl_mon around f_center with kvco_hz_per_v sensitivity and remains clamped to f_min through f_max. Required traces: `time`, `dco_clk`, `vctrl_mon`.
- `P_FEEDBACK_DIVISION`: restore: Fb_clk is derived from dco_clk rising-edge activity using div_ratio. Required traces: `time`, `dco_clk`, `fb_clk`.
- `P_BOUNDED_TRACKING_CONTROL`: restore: Reference-versus-feedback phase error updates proportional and bounded integral correction while vctrl_mon remains within the supply rails. Required traces: `time`, `vdd`, `vss`, `ref_clk`, `fb_clk`, `vctrl_mon`.
- `P_INITIAL_LOCK_ACQUISITION`: restore: Stable pre-step tracking asserts lock only after lock_count_target consecutive in-tolerance events. Required traces: `time`, `ref_clk`, `fb_clk`, `lock`.
- `P_DISTURBANCE_UNLOCK`: restore: The reference-period step removes or destabilizes lock qualification while the loop responds to the changed cadence. Required traces: `time`, `ref_clk`, `fb_clk`, `vctrl_mon`, `lock`.
- `P_LATE_REACQUISITION`: restore: After the step, fb_clk tracks the new reference cadence and lock reasserts while vctrl_mon remains rail-bounded. Required traces: `time`, `vdd`, `vss`, `ref_clk`, `fb_clk`, `vctrl_mon`, `lock`.

## Modeling Constraints

- Treat the two source files as one atomic system bundle with no direct module-instantiation dependency between them.
- Use deterministic event-driven oscillator, divider, tracking, and reference-step behavior with timestep guidance.
- Do not hard-code validation windows or use transistor-level, AC/noise, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cppll_timer_ref.va`, `ref_step_clk.va`.
Every supplied `.va` file is editable; do not add or omit files.
