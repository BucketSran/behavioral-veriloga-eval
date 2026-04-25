# Slow Task Report: `/Users/bucketsran/Documents/TsingProject/vaEvas/behavioral-veriloga-eval/results/runtime-profile-G-kimi-isolated-2026-04-26`

## Summary

- tasks: 92
- timed tasks: 89
- total EVAS elapsed sum: 755.8 s
- median: 0.6 s
- p90: 24.9 s
- p95: 43.7 s
- max: 176.9 s
- classes: `{'normal': 75, 'checker_timeout': 12, 'compile_or_preflight': 1, 'large_csv': 2, 'missing_csv': 1, 'many_steps': 1}`

## Slowest Tasks

| task | class | status | total s | tran s | steps | CSV MB | notes |
|---|---|---|---:|---:|---:|---:|---|
| sar_adc_dac_weighted_8b_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 176.900 | 134.316 | 1466234 | 265.7 | generated_include=sar_adc_weighted_8b.va \| generated_include=dac_weighted_8b.va \| generated_include=sh_ideal.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_ |
| pfd_reset_race_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 90.200 | 71.239 | 1186876 | 81.5 | generated_include=pfd_updn.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| inl_dnl_probe | large_csv | PASS | 72.100 | 53.262 | 956315 | 101.2 | gold_dut_include=dac_for_probe.va \| gold_dut_include=inl_dnl_probe.va \| spectre_strict:preflight_pass \| returncode=0 \| sim_correct not required by scoring |
| pfd_deadzone_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 65.800 | 48.196 | 1138675 | 78.2 | generated_include=pfd_updn.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| digital_basics_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 50.700 | 35.424 | 325300 | 58.6 | generated_include=not_gate.va \| generated_include=and_gate.va \| generated_include=or_gate.va \| generated_include=dff_rst.va \| spectre_strict:preflight_pass \| returncode=0 \| b |
| noise_gen_smoke | large_csv | PASS | 43.700 | 27.284 | 1000000 | 68.7 | normalized_tb_save_tokens=2 \| generated_include=noise_gen.va \| spectre_strict:preflight_pass \| returncode=0 \| noise_std=0.0577 max_abs=0.2773 samples=1000001 |
| dac_binary_clk_4b_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 38.500 | 26.683 | 552403 | 44.8 | generated_include=dac_binary_clk_4b.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| dwa_ptr_gen_no_overlap_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 36.700 | 11.338 | 217408 | 95.8 | generated_include=dwa_ptr_gen_no_overlap.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| segmented_dac_glitch_tb | many_steps | PASS | 31.400 | 22.108 | 457670 | 42.8 | gold_dut_include=segmented_dac_glitch_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| sim_correct not required by scoring |
| gain_extraction_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 24.900 | 21.167 | 219910 | 15.1 | generated_include=vin_src.va \| generated_include=lfsr.va \| generated_include=dither_adder.va \| generated_include=gain_amp_fixed.va \| spectre_strict:preflight_pass \| returncode |
| bad_bus_output_loop | checker_timeout | FAIL_SIM_CORRECTNESS | 21.700 | 14.168 | 195932 | 24.1 | spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| multimod_divider_ratio_switch_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 13.200 | 8.916 | 307869 | 17.3 | generated_include=multimod_divider_ratio_switch_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| therm2bin | normal | PASS | 10.900 | 7.657 | 42221 | 11.1 | spectre_strict:preflight_pass \| returncode=0 \| all_bits_high_final_window=True |
| dff_rst_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 7.300 | 4.917 | 115157 | 9.3 | generated_include=dff_rst.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| simultaneous_event_order_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 6.700 | 4.524 | 132461 | 9.1 | normalized_tb_save_tokens=1 \| generated_include=simultaneous_event_order_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| sample_hold_aperture_tb | normal | PASS | 5.800 | 3.813 | 95112 | 7.7 | gold_dut_include=sample_hold_aperture_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| sim_correct not required by scoring |
| nrz_prbs_jitter_tb | normal | PASS | 5.700 | 4.070 | 100238 | 6.9 | gold_dut_include=nrz_prbs_jitter_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| sim_correct not required by scoring |
| final_step_file_metric_smoke | checker_timeout | FAIL_SIM_CORRECTNESS | 5.100 | 3.724 | 138863 | 6.1 | generated_include=final_step_file_metric_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| behavior_eval_timeout>60s |
| adpll_ratio_hop_smoke | normal | FAIL_SIM_CORRECTNESS | 3.700 | 2.553 | 55096 | 4.5 | generated_include=adpll_ratio_hop_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| hop_t=2.550e-06 pre_ratio=4.000 post_ratio=4.000 pre_lock=1.000 post_lock=0.000 vctrl_r |
| transition_branch_target_smoke | normal | FAIL_SIM_CORRECTNESS | 3.600 | 2.247 | 65380 | 5.3 | generated_include=transition_branch_target_ref.va \| spectre_strict:preflight_pass \| returncode=0 \| insufficient_window_samples |
