# vaBench Release v2 Package Manifest

Date: 2026-06-24

This manifest indexes migrated v2 task forms. It is package metadata,
not fresh EVAS/Spectre certification evidence.

## Summary

| Metric | Value |
| --- | ---: |
| entries | `23` |
| forms | `23` |
| prompt-boundary pass forms | `23` |
| spec-checker map forms | `23` |
| public/private requirement links | `89` |
| score candidate forms | `19` |
| final score-enabled forms | `0` |
| fresh dual-certification pending forms | `23` |

## Claim Boundary

- v2 score claims remain disabled until fresh v2 EVAS/Spectre certification is available.
- Agent prompts must be rendered from `agent_visible_files.json`, not from private evaluator files.
- `task_release_card.json`, `private/*`, and gold assets must never be agent-visible.

## Forms

| Task | Form | Prompt Boundary | Score Enabled | Fresh Dual Pending |
| --- | --- | --- | --- | --- |
| `vbr1_l1_binary_weighted_voltage_dac:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_flash_adc_mini_array:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l2_weighted_sar_adc_dac_loop:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_threshold_comparator:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l1_window_comparator_detector:tb` | `tb-generation` | `pass` | `False` | `True` |
| `vbr1_l2_comparator_measurement_flow:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_acquisition_limited_sample_and_hold:bugfix` | `bugfix` | `pass` | `False` | `True` |
| `vbr1_l1_aperture_delay_track_and_hold:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l1_first_order_lowpass:bugfix` | `bugfix` | `pass` | `False` | `True` |
| `vbr1_l1_slew_rate_limiter:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_amplifier_filter_chain:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_bang_bang_phase_detector:tb` | `tb-generation` | `pass` | `False` | `True` |
| `vbr1_l1_vco_phase_integrator:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l1_gain_trim_controller:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_complete_calibration_loop:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_ptat_ctat_reference_generator:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_ldo_load_step_recovery_flow:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_rf_mixer_downconverter_macro:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_agc_receiver_leveling_loop:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_peak_detector:dut` | `spec-to-va` | `pass` | `False` | `True` |
| `vbr1_l2_gain_extraction_convergence_measurement_flow:e2e` | `end-to-end` | `pass` | `False` | `True` |
| `vbr1_l1_lfsr_prbs_generator:bugfix` | `bugfix` | `pass` | `False` | `True` |
| `vbr1_l2_programmable_stimulus_sequencer:e2e` | `end-to-end` | `pass` | `False` | `True` |
