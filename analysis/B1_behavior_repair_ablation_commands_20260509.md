# B1 Behavior Repair Ablation Commands - 2026-05-09

Run from `behavioral-veriloga-eval/`.

## Method Note

Current operating mode: use EVAS as the provisional B1 behavior standard while
the Virtuoso/Spectre bridge is unstable.  Keep Spectre commands and result roots
for later comparison, but do not use current `FAIL_INFRA` Spectre runs to rank
or reject candidates.

Prompt-control note: the full adaptive prompt can be 10x-20x larger than the
original B1 task prompt.  See
`analysis/B1_prompt_controller_finding_20260509.md`.  Future B1 controller
experiments should compare injected content and routing policy with a high token
ceiling, rather than treating token size as the primary mechanism.

For Main120 B1 behavior tasks, do not treat `run_adaptive_repair.py`'s internal
round score as the final behavior score.  It still goes through an older
`score.py`/quick simulation path for some tasks.  The authoritative B1 behavior
check is:

1. Run one adaptive round.
2. Materialize `<task>/adaptive_round1` into a clean candidate root as
   `<task>/sample_0`.
3. Run `runners/validate_benchmark_v2_gold.py`, which loads each task's
   `checker.py`.
4. Spectre-audit every EVAS-positive candidate before accepting it.
5. Treat `FAIL_INFRA` Spectre audits as infrastructure-blocked, not as candidate
   rejection.  On 2026-05-09 the `jin` bridge failed both candidate and gold
   Spectre runs with SSH/upload banner timeouts.

## MiMo Full Form-Routed DUT, Fixed Gold-Harness Path

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-full-dut-mimo-mt8192-fixed-20260509 \
  --output-root results/b1-ablation-full-dut-mimo-mt8192-fixed-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --freeze-gold-harness-on-behavior \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## MiMo No-Skill DUT

Use the same command as above, replacing roots and adding `--no-repair-skill`:

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-20260509 \
  --output-root results/b1-ablation-noskill-dut-mimo-mt8192-fixed-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --freeze-gold-harness-on-behavior \
  --no-repair-skill \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## MiMo No-Contract DUT

Use the same command as full DUT, replacing roots and adding
`--disable-contract-diagnosis`:

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-nocontract-dut-mimo-mt8192-fixed-20260509 \
  --output-root results/b1-ablation-nocontract-dut-mimo-mt8192-fixed-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --freeze-gold-harness-on-behavior \
  --disable-contract-diagnosis \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## MiMo No-Skill + No-Contract DUT

This combination was run because the two single ablations improved different
EVAS tasks.  It produced an EVAS positive on `vbm1_edge_detector_dut`, but the
positive failed Spectre.

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-noskill-nocontract-dut-mimo-mt8192-fixed-20260509 \
  --output-root results/b1-ablation-noskill-nocontract-dut-mimo-mt8192-fixed-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --freeze-gold-harness-on-behavior \
  --no-repair-skill \
  --disable-contract-diagnosis \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## MiMo Strict + Retry No-Skill + No-Contract DUT

This is the best B1 DUT smoke so far: EVAS 2/8 and no-code reduced to 1/8.
Use a high token ceiling as a resource budget; compare fixed behavior policies
and injected content rather than treating token size as the core mechanism.

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-20260509 \
  --output-root results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --artifact-retry-max-tokens 8192 \
  --freeze-gold-harness-on-behavior \
  --no-repair-skill \
  --disable-contract-diagnosis \
  --strict-code-output \
  --artifact-retry-on-truncation \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

Aggressive token-ceiling variant:

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt32768-20260509 \
  --output-root results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt32768-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 32768 \
  --artifact-retry-max-tokens 32768 \
  --freeze-gold-harness-on-behavior \
  --no-repair-skill \
  --disable-contract-diagnosis \
  --strict-code-output \
  --artifact-retry-on-truncation \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## MiMo Full Form-Routed TB

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-main120-S2-compile-skill-accept-mimo-v2.5-pro-20260509 \
  --initial-result-root results/main120-S2-maintained-evas-mimo-v2.5-pro-20260509 \
  --generated-root generated-b1-ablation-full-tb-mimo-mt8192-fixed-20260509 \
  --output-root results/b1-ablation-full-tb-mimo-mt8192-fixed-evas-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --workers 2 \
  --timeout-s 180 \
  --quick-maxstep 500p \
  --max-tokens 8192 \
  --freeze-dut-on-behavior \
  --task vbm1_segmented_dac_tb \
  --task vbm1_offset_comparator_tb
```

## Materialize Round 1

Example for a DUT run:

```bash
mkdir -p generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-20260509/mimo-v2.5-pro
while read -r task; do
  src="generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-20260509/mimo-v2.5-pro/$task/adaptive_round1"
  dst="generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-20260509/mimo-v2.5-pro/$task/sample_0"
  rm -rf "$dst"
  mkdir -p "$dst"
  if [ -d "$src" ]; then cp -R "$src"/. "$dst"/; fi
done < tasklists/B1_behavior_repair_dut_smoke_20260509.txt
```

Use the TB tasklist for TB runs:

```bash
done < tasklists/B1_behavior_repair_tb_smoke_20260509.txt
```

## Authoritative EVAS Validation

Always pass the same `--task` list used for the smoke run.  Otherwise the
validator will scan all 120 Main120 tasks and fail on tasks that were not
materialized into the round1 candidate root.

```bash
python3 runners/validate_benchmark_v2_gold.py \
  --backend evas \
  --bench-dir benchmark-vabench-main-v1 \
  --candidate-dir generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-20260509 \
  --model mimo-v2.5-pro \
  --sample-idx 0 \
  --output-dir results/b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-evas-20260509 \
  --timeout-s 180 \
  --max-workers 2 \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

## Spectre Audit For EVAS Positives

Current status: the `jin` Spectre bridge is infrastructure-blocked.  The
classified audit root is:

```text
results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-spectre-jin-classified-20260509
```

Both strict+retry EVAS positives currently return `FAIL_INFRA` with
`spectre_infra_failure=remote_upload_or_ssh_timeout`.
The gold control shows the same infrastructure failure in:

```text
results/b1-spectre-infra-gold-edge-detector-jin-classified-20260509
```

```bash
python3 runners/validate_benchmark_v2_gold.py \
  --backend spectre \
  --bench-dir benchmark-vabench-main-v1 \
  --family b1-noskill-dut-mimo-mt8192-fixed-round1-spectre \
  --candidate-dir generated-b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-20260509 \
  --model mimo-v2.5-pro \
  --sample-idx 0 \
  --output-dir results/b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-spectre-jin-20260509 \
  --timeout-s 180 \
  --max-workers 2 \
  --env /Users/bucketsran/Documents/TsingProject/iccad/virtuoso-bridge-lite/.env \
  --profile jin \
  --task vbm1_vco_phase_integrator_dut
```

## Provider Notes

- Bailian/Kimi attempts are currently blocked by the expired Bailian key.
- MiMo is the active provider path for this smoke wave; the key is stored in
  `.env.table2`.

## Compact-Controller Runner Smoke

Tasklist:

```text
tasklists/B1_compact_controller_smoke_20260509.txt
```

Adaptive repair command:

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_edge_detector_dut \
  --source-generated-dir generated-b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-20260509 \
  --initial-result-root results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-evas-20260509 \
  --generated-root generated-b1-compact-controller-runner-smoke-mimo-mt32768-20260509 \
  --output-root results/b1-compact-controller-runner-smoke-mimo-mt32768-adaptive-20260509 \
  --sample-idx 0 \
  --max-rounds 1 \
  --patience 1 \
  --timeout-s 60 \
  --quick-maxstep 1n \
  --max-tokens 32768 \
  --strict-code-output \
  --artifact-retry-on-truncation \
  --artifact-retry-max-tokens 32768 \
  --compact-controller always \
  --compact-controller-public-spec-mode prompt-only \
  --compact-controller-max-candidate-chars 6000 \
  --no-repair-skill \
  --disable-contract-diagnosis \
  --freeze-gold-harness-on-behavior \
  --env-file .env.table2
```

Authoritative EVAS validation:

```bash
python3 runners/validate_benchmark_v2_gold.py \
  --backend evas \
  --bench-dir benchmark-vabench-main-v1 \
  --task-file tasklists/B1_compact_controller_smoke_20260509.txt \
  --candidate-dir generated-b1-compact-controller-runner-smoke-mimo-mt32768-20260509 \
  --model mimo-v2.5-pro \
  --sample-idx 0 \
  --output-dir results/b1-compact-controller-runner-smoke-mimo-mt32768-evas-20260509 \
  --timeout-s 60
```

Observed official EVAS result: 2/3 pass.  The adaptive quick summary under-
reported `vbm1_resettable_counter_divider_dut`; use the official validation
root for claims.

## Full 8-Task Compact-Controller Fallback

Adaptive repair command:

```bash
python3 runners/run_adaptive_repair.py \
  --model mimo-v2.5-pro \
  --bench-dir benchmark-vabench-main-v1 \
  --source-generated-dir generated-b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-20260509 \
  --initial-result-root results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-evas-20260509 \
  --generated-root generated-b1-compact-controller-fallback-dut-mimo-mt32768-20260511 \
  --output-root results/b1-compact-controller-fallback-dut-mimo-mt32768-adaptive-20260511 \
  --max-rounds 1 \
  --patience 1 \
  --workers 1 \
  --timeout-s 60 \
  --quick-maxstep 1n \
  --max-tokens 32768 \
  --strict-code-output \
  --artifact-retry-on-truncation \
  --artifact-retry-max-tokens 32768 \
  --compact-controller fallback \
  --compact-controller-public-spec-mode prompt-only \
  --compact-controller-max-candidate-chars 6000 \
  --no-repair-skill \
  --disable-contract-diagnosis \
  --freeze-gold-harness-on-behavior \
  --env-file .env.table2 \
  --task vbm1_background_calibration_accumulator_bugfix \
  --task vbm1_cdac_calibration_dut \
  --task vbm1_first_order_lowpass_dut \
  --task vbm1_vco_phase_integrator_dut \
  --task vbm1_edge_detector_dut \
  --task vbm1_resettable_counter_divider_dut \
  --task vbm1_barrel_pointer_window_bugfix \
  --task vbm1_leaky_hold_dut
```

Authoritative EVAS validation:

```bash
python3 runners/validate_benchmark_v2_gold.py \
  --backend evas \
  --bench-dir benchmark-vabench-main-v1 \
  --task-file tasklists/B1_behavior_repair_dut_smoke_20260509.txt \
  --candidate-dir generated-b1-compact-controller-fallback-dut-mimo-mt32768-20260511 \
  --model mimo-v2.5-pro \
  --sample-idx 0 \
  --output-dir results/b1-compact-controller-fallback-dut-mimo-mt32768-evas-20260511 \
  --timeout-s 60 \
  --max-workers 2
```

Observed official EVAS result: 3/8 pass.  Admission table:
`analysis/B1_compact_controller_fallback_admission_20260511.md`.
