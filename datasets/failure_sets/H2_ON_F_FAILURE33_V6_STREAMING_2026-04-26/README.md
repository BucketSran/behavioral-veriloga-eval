# Current Failure Dataset

Source result root: `results/latest-system-score-condition-H2-on-F-failure33-v6-streaming-kimi-2026-04-26`

## Summary

- Total result count: `33`
- Pass@1 failure count: `23`

### Suspected Layer Counts

| suspected_layer | count |
|---|---:|
| `checker_runtime_or_complex_behavior` | 3 |
| `dut` | 7 |
| `dut_or_complex_system` | 6 |
| `harness_artifact` | 1 |
| `harness_runtime` | 1 |
| `scoring_contract` | 2 |
| `unknown_or_mixed` | 3 |

### Repair Scope Counts

| repair_scope | count |
|---|---:|
| `diagnose-before-repair` | 6 |
| `dut-only` | 7 |
| `harness-first` | 1 |
| `score-axis-alias-only` | 2 |
| `submodule-or-loop-local-repair` | 6 |
| `tb-or-artifact-only` | 1 |

## Failed Tasks

| task | layer | mechanism | signature | scope |
|---|---|---|---|---|
| `adc_dac_ideal_4b_smoke` | `dut` | `adc_dac_code_or_output_coverage` | unique_codes=1 vout_span=0.000 vin_span=0.719 | `dut-only` |
| `adpll_lock_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | not_enough_edges ref=250 fb=0 | `submodule-or-loop-local-repair` |
| `adpll_ratio_hop_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | pre_lock=1.000 post_lock=0.000 vctrl_range_ok=True | `submodule-or-loop-local-repair` |
| `adpll_timer_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | not_enough_edges ref=250 fb=0 | `submodule-or-loop-local-repair` |
| `bbpd_data_edge_alignment_smoke` | `unknown_or_mixed` | `unsupported` | lag_window_updn=8/0 | `diagnose-before-repair` |
| `bg_cal` | `dut` | `adc_dac_code_or_output_coverage` | code_span=15 settled_high=False | `dut-only` |
| `cdac_cal` | `dut` | `adc_dac_code_or_output_coverage` | no vdac activity in ['VDAC_P', 'VDAC_N', 'vdac_p', 'vdac_n'] | `dut-only` |
| `cppll_freq_step_reacquire_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.4875 relock_time=nan vctrl_min=0.500 vctrl_max=0.500 | `submodule-or-loop-local-repair` |
| `cppll_timer` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.1520 fb_jitter_frac=0.0000 lock_time=nan vctrl_min=0.450 vctrl_max=0.855 | `submodule-or-loop-local-repair` |
| `cppll_tracking_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.4002 fb_jitter_frac=0.0001 lock_time=nan vctrl_min=0.500 vctrl_max=0.500 | `submodule-or-loop-local-repair` |
| `cross_sine_precision_smoke` | `dut` | `analog_event_crossing` | count_out_too_low=0.000 | `dut-only` |
| `dac_therm_16b_smoke` | `dut` | `adc_dac_code_or_output_coverage` | max_vout=16.000 | `dut-only` |
| `digital_basics_smoke` | `unknown_or_mixed` | `unsupported` | streaming_checker:invert_match_frac=0.465 | `diagnose-before-repair` |
| `dwa_ptr_gen_smoke` | `harness_artifact` | `missing_generated_testbench` | missing_generated_files:testbench.scs | `tb-or-artifact-only` |
| `dwa_wraparound_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `gain_extraction_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `multimod_divider_ratio_switch_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `multitone` | `harness_runtime` | `csv_missing_or_runtime` | tran.csv missing | `harness-first` |
| `pfd_reset_race_smoke` | `unknown_or_mixed` | `unsupported` | streaming_checker:up_first=0.2000 dn_first=0.0000 up_second=0.8000 dn_second=0.0000 up_pulses_first=10 dn_pulses_second= | `diagnose-before-repair` |
| `sar_adc_dac_weighted_8b_smoke` | `dut` | `adc_dac_code_or_output_coverage` | unique_codes=1 avg_abs_err=0.1881 vout_span=0.000 | `dut-only` |
| `sar_logic_10b` | `scoring_contract` | `scoring_axis_alias` | status_PASS_but_required_axes_use_legacy_names | `score-axis-alias-only` |
| `segmented_dac` | `dut` | `adc_dac_code_or_output_coverage` | diff_range=0.000 | `dut-only` |
| `spectre_port_discipline` | `scoring_contract` | `scoring_axis_alias` | status_PASS_but_required_axes_use_legacy_names | `score-axis-alias-only` |
