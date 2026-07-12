# ADPLL Ratio Hop Timer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `adpll_ratio_hop_ref.va`:
  - Module `adpll_ratio_hop_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `ref_clk` (input, electrical)
    - position 3: `ratio_ctrl` (input, electrical)
    - position 4: `fb_clk` (output, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `vctrl_mon` (output, electrical)
    - position 7: `lock` (output, electrical)

## Public Parameter Contract

- `adpll_ratio_hop_ref.f_center` defaults to `240000000.0` Hz; valid range: f_center > 0; sets the DCO center frequency near code_center.
- `adpll_ratio_hop_ref.freq_step_hz` defaults to `5000000.0` Hz/code; valid range: freq_step_hz > 0; sets DCO frequency change per control-code step.
- `adpll_ratio_hop_ref.f_min` defaults to `120000000.0` Hz; valid range: f_min > 0 and f_min <= f_max; sets the lower generated-frequency clamp.
- `adpll_ratio_hop_ref.f_max` defaults to `420000000.0` Hz; valid range: f_max > 0 and f_max >= f_min; sets the upper generated-frequency clamp.
- `adpll_ratio_hop_ref.code_min` defaults to `0` code; valid range: code_min >= 0 and code_min <= code_max; sets the minimum loop-control code.
- `adpll_ratio_hop_ref.code_max` defaults to `63` code; valid range: code_max >= 1 and code_max >= code_min; sets the maximum loop-control code.
- `adpll_ratio_hop_ref.code_center` defaults to `32` code; valid range: code_min <= code_center <= code_max; sets the control code corresponding to f_center.
- `adpll_ratio_hop_ref.code_init` defaults to `24` code; valid range: code_min <= code_init <= code_max; sets the initial bounded loop-control code.
- `adpll_ratio_hop_ref.ratio_min` defaults to `2` ratio; valid range: ratio_min >= 1 and ratio_min <= ratio_max; sets the minimum accepted feedback divide ratio.
- `adpll_ratio_hop_ref.ratio_max` defaults to `16` ratio; valid range: ratio_max >= 2 and ratio_max >= ratio_min; sets the maximum accepted feedback divide ratio.
- `adpll_ratio_hop_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets voltage-coded output transition smoothing.
- `adpll_ratio_hop_ref.lock_tol` defaults to `2e-09` s; valid range: lock_tol > 0; sets the timing-error tolerance for lock qualification.
- `adpll_ratio_hop_ref.lock_count_target` defaults to `5` events; valid range: lock_count_target >= 1; sets the required consecutive in-tolerance feedback-event count.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RATIO_REQUEST_CLAMP`: restore: The voltage-coded ratio request rounds V(ratio_ctrl) to the nearest integer with half-step boundaries and then clips the feedback divide ratio to the inclusive ratio_min through ratio_max range, including legal non-default override ranges. Required traces: `time`, `ratio_ctrl`, `vout`, `fb_clk`.
- `P_DCO_FREQUENCY_BOUNDS`: restore: The behavioral DCO on vout remains within the configured f_min and f_max limits. Required traces: `time`, `vout`.
- `P_FEEDBACK_DERIVED_FROM_DCO`: restore: Feedback-clock activity is derived by dividing vout activity by the requested ratio rather than from an independent clock source. Required traces: `time`, `ratio_ctrl`, `vout`, `fb_clk`.
- `P_BOUNDED_CONTROL_MONITOR`: restore: Reference-versus-feedback timing error adjusts a bounded control state represented by rail-referenced vctrl_mon. Required traces: `time`, `vdd`, `vss`, `ref_clk`, `fb_clk`, `vctrl_mon`.
- `P_PRE_HOP_LOCK`: restore: Stable pre-hop tracking produces lock only after lock_count_target consecutive feedback events satisfy lock_tol. Required traces: `time`, `ref_clk`, `fb_clk`, `lock`.
- `P_RATIO_HOP_REACQUISITION`: restore: A changed ratio request causes loss of lock qualification followed by renewed lock after the loop tracks the new feedback cadence. Required traces: `time`, `ratio_ctrl`, `ref_clk`, `fb_clk`, `vctrl_mon`, `lock`.

## Modeling Constraints

- Use a deterministic timing loop whose feedback clock is derived from the generated DCO.
- Use rail-referenced voltage-coded outputs and appropriate oscillator timestep guidance.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `adpll_ratio_hop_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
