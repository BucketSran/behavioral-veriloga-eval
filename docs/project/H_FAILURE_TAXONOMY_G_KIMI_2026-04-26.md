# H Failure Taxonomy: `/Users/bucketsran/Documents/TsingProject/vaEvas/behavioral-veriloga-eval/results/runtime-profile-G-kimi-isolated-2026-04-26`

## Counts

| family | count |
|---|---:|
| `counter_cadence/off-by-one` | 2 |
| `onehot/thermometer/no-overlap` | 3 |
| `frame/sequence_alignment` | 2 |
| `PFD/PLL timing_window` | 6 |
| `multi-module interface sanity` | 2 |
| `compile/preflight` | 1 |
| `unsupported/behavior_other` | 25 |
| `pass` | 51 |

## Failed Tasks

| task | H family | reason | status | notes |
|---|---|---|---|---|
| `adpll_lock_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=adpll_va_idtmod.va
spectre_strict:preflight_pass
returncode=0
not_enough_edges ref=250 fb=0 |
| `adpll_ratio_hop_smoke` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | generated_include=adpll_ratio_hop_ref.va
spectre_strict:preflight_pass
returncode=0
hop_t=2.550e-06 pre_ratio=4.000 post_ratio=4.000 pre_lock=1.000 post_lock=0.000 vctrl_range_ok=T |
| `adpll_timer` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
late_edge_ratio=1.140 lock_time=8.070e-08 vctrl_range_ok=True |
| `adpll_timer_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=adpll_timer_ref.va
spectre_strict:preflight_pass
returncode=0
not_enough_edges ref=250 fb=0 |
| `bad_bus_output_loop` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `bbpd_data_edge_alignment_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=bbpd_data_edge_alignment_ref.va
spectre_strict:preflight_pass
returncode=0
too_few_data_edges=0 |
| `bg_cal` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
code_span=15 settled_high=False |
| `bound_step_period_guard_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=bound_step_period_guard_ref.va
spectre_strict:preflight_pass
returncode=0
guard_hi_frac_out_of_range=0.000 |
| `cdac_cal` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
no vdac activity in ['VDAC_P', 'VDAC_N', 'vdac_p', 'vdac_n'] |
| `clk_divider` | `counter_cadence/off-by-one` | `ratio_interval_hist` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
ratio_code=5 in_edges=80 out_edges=8 lock_edges=1 final_lock_high=True period_match=0.000 interval_hist={10: 6} |
| `comparator_hysteresis_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=cmp_hysteresis.va
spectre_strict:preflight_pass
returncode=0
window_fracs pre=0.942 mid=1.000 post=0.000 |
| `cppll_freq_step_reacquire_smoke` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | generated_include=ref_step_clk.va
generated_include=cppll_timer_ref.va
spectre_strict:preflight_pass
returncode=0
pre_lock_edges=0 disturb_lock_low_frac=1.000 post_lock_edges=0 lat |
| `cppll_timer` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
freq_ratio=0.1667 fb_jitter_frac=0.0000 lock_time=nan vctrl_min=0.450 vctrl_max=0.855 |
| `cppll_tracking_smoke` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | generated_include=cppll_timer_ref.va
spectre_strict:preflight_pass
returncode=0
freq_ratio=0.4002 fb_jitter_frac=0.0001 lock_time=nan vctrl_min=0.500 vctrl_max=0.500 |
| `cross_sine_precision_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=cross_sine_precision_ref.va
spectre_strict:preflight_pass
returncode=0
count_out_too_low=0.000 |
| `dac_binary_clk_4b_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=dac_binary_clk_4b.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `dac_therm_16b_smoke` | `onehot/thermometer/no-overlap` | `onehot_overlap_or_pointer` | `FAIL_SIM_CORRECTNESS` | generated_include=dac_therm_16b.va
spectre_strict:preflight_pass
returncode=0
max_ones=16 max_vout=0.000 |
| `dff_rst_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=dff_rst.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `digital_basics_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=not_gate.va
generated_include=and_gate.va
generated_include=or_gate.va
generated_include=dff_rst.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeo |
| `dwa_ptr_gen_no_overlap_smoke` | `onehot/thermometer/no-overlap` | `onehot_overlap_or_pointer` | `FAIL_SIM_CORRECTNESS` | generated_include=dwa_ptr_gen_no_overlap.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `dwa_ptr_gen_smoke` | `onehot/thermometer/no-overlap` | `onehot_overlap_or_pointer` | `FAIL_SIM_CORRECTNESS` | generated_include=v2b_4b.va
generated_include=dwa_ptr_gen.va
spectre_strict:preflight_pass
returncode=0
ptr_unique=1 max_cell_code=0 |
| `dwa_wraparound_smoke` | `compile/preflight` | `compile_or_spectre_strict` | `FAIL_DUT_COMPILE` | generated_include=dwa_wraparound_ref.va
spectre_strict:conditional_transition=dwa_wraparound_ref.va
spectre_strict:dynamic_analog_vector_index=dwa_wraparound_ref.va:33:i:code_i[i], |
| `final_step_file_metric_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=final_step_file_metric_ref.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `flash_adc_3b_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=flash_adc_3b.va
spectre_strict:preflight_pass
returncode=0
too_few_edges=0 |
| `gain_extraction_smoke` | `frame/sequence_alignment` | `frame_or_sequence` | `FAIL_SIM_CORRECTNESS` | generated_include=vin_src.va
generated_include=lfsr.va
generated_include=dither_adder.va
generated_include=gain_amp_fixed.va
spectre_strict:preflight_pass
returncode=0
behavior_eva |
| `gray_counter_4b_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=gray_counter_4b.va
spectre_strict:preflight_pass
returncode=0
gray_property_violated bad_transitions=193 |
| `gray_counter_one_bit_change_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=gray_counter_one_bit_change_ref.va
spectre_strict:preflight_pass
returncode=0
not_enough_clk_edges=0 |
| `multimod_divider` | `counter_cadence/off-by-one` | `base_pre_post_count` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
base=4 pre_count=4 post_count=4 switch_time_ns=40.250 |
| `multimod_divider_ratio_switch_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=multimod_divider_ratio_switch_ref.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `multitone` | `multi-module interface sanity` | `missing_csv_or_missing_generated_artifact` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=1
tran.csv missing |
| `nrz_prbs` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | spectre_strict:preflight_pass
returncode=0
transitions=0 complement_err=0.0041 swing=0.900 |
| `parameter_type_override_smoke` | `PFD/PLL timing_window` | `pulse_phase_lock_window` | `FAIL_SIM_CORRECTNESS` | generated_include=parameter_type_override_ref.va
spectre_strict:preflight_pass
returncode=0
pulses=0 peak=0.000 |
| `pfd_deadzone_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=pfd_updn.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `pfd_reset_race_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=pfd_updn.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `sample_hold_droop_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=sample_hold_droop_ref.va
spectre_strict:preflight_pass
returncode=0
insufficient_high_hold_windows=0 |
| `sar_adc_dac_weighted_8b_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=sar_adc_weighted_8b.va
generated_include=dac_weighted_8b.va
generated_include=sh_ideal.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `segmented_dac` | `multi-module interface sanity` | `missing_csv_or_missing_generated_artifact` | `FAIL_INFRA` | missing_generated_sample |
| `serializer_frame_alignment_smoke` | `frame/sequence_alignment` | `frame_or_sequence` | `FAIL_SIM_CORRECTNESS` | generated_include=serializer_frame_alignment_ref.va
spectre_strict:preflight_pass
returncode=0
clk_edges=13 |
| `simultaneous_event_order_smoke` | `unsupported/behavior_other` | `checker_timeout_no_specific_signature` | `FAIL_SIM_CORRECTNESS` | normalized_tb_save_tokens=1
generated_include=simultaneous_event_order_ref.va
spectre_strict:preflight_pass
returncode=0
behavior_eval_timeout>60s |
| `timer_absolute_grid_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=timer_absolute_grid_ref.va
spectre_strict:preflight_pass
returncode=0
too_few_rising_edges=0 |
| `transition_branch_target_smoke` | `unsupported/behavior_other` | `no_supported_signature` | `FAIL_SIM_CORRECTNESS` | generated_include=transition_branch_target_ref.va
spectre_strict:preflight_pass
returncode=0
insufficient_window_samples |
