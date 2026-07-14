# Fractional-N Divider Accumulator Flow Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fracn_pll_timer_ref.va`:
  - Module `fracn_pll_timer_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `ref_clk` (input, electrical)
    - position 3: `fb_clk` (output, electrical)
    - position 4: `dco_clk` (output, electrical)
    - position 5: `vctrl_mon` (output, electrical)
    - position 6: `lock` (output, electrical)

## Public Parameter Contract

- `fracn_pll_timer_ref.div_int` defaults to `8 from [1:inf)`; valid range: finite; overrides div_int.
- `fracn_pll_timer_ref.frac_word` defaults to `3 from [0:inf)`; valid range: finite; overrides frac_word.
- `fracn_pll_timer_ref.acc_modulus` defaults to `8 from [1:inf)`; valid range: finite; overrides acc_modulus.
- `fracn_pll_timer_ref.f_center` defaults to `800.0e6 from (0:inf)`; valid range: finite; overrides f_center.
- `fracn_pll_timer_ref.kvco_hz_per_v` defaults to `350.0e6 from (0:inf)`; valid range: finite; overrides kvco_hz_per_v.
- `fracn_pll_timer_ref.f_min` defaults to `300.0e6 from (0:inf)`; valid range: finite; overrides f_min.
- `fracn_pll_timer_ref.f_max` defaults to `1.6e9 from (0:inf)`; valid range: finite; overrides f_max.
- `fracn_pll_timer_ref.kp` defaults to `8.0e6 from [0:inf)`; valid range: finite; overrides kp.
- `fracn_pll_timer_ref.ki` defaults to `1.2e5 from [0:inf)`; valid range: finite; overrides ki.
- `fracn_pll_timer_ref.integ_min` defaults to `-0.45`; valid range: finite; overrides integ_min.
- `fracn_pll_timer_ref.integ_max` defaults to `0.45`; valid range: finite; overrides integ_max.
- `fracn_pll_timer_ref.vctrl_init` defaults to `0.45`; valid range: finite; overrides vctrl_init.
- `fracn_pll_timer_ref.tedge` defaults to `20p from (0:inf)`; valid range: finite; overrides tedge.
- `fracn_pll_timer_ref.lock_tol` defaults to `0.4e-9 from (0:inf)`; valid range: finite; overrides lock_tol.
- `fracn_pll_timer_ref.lock_count_target` defaults to `6 from [1:inf)`; valid range: finite; overrides lock_count_target.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_USE_REF_CLK_AS_THE_REFERENCE`: restore: Use `ref_clk` as the reference timing input. Required traces: `time`, `VDD`, `VSS`, `ref_clk`, `fb_clk`, `dco_clk`, `vctrl_mon`, `lock`.
- `P_GENERATE_A_BEHAVIORAL_DCO_CLOCK_ON`: restore: Generate a behavioral DCO clock on `dco_clk`. Required traces: `time`, `VDD`, `VSS`, `ref_clk`, `fb_clk`, `dco_clk`, `vctrl_mon`, `lock`.
- `P_GENERATE_FB_CLK_BY_TOGGLING_IT`: restore: Generate `fb_clk` by toggling it after a DCO rising-edge count selected by a Required traces: `time`, `VDD`, `VSS`, `ref_clk`, `fb_clk`, `dco_clk`, `vctrl_mon`, `lock`.
- `P_UPDATE_A_BOUNDED_CONTROL_VOLTAGE_MONITOR`: restore: Update a bounded control-voltage monitor on `vctrl_mon` from the PFD phase Required traces: `time`, `VDD`, `VSS`, `ref_clk`, `fb_clk`, `dco_clk`, `vctrl_mon`, `lock`.
- `P_DRIVE_LOCK_HIGH_AFTER_STABLE_TRACKING`: restore: Drive `lock` high after stable tracking, low or unstable during the Required traces: `time`, `VDD`, `VSS`, `ref_clk`, `fb_clk`, `dco_clk`, `vctrl_mon`, `lock`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fracn_pll_timer_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
