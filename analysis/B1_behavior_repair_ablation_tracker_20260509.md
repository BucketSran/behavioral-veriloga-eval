# B1 Behavior Repair Ablation Tracker - 2026-05-09

Current decision: while the Virtuoso/Spectre bridge is unstable, use EVAS as the
provisional B1 behavior standard and defer Spectre comparison.  Spectre
`FAIL_INFRA` rows below should not be used to rank or reject candidates.

| Run ID | Variant | Scope | Backend | Status | Result root | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| B1-R001 | full-form-routed / Kimi | 8 DUT tasks | EVAS | BLOCKED_API | `results/b1-ablation-full-dut-evas-20260509` | Attempted; 8/8 `FAIL_INFRA` due Bailian `invalid_api_key/token expired`. Repair prompts and result JSONs are retained. |
| B1-R002 | full-form-routed / Kimi | 2 TB tasks | EVAS | SKIPPED_AFTER_API_BLOCK | `results/b1-ablation-full-tb-evas-20260509` | Not launched with Kimi after provider block. |
| B1-R003 | no-skill-form-routed / Kimi | 8 DUT tasks | EVAS | SKIPPED_AFTER_API_BLOCK | `results/b1-ablation-noskill-dut-evas-20260509` | Not launched with Kimi after provider block. |
| B1-R004 | no-skill-form-routed / Kimi | 2 TB tasks | EVAS | SKIPPED_AFTER_API_BLOCK | `results/b1-ablation-noskill-tb-evas-20260509` | Not launched with Kimi after provider block. |
| B1-R005 | no-contract-form-routed / Kimi | 8 DUT tasks | EVAS | SKIPPED_AFTER_API_BLOCK | `results/b1-ablation-nocontract-dut-evas-20260509` | Not launched with Kimi after provider block. |
| B1-R006 | no-contract-form-routed / Kimi | 2 TB tasks | EVAS | SKIPPED_AFTER_API_BLOCK | `results/b1-ablation-nocontract-tb-evas-20260509` | Not launched with Kimi after provider block. |
| B1-R007 | no-routing / Kimi | 10 tasks | EVAS | TODO | `results/b1-ablation-norouting-evas-20260509` | Still worth running after a stable provider/model path is chosen. |
| B1-R008 | EVAS-accepted candidate audit | EVAS-positive candidates | Spectre | INFRA_BLOCKED | See Spectre rows below | Spectre audits currently fail at remote upload/SSH banner exchange. Treat them as infra, not candidate rejection. |
| B1-R009 | full-form-routed / MiMo / 4096 | 8 DUT tasks | EVAS | SUPERSEDED | `results/b1-ablation-full-dut-mimo-evas-20260509` | First MiMo attempt before key setup, then superseded by 8192 fixed runs. |
| B1-R010 | full-form-routed / MiMo / 8192 | 8 DUT tasks | EVAS | INVALID_SUPERSEDED | `results/b1-ablation-full-dut-mimo-mt8192-round1-evas-20260509` | Exposed gold-DUT leakage when no candidate DUT existed; retained as bug evidence only. |
| B1-R011 | full-form-routed / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | DONE_EVAS | `results/b1-ablation-full-dut-mimo-mt8192-fixed-round1-evas-20260509` | 0/8 pass. Failure taxonomy: 4 `FAIL_DUT_COMPILE`, 4 `FAIL_SIM_CORRECTNESS`. |
| B1-R012 | no-skill / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-evas-20260509` | 1/8 pass: `vbm1_vco_phase_integrator_dut`. |
| B1-R013 | no-skill positive audit | 1 DUT task | Spectre | SUPERSEDED_INFRA_CLASSIFICATION | `results/b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-spectre-jin-20260509` | Old validator mislabeled remote upload timeout as `FAIL_DUT_COMPILE`; do not treat as candidate rejection. |
| B1-R014 | no-contract / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-ablation-nocontract-dut-mimo-mt8192-fixed-round1-evas-20260509` | 1/8 pass: `vbm1_edge_detector_dut`. |
| B1-R015 | no-contract positive audit | 1 DUT task | Spectre | SUPERSEDED_INFRA_CLASSIFICATION | `results/b1-ablation-nocontract-dut-mimo-mt8192-fixed-round1-spectre-jin-20260509` | Old validator mislabeled remote upload timeout as `FAIL_DUT_COMPILE`; do not treat as candidate rejection. |
| B1-R016 | full-form-routed TB / MiMo / 8192 / fixed | 2 TB tasks | EVAS | DONE_EVAS | `results/b1-ablation-full-tb-mimo-mt8192-fixed-round1-evas-20260509` | 0/2 pass. Failures: one `FAIL_TB_COMPILE`, one `FAIL_SIM_CORRECTNESS`. |
| B1-R017 | no-skill + no-contract / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-ablation-noskill-nocontract-dut-mimo-mt8192-fixed-round1-evas-20260509` | 1/8 pass: `vbm1_edge_detector_dut`. Did not preserve the no-skill VCO positive. |
| B1-R018 | strict code extraction / MiMo / 8192+ | 8 DUT tasks | EVAS | TODO_NEXT | TBD | Target `no_code_extracted`/length failures by requiring a complete `.va` file only. |
| B1-R019 | TB syntax-hardened prompt / MiMo / 8192+ | 2 TB tasks | EVAS | TODO_NEXT | TBD | Target multiline PWL/Spectre source syntax and segmented-DAC correctness. |
| B1-R020 | no-skill + no-contract positive audit | 1 DUT task | Spectre | SUPERSEDED_INFRA_CLASSIFICATION | `results/b1-ablation-noskill-nocontract-dut-mimo-mt8192-fixed-round1-spectre-jin-20260509` | Old validator mislabeled remote upload timeout as `FAIL_DUT_COMPILE`; do not treat as candidate rejection. |
| B1-R021 | Spectre infra gold check | 1 gold task | Spectre | INFRA_CONFIRMED | `results/b1-spectre-infra-gold-edge-detector-jin-classified-20260509` | Gold `vbm1_edge_detector_dut` also failed remote upload/SSH banner exchange and is classified as `FAIL_INFRA`. |
| B1-R022 | strict + retry + no-skill + no-contract / MiMo / 8192 | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-evas-20260509` | 2/8 pass: `vbm1_edge_detector_dut`, `vbm1_vco_phase_integrator_dut`; no-code reduced to 1/8. |
| B1-R023 | strict + retry positive audit | 2 DUT tasks | Spectre | INFRA_BLOCKED | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-spectre-jin-classified-20260509` | 0/2, both `FAIL_INFRA` due remote upload/SSH banner exchange. |
| B1-R024 | strict + retry + no-skill + no-contract / MiMo / 32768 | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE_PARTIAL_GEN | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt32768-round1-evas-20260509` | 2/8 pass. 7/8 tasks generated before `first_order_lowpass` was stopped for a long provider call. `resettable_counter_divider` became runnable behavior failure instead of no-code. |
| B1-R025 | compact-controller targeted first-order / MiMo / 32768 | 1 DUT task | EVAS | DONE_NEGATIVE_BUT_USEFUL | `results/b1-ablation-compact-controller-firstorder-mimo-mt32768-evas-20260509` | 0/1 pass, but prompt shrank 12185 -> 3001 chars and returned complete artifact in 67.744s. Shows controller can reduce latency/artifact instability while behavior still needs mechanism repair. |
| B1-R026 | compact-controller runner mode / MiMo / 32768 | 3 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-compact-controller-runner-smoke-mimo-mt32768-evas-20260509` | 2/3 pass: `vbm1_edge_detector_dut`, `vbm1_resettable_counter_divider_dut`. Prompt chars: first-order 5448, resettable 5252. Resettable improved from compile/no-code surfaces to official EVAS PASS; first-order still fails with `ZeroDivisionError`/`tran.csv missing`. |
| B1-R027 | compact-controller fallback / MiMo / 32768 | 8 DUT tasks | EVAS | DONE_EVAS_POSITIVE | `results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511` | 3/8 pass: `vbm1_edge_detector_dut`, `vbm1_resettable_counter_divider_dut`, `vbm1_vco_phase_integrator_dut`. Admission table: `analysis/B1_compact_controller_fallback_admission_20260511.md`. Only resettable used compact fallback; pure behavior-layer tasks stayed on full prompts and did not improve. |

## Attempt Log

- `2026-05-09`: patched `runners/run_adaptive_repair.py` with `--freeze-dut-on-behavior` so TB-generation behavior repair can preserve DUT files and edit only generated testbenches.
- `2026-05-09`: created source mirror `generated-b1-source-mimo-s2-as-kimi/kimi-k2.5 -> generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509/mimo-v2.5-pro`.
- `2026-05-09`: attempted B1-R001 with `kimi-k2.5`; model calls failed with Bailian authentication error. Output retained in `results/b1-ablation-full-dut-evas-20260509/summary.json`.
- `2026-05-09`: switched to MiMo after the MiMo key was added to `.env.table2`.
- `2026-05-09`: found that the adaptive runner's internal scoring path is not authoritative for Main120 B1 behavior tasks; authoritative checks must materialize `adaptive_round1` and run `runners/validate_benchmark_v2_gold.py`.
- `2026-05-09`: fixed `_freeze_gold_harness` to avoid leaking gold DUT `.va` files into no-code DUT-side candidates.
- `2026-05-09`: ran valid MiMo 8192 DUT/TB smokes and found EVAS positives.
- `2026-05-09`: confirmed Spectre audit is currently infrastructure-blocked because both candidate and gold runs fail remote upload/SSH banner exchange.
- `2026-05-09`: added strict code output and artifact retry to adaptive repair; strict+retry improved no-skill+no-contract DUT smoke from EVAS 1/8 to 2/8 and reduced no-code from 4/8 to 1/8.
- `2026-05-09`: ran aggressive token ceiling test at 32768. Pass count stayed EVAS 2/8, but `vbm1_resettable_counter_divider_dut` moved from missing DUT/no-code to runnable `FAIL_SIM_CORRECTNESS`, confirming token ceiling was a candidate-completeness confounder.
- `2026-05-09`: ran compact-controller targeted first-order experiment. Compact prompt improved generation controllability but did not fix EVAS behavior/runtime failure; finding written to `analysis/B1_prompt_controller_finding_20260509.md`.
- `2026-05-09`: implemented `--compact-controller {off,fallback,always}` in `runners/run_adaptive_repair.py`, added unit tests, and ran a 3-task runner smoke. Official EVAS validation was 2/3. The adaptive quick-check path under-reported `vbm1_resettable_counter_divider_dut`, so Main120 B1 claims must continue to use `validate_benchmark_v2_gold.py` as the authority.
- `2026-05-11`: ran the full 8-task compact-controller fallback smoke. Official EVAS improved from 2/8 to 3/8 by adding `vbm1_resettable_counter_divider_dut`; fallback only triggered on that compile-layer task, while behavior-layer full prompts did not improve. This motivates a two-trigger controller: compact for blockers plus compact mechanism prompts for known behavior families.
