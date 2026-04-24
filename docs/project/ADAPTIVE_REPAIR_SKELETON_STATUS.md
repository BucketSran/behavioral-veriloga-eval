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
| DWA behavior skeleton through normal adaptive loop | `results/adaptive-dwa-normal-pass-kimi-2026-04-25` | `dwa_wraparound_smoke` reached `PASS` through the normal runner path: `sampled_cycles=8 bad_ptr_rows=0 bad_count_rows=0 wrap_events=3 split_wrap_rows=3`. |
| Sample-hold behavior skeleton | `results/adaptive-samplehold-behavior-kimi-2026-04-25` | `sample_hold_droop_smoke` reached `PASS`: `edges=9 sample_mismatch=0/6 droop_windows=2`. |
| Flash ADC edge + code-coverage skeleton | `results/adaptive-flash-adc-template-kimi-2026-04-25` and `results/adaptive-flash-adc-floorfix-kimi-2026-04-25` | `flash_adc_3b_smoke` progressed from `too_few_edges=0` to `only_1_codes`, then reached `PASS`: `codes=8/8 reversals=0`. |
| Serializer first-clock-pending skeleton | `results/adaptive-serializer-pending-kimi-2026-04-25` | `serializer_8b_smoke` reached `PASS`: `0xA5_serialized_ok mode=edge_only mismatches=0`. |
| SAR/ADC-DAC runtime skeleton | `results/adaptive-sar-adc-hardened-kimi-2026-04-25` | No PASS yet; new candidates still regressed to TB/runtime failure, so this likely needs a structured code/harness template rather than natural-language-only guidance. |
| PFD pulse-window skeleton | `results/adaptive-pfd-pulsewidth-kimi-2026-04-25` | No PASS yet; best candidate remains close but fails with `up_first=0.0975` above the checker upper bound `0.08`. New candidates can regress to compile/timeout. |
| Accumulated skeleton small matrix | `results/adaptive-smallmatrix-kimi-skeleton-v2-2026-04-25` | `9/16` PASS, improved over the previous `5/16` layered-only small matrix. New matrix PASS cases include comparator hysteresis, DWA wraparound, flash ADC, and serializer. |
| Cross-model Qwen small matrix | `results/adaptive-smallmatrix-qwen-skeleton-v2-2026-04-25` plus `results/adaptive-smallmatrix-qwen-skeleton-v2-remaining-2026-04-25` | `3/16` PASS. PASS cases: `adpll_timer_smoke`, `gain_extraction_smoke`, `mux_4to1_smoke`. Several compile failures improved to observable/behavior but did not reach PASS. |

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

### Behavior skeletons with positive PASS evidence

Implemented in `runners/build_repair_prompt.py` and routed through `runners/diagnosis_translation.py`.

- DWA wraparound pointer/count repair: maps `bad_ptr_rows`, `bad_count_rows`, `wrap_events`, and
  `split_wrap_rows` into pointer-update and rotating-window edits.
- Sample-hold droop repair: maps `droop_failures`, `sample_mismatch`, and high-hold windows into
  sample aperture, held state, and monotonic droop edits.
- Flash ADC repair: maps `too_few_edges` to pulse-clock/stimulus repair, then maps `only_N_codes`
  to threshold/code bit-drive repair. A portability rule was added: use Verilog-A `floor(...)`,
  not `$floor(...)`.
- Serializer repair: maps `bit_mismatch` to bit order and first-clock phase repair. The current
  successful skeleton latches on LOAD, marks `load_pending`, outputs the MSB on the first post-LOAD
  CLK, and shifts only on subsequent CLK edges.

## Current Limitations

- The observable and post-reset skeletons mostly improve failure-surface progress; final Pass@1 appears only after a targeted behavior skeleton is available.
- DWA wraparound and sample-hold droop now have positive single-task PASS evidence.
- Flash ADC and serializer now also have positive single-task PASS evidence.
- Behavior repair remains the next bottleneck for SAR/ADC-DAC, PFD/BBPD, and PLL-like tasks.
- Long DWA prompts are slow because the model has to regenerate many files and long bus wiring.
- SAR/ADC-DAC and PFD show that natural-language repair policies are sometimes too soft; these may
  need structured code skeletons or verifier-harness templates.
- Small-matrix reproducibility depends on the round-0 anchor. For example, sample-hold passed in a
  targeted single-task run but did not pass in the `16`-task matrix when started from the older matrix
  round-1 anchor.

## Latest Small-Matrix Result

Run: `results/adaptive-smallmatrix-kimi-skeleton-v2-2026-04-25`

Setup:

- Model: `kimi-k2.5`
- Tasks: `16`
- Max repair rounds: `2`
- Policy: `--layered-only-repair`
- EVAS only, no Spectre conclusion run
- Initial result root: `results/adaptive-layered-only-smallmatrix-kimi-2026-04-25/round1`

Outcome:

- PASS: `9/16`
- Previous comparable layered-only result: `5/16`
- Net improvement: `+4` PASS on this small matrix

PASS tasks:

- `adc_dac_ideal_4b_smoke`
- `comparator_hysteresis_smoke`
- `dac_binary_clk_4b_smoke`
- `dwa_ptr_gen_no_overlap_smoke`
- `dwa_wraparound_smoke`
- `flash_adc_3b_smoke`
- `gray_counter_4b_smoke`
- `mux_4to1_smoke`
- `serializer_8b_smoke`

Remaining failures:

- PLL-like timing/ratio: `adpll_timer_smoke`, `cppll_tracking_smoke`
- Observable/runtime harness: `dwa_ptr_gen_smoke`, `gain_extraction_smoke`, `sar_adc_dac_weighted_8b_smoke`
- Pulse-window behavior: `pfd_reset_race_smoke`
- Anchor-sensitive sample/hold behavior: `sample_hold_droop_smoke`

## Cross-Model Qwen Probe

Runs:

- Main partial run: `results/adaptive-smallmatrix-qwen-skeleton-v2-2026-04-25`
- Remaining-task run: `results/adaptive-smallmatrix-qwen-skeleton-v2-remaining-2026-04-25`

Outcome:

- PASS: `3/16`
- PASS tasks: `adpll_timer_smoke`, `gain_extraction_smoke`, `mux_4to1_smoke`
- The PFD second repair round became a long-tail run and was manually stopped; the recorded PFD
  conclusion uses the completed first-round result.

Interpretation:

- The same repair skeletons do transfer partially across models, but Qwen starts with many more
  compile-layer failures than Kimi on this small matrix.
- Qwen did solve `adpll_timer_smoke`, which Kimi did not solve in the Kimi matrix. This suggests
  the limitation is not simply "Qwen is worse"; the two models have different failure profiles.
- Qwen repeatedly made useful layer progress without reaching PASS, for example compile-to-observable
  on DWA/SAR-like cases and observable-to-behavior on PFD-like cases.
- Qwen-specific next work should emphasize stricter compile skeletons and structured testbench
  templates before behavior-level repair.

Update after the first DWA behavior probe:

- A remaining DWA wraparound failure was traced to the behavior-layer harness freeze policy.
- The loop preserved the model-generated `dwa_code_step_ref` helper, but the verifier harness expects
  the benchmark helper/stimulus module.
- Fixing the freeze policy so that only protected DUT modules are preserved, while verifier helper
  modules are copied back from gold, converted the repaired DWA candidate to PASS.
- This is a method-level finding: behavior-only repair must freeze the verifier harness and helper
  stimulus modules, not only the `.scs` file.

## Recommended Next Work

1. For remaining SAR/ADC-DAC and PFD failures, decide whether to add structured code skeletons rather
   than more natural-language guidance.
2. Add a better anchor-selection rule for matrix runs so tasks can start from `best` when available,
   not only from a fixed `round1` root.
3. Add Qwen-oriented compile repair hardening for dynamic vector indexing, conditional transition,
   colon-instance save syntax, and invalid testbench control statements.
4. Re-run the same small validation cases after each skeleton, using failure-surface progress plus PASS
   as the acceptance metric.
5. Only after anchor-selection cleanup and one more small-matrix confirmation, decide whether to promote the method
   to the full 92-task EVAS-only experiment.

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
