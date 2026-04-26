# Current Failure Dataset

Source result root: `results/latest-system-score-condition-H2-on-F-failure33-v2-kimi-2026-04-26`

## Summary

- Total result count: `33`
- Pass@1 failure count: `27`

### Suspected Layer Counts

| suspected_layer | count |
|---|---:|
| `checker_runtime_or_complex_behavior` | 8 |
| `dut` | 6 |
| `dut_or_complex_system` | 6 |
| `harness_artifact` | 1 |
| `harness_runtime` | 1 |
| `scoring_contract` | 2 |
| `tb_stimulus_or_observable` | 3 |

### Repair Scope Counts

| repair_scope | count |
|---|---:|
| `diagnose-before-repair` | 8 |
| `dut-only` | 6 |
| `harness-first` | 1 |
| `score-axis-alias-only` | 2 |
| `submodule-or-loop-local-repair` | 6 |
| `tb-first-then-dut` | 3 |
| `tb-or-artifact-only` | 1 |

## Failed Tasks

| task | layer | mechanism | signature | scope |
|---|---|---|---|---|
| `adc_dac_ideal_4b_smoke` | `dut` | `adc_dac_code_or_output_coverage` | unique_codes=1 vout_span=0.000 vin_span=0.719 | `dut-only` |
| `adpll_lock_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | not_enough_edges ref=250 fb=0 | `submodule-or-loop-local-repair` |
| `adpll_ratio_hop_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | pre_lock=1.000 post_lock=0.000 vctrl_range_ok=True | `submodule-or-loop-local-repair` |
| `adpll_timer_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | not_enough_edges ref=250 fb=0 | `submodule-or-loop-local-repair` |
| `bad_bus_output_loop` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `bbpd_data_edge_alignment_smoke` | `tb_stimulus_or_observable` | `missing_data_or_reset_window` | too_few_data_edges=0 | `tb-first-then-dut` |
| `bg_cal` | `dut` | `adc_dac_code_or_output_coverage` | code_span=15 settled_high=False | `dut-only` |
| `cdac_cal` | `dut` | `adc_dac_code_or_output_coverage` | no vdac activity in ['VDAC_P', 'VDAC_N', 'vdac_p', 'vdac_n'] | `dut-only` |
| `cppll_freq_step_reacquire_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.4875 relock_time=nan vctrl_min=0.500 vctrl_max=0.500 | `submodule-or-loop-local-repair` |
| `cppll_timer` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.1520 fb_jitter_frac=0.0000 lock_time=nan vctrl_min=0.450 vctrl_max=0.855 | `submodule-or-loop-local-repair` |
| `cppll_tracking_smoke` | `dut_or_complex_system` | `pll_clock_ratio_lock` | freq_ratio=0.4002 fb_jitter_frac=0.0001 lock_time=nan vctrl_min=0.500 vctrl_max=0.500 | `submodule-or-loop-local-repair` |
| `cross_sine_precision_smoke` | `dut` | `analog_event_crossing` | count_out_too_low=0.000 | `dut-only` |
| `dac_therm_16b_smoke` | `dut` | `adc_dac_code_or_output_coverage` | max_vout=16.000 | `dut-only` |
| `digital_basics_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `dwa_ptr_gen_no_overlap_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `dwa_ptr_gen_smoke` | `harness_artifact` | `missing_generated_testbench` | missing_generated_files:testbench.scs | `tb-or-artifact-only` |
| `dwa_wraparound_smoke` | `tb_stimulus_or_observable` | `missing_data_or_reset_window` | insufficient_post_reset_samples count=0 | `tb-first-then-dut` |
| `gain_extraction_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `gray_counter_one_bit_change_smoke` | `tb_stimulus_or_observable` | `missing_clock_or_edge_stimulus` | not_enough_clk_edges=0 | `tb-first-then-dut` |
| `multimod_divider_ratio_switch_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `multitone` | `harness_runtime` | `csv_missing_or_runtime` | tran.csv missing | `harness-first` |
| `pfd_deadzone_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `pfd_reset_race_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `sar_adc_dac_weighted_8b_smoke` | `checker_runtime_or_complex_behavior` | `checker_timeout` | behavior_eval_timeout>53s | `diagnose-before-repair` |
| `sar_logic_10b` | `scoring_contract` | `scoring_axis_alias` | status_PASS_but_required_axes_use_legacy_names | `score-axis-alias-only` |
| `segmented_dac` | `dut` | `adc_dac_code_or_output_coverage` | diff_range=0.000 | `dut-only` |
| `spectre_port_discipline` | `scoring_contract` | `scoring_axis_alias` | status_PASS_but_required_axes_use_legacy_names | `score-axis-alias-only` |
