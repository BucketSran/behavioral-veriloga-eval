# Submission Notes (2026-05-27)

This file describes what should be included in the current benchmark-v2 expansion submission.

## Recommended include

1. `benchmark-v2/tasks/v2_dac_binary_clk_5b_cadence_held_level/**`
2. `benchmark-v2/tasks/v2_dac_binary_clk_6b_refclk_recon_level/**`
3. `benchmark-v2/tasks/v2_dac_binary_clk_3b_code_event_level/**`
4. `benchmark-v2/tasks/v2_adc_dac_ideal_4b_renamed_recon/**`
5. `benchmark-v2/tasks/v2_adc_dac_ideal_4b_param_shift/**`
6. `benchmark-v2/tasks/v2_adc_dac_ideal_4b_negconstraint_strict/**`
7. `benchmark-v2/tasks/v2_ext_hysteresis_cmp_window/**`
8. `benchmark-v2/tasks/v2_ext_hysteresis_cmp_window_offset/**`
9. `benchmark-v2/EXPANSION_REPORT.md`
10. `benchmark-v2/SUBMISSION_NOTES.md`

## Recommended exclude for this PR

1. `results/**` (local run artifacts)
2. `tasks/end-to-end/voltage/v2_dac_binary_clk_5b_rename_negconstraint/**` (earlier onboarding/demo task)
3. `runners/simulate_evas.py` local onboarding edits unless a separate runner-fix PR is intended

## Suggested split strategy

1. PR-A (benchmark-v2 tasks only): include only `benchmark-v2/**`
2. PR-B (optional, later): any runner/checker-framework cleanup in `runners/`

## Status note

Current local validation: all 8 benchmark-v2 tasks pass EVAS + task-local checker.  
Spectre parity and formal promotion status update are pending next step.
