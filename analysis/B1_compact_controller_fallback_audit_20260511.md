# B1 Compact-Controller Fallback Audit - 2026-05-11

Overall verdict: `PASS`

This is a local file-consistency audit of the EVAS result and admission artifacts.

| Check | Status | Detail |
| --- | --- | --- |
| `summary_exists` | `PASS` | results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511/summary.json |
| `admission_exists` | `PASS` | analysis/B1_compact_controller_fallback_admission_20260511.json |
| `row_count_8` | `PASS` | rows=8 |
| `per_task_results_exist` | `PASS` | all present |
| `pass_tasks_match` | `PASS` | summary=['vbm1_edge_detector_dut', 'vbm1_resettable_counter_divider_dut', 'vbm1_vco_phase_integrator_dut'] counted=['vbm1_edge_detector_dut', 'vbm1_resettable_counter_divider_dut', 'vbm1_vco_phase_integrator_dut'] |
| `pass_count_match` | `PASS` | summary=3 counted=3 |
| `repair_round_meta_present_for_nonpass_sources` | `PASS` | all present |
| `compact_trigger_expected_resettable` | `PASS` | compact_rows=['vbm1_resettable_counter_divider_dut'] |
| `official_root_matches_admission` | `PASS` | results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511 |

Scope caveat: this does not audit Spectre equivalence because the current Spectre bridge remains infrastructure-blocked.
