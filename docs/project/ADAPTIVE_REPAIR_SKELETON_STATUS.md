# Adaptive Repair Skeleton Status

Date: 2026-04-25

## Purpose

This document records the compact, tracked conclusions from the local EVAS-only adaptive repair work.
Raw `generated-*`, `results/*/result.json`, `tran.csv`, and temporary artifacts remain local and are not
intended for remote upload.

The current goal is not to tune one benchmark to match a gold implementation. The goal is to make the
EVAS closed loop progressively expose more actionable diagnostics:

1. compile/link failures,
2. observable CSV contract failures,
3. post-reset sample-window failures,
4. behavior-level metric failures,
5. final PASS.

## Current Evidence

| Stage | Local result path | Main outcome |
| --- | --- | --- |
| Baseline small matrix | `results/evas-scoring-contract-audit-smallmatrix-B-kimi-2026-04-25` | `2/16` PASS before adaptive layered repair. |
| Layered only-repair small matrix | `results/adaptive-layered-only-smallmatrix-kimi-2026-04-25` | `5/16` PASS; strict re-score confirmed the 5 quick PASS cases. |
| Template need scan | `results/repair-template-needs-2026-04-25` | Scanned `2356` local `result.json` files; top need was observable scalar CSV aliases across `54` distinct tasks. |
| Observable scalar alias skeleton | `results/adaptive-observable-skeleton-kimi-adc-v2-2026-04-25` | `adc_dac_ideal_4b_smoke`: `missing dout_code or dout_3..0` became `unique_codes=1 vout_span=0.000`. |
| Observable scalar alias skeleton | `results/adaptive-observable-skeleton-kimi-dwa-v3-2026-04-25` | `dwa_wraparound_smoke`: missing scalar columns became `insufficient_post_reset_samples count=0`. |
| Post-reset sample budget skeleton | `results/adaptive-postreset-skeleton-kimi-dwa-2026-04-25` | `dwa_wraparound_smoke`: `insufficient_post_reset_samples count=0` became `sampled_cycles=8 bad_ptr_rows=8 bad_count_rows=7 wrap_events=3 split_wrap_rows=4`. |
| Post-reset sample budget skeleton | `results/adaptive-postreset-skeleton-kimi-sh-2026-04-25` | `sample_hold_droop_smoke`: `too_few_clock_edges=2` became `droop_failures=3 windows=3`. |
| DWA behavior + verifier-helper freeze fix | `results/adaptive-dwa-behavior-freezecheck-kimi-2026-04-25` | Existing repaired DWA DUT plus corrected verifier helper/harness reached `PASS`: `sampled_cycles=8 bad_ptr_rows=0 bad_count_rows=0 wrap_events=3 split_wrap_rows=3`. |

## What Changed Conceptually

- The repair loop now preserves useful tied-score progress. A candidate that moves from "CSV missing" to
  "behavior metric visible" is kept even if the coarse weighted score remains `0.6667`.
- Observable repair is now treated as a generic layer rather than a task-specific prompt trick.
- Post-reset sample-window repair is now treated as a generic layer before behavior repair.
- These changes do not directly inject gold circuit behavior; they make EVAS feedback readable and
  well-sampled so that later behavior repair has a real target.

## Implemented Skeletons

### `observable_scalar_alias_template`

Implemented in `runners/build_repair_prompt.py`.

This skeleton is injected for missing CSV columns and related observable-contract failures. It requires:

- top-level scalar node names matching checker columns,
- direct scalar DUT port wiring,
- one canonical save list,
- no vector CSV headers such as `dout[0]`,
- no instance-qualified save names,
- no `save signal as alias` workaround,
- behavior repair deferred until columns are visible.

### `post_reset_sample_budget_template`

Implemented in `runners/build_repair_prompt.py` and routed through `runners/diagnosis_translation.py`.

This skeleton is injected for too-few-sample and too-few-edge failures. It extracts current testbench facts:

- `tran stop`,
- clock period/delay,
- reset delay or PWL release time,
- estimated post-reset rising edges.

It asks the model to keep the benchmark transient window when possible and instead move reset, clock,
and stimulus timing so enough post-reset samples exist.

## Current Limitations

- The new skeletons improve failure-surface progress, not final Pass@1 yet.
- Behavior repair remains the next bottleneck.
- Long DWA prompts are slow because the model has to regenerate many files and long bus wiring.
- Some existing code changes are still experimental and should be reviewed before a clean commit.

Update after the first DWA behavior probe:

- A remaining DWA wraparound failure was traced to the behavior-layer harness freeze policy.
- The loop preserved the model-generated `dwa_code_step_ref` helper, but the verifier harness expects
  the benchmark helper/stimulus module.
- Fixing the freeze policy so that only protected DUT modules are preserved, while verifier helper
  modules are copied back from gold, converted the repaired DWA candidate to PASS.
- This is a method-level finding: behavior-only repair must freeze the verifier harness and helper
  stimulus modules, not only the `.scs` file.

## Recommended Next Work

1. Implement a behavior-layer DWA skeleton for `bad_ptr_rows`, `bad_count_rows`, `wrap_events`, and
   `split_wrap_rows`.
2. Re-run DWA wraparound through the normal adaptive loop after the verifier-helper freeze fix, not
   just through the direct freeze-check path.
3. Implement a sample-hold behavior skeleton for `droop_failures` and `windows`.
4. Re-run the same small validation cases after each skeleton, using failure-surface progress plus PASS
   as the acceptance metric.
5. Once the small validation cases show real PASS uplift, run the 16-task small matrix again.
6. Only after the small matrix improves, promote the method to the full 92-task EVAS-only experiment.

## Upload Policy

Keep for remote:

- source changes under `runners/`,
- prompt-contract changes under `tasks/`,
- concise summaries under `docs/project/` and `tables/`.

Do not upload:

- `generated-*` raw model outputs,
- `tmp/`,
- `tran.csv`,
- per-task `result.json`,
- bulky local intermediate experiment roots.
