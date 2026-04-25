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
| Full92 Kimi A-G overnight matrix | `results/evas-scoring-condition-{A..G}-kimi-k2.5-full86-2026-04-25-overnight-kimi` | Best condition is F: `53/92` PASS (`0.5761`), improving over B checker baseline `43/92` (`0.4674`) by `+10` tasks. |
| Full92 Qwen A-F overnight matrix | `results/evas-scoring-condition-{A..F}-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen` | Best clean condition is D: `29/92` PASS (`0.3152`), improving over B checker baseline `24/92` (`0.2609`) by `+5` tasks. G was rate-limit contaminated. |
| Strict public-contract validation subset | `results/contract-validation-condition-{A,B}-kimi-k2.5-2026-04-25` | On 12 hard contract-sensitive tasks, A remained `2/12`; B remained `2/12`, but DUT compile failures dropped from old B `4` to new B `2`. Stricter contract improves evaluability, but does not by itself solve behavior repair. |
| Reset-hold + clocked-settling F probe | `results/f-repair-settling-gray-final-v2-kimi-2026-04-25` | `gray_counter_4b_smoke` reached `PASS` through normal F: baseline `FAIL_DUT_COMPILE` -> round1 `FAIL_SIM_CORRECTNESS` -> round2 `PASS` with `unique_codes=16 bad_transitions=0`. |
| Standard F latest-policy hard small matrix | `results/f-smallmatrix-kimi-latest-policy-strict-2026-04-25` | `4/16` PASS. This matches old full92 F on the same subset but underperforms adaptive layered-only `9/16`, showing that skeleton text alone is weaker than explicit layer freezing/routing. |
| Main F runner with layered-only routing | `results/f-layered-smallmatrix-kimi-strict-2026-04-25` | `5/16` PASS. This improves standard F by one task on the hard subset and proves the main F runner can apply layer freezing/routing, but it still trails the standalone adaptive layered-only result (`9/16`). |
| Standalone adaptive v3 latest trajectory | `results/adaptive-smallmatrix-kimi-skeleton-v3-2026-04-25` | `6/16` PASS. This run showed that a newer repair trajectory can forget earlier successful candidates, so single-path repair is not monotonic. |
| Standalone adaptive v4 continuation | `results/adaptive-smallmatrix-kimi-skeleton-v4-continue-2026-04-25` | `2/10` PASS on v3 failures: `cppll_tracking_smoke` and `sample_hold_droop_smoke`. This supports behavior-layer patience greater than one retry. |
| Standalone adaptive v5 anchor guard | `results/adaptive-smallmatrix-kimi-skeleton-v5-anchor-guard-2026-04-25` | `1/7` PASS on targeted failures: `serializer_8b_smoke`. More importantly, it confirmed that failed/regressed candidates should not become the next repair anchor. |
| Standalone adaptive v6 candidate memory | `results/adaptive-smallmatrix-kimi-skeleton-v6-memory-2026-04-25` | `11/16` PASS. The runner selected the best EVAS-verified round-0 candidate from v2/v3/v4/v5 roots, then repaired only non-PASS tasks. This is the best current Hard16 method-development result. |
| Standalone adaptive v7 structural skeletons | `results/adaptive-smallmatrix-kimi-skeleton-v7-structural-2026-04-25` | `1/5` PASS on the remaining hard failures. `dwa_ptr_gen_smoke` reached PASS after multi-module interface/harness sanity guidance. |
| Standalone adaptive v8 runtime-interface routing | `results/adaptive-smallmatrix-kimi-skeleton-v8-runtime-interface-2026-04-25` | No additional PASS, but `sar_adc_dac_weighted_8b_smoke` progressed from runtime artifact loss (`tran.csv missing`) to checker-visible behavior failure (`unique_codes=1`, `vout_span=0.000`). |
| Standalone adaptive v10 memory summary | `results/adaptive-smallmatrix-kimi-skeleton-v10-memory-summary-2026-04-25` | `12/16` PASS after merging v6/v7/v8/v9 best candidates. This is the best current Hard16 method-development result. |

## What Changed Conceptually

- The repair loop now preserves useful tied-score progress. A candidate that moves from "CSV missing" to
  "behavior metric visible" is kept even if the coarse weighted score remains `0.6667`.
- Observable repair is now treated as a generic layer rather than a task-specific prompt trick.
- Post-reset sample-window repair is now treated as a generic layer before behavior repair.
- Reset release persistence and clocked-output settling are now treated as generic layers before
  deeper behavior rewrites.
- Non-improving candidates are no longer allowed to become the next repair anchor. The loop keeps
  repairing from the best EVAS-ranked candidate, which prevents one bad rewrite from compounding.
- Candidate memory is now part of the experimental standalone adaptive loop. If prior EVAS-verified
  roots exist, the runner can select the best round-0 candidate before spending new LLM calls.
- Complex systems now receive a local-validation skeleton keyed to public task modules/signals.
  For SAR ADC/DAC it checks `sh_ideal`, ADC code generation, DAC decode, and top-level code path.
  For ADPLL it checks reference edges, DCO scheduling, feedback divider edges, and lock/control coupling.
- Multi-module runtime failures now receive an interface/harness sanity skeleton, and `tran.csv missing`
  / `returncode=1` is routed to `runtime_interface` instead of observable-only repair. This avoids
  freezing broken DUT module declarations when the DUT/TB interface is jointly inconsistent.
- PFD/PLL timing-window failures now receive a timing-window skeleton that distinguishes waveform-window
  construction from generic behavior repair.
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

### `reset_hold_contract_template`

Implemented in `runners/build_repair_prompt.py`.

This skeleton is injected when the candidate has reset-window symptoms or when the current testbench
contains a reset pulse that deasserts only temporarily and then reasserts before `tran stop`.

The main generic rule is:

- active-low reset sources such as `rstb`/`rst_n`/`rst_ni` must remain high after release,
- active-high reset sources must remain low after release,
- finite-width pulse sources are unsafe for reset release unless the deasserted level lasts beyond
  the full checking window,
- PWL reset release is preferred for smoke tests.

Evidence: in `gray_counter_4b_smoke`, the repair loop changed the reset source from a finite pulse
to a PWL that remains deasserted through the full `2us` transient.

### `clocked_output_settle_template`

Implemented in `runners/build_repair_prompt.py`.

This skeleton is injected for clocked digital behavior mismatches such as `bad_transitions`,
`q_mismatch`, `qb_mismatch`, `bit_mismatch`, or `sample_mismatch`.

The main generic rule is:

- if discrete state behavior is already plausible, do not immediately rewrite the algorithm,
- first ensure `transition()` outputs settle before the checker samples after a clock edge,
- when a module exposes `tedge`/`tr`/`tf`, prefer a testbench instance override such as
  `XDUT (...) module_name tedge=10p` rather than changing the public default parameter,
- if the same mismatch metric stalls across rounds, the transition-parameter override becomes a
  mandatory next edit instead of another cosmetic rewrite.

Evidence: in `gray_counter_4b_smoke`, the round1 candidate had the correct Gray sequence but EVAS
read sampled values below the checker threshold because `1.8V` outputs with `100p` transition had
not settled at the sample point. Round2 added `tedge=10p` in the DUT instance and reached `PASS`.

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
- Reset-hold plus clocked-output settling now has positive normal-F evidence on `gray_counter_4b_smoke`.
- Standard F with latest skeletons did not improve the 16-task hard subset aggregate over old F (`4/16` vs `4/16`).
- Main F now has an optional `--layered-only-repair` path. It improves the hard subset from `4/16` to `5/16`,
  but the stronger result remains standalone adaptive layered-only repair (`9/16`).
- The standalone adaptive loop now has anchor guarding and candidate-memory warm start. These mechanics
  should later be migrated carefully into main F/G after a clean ablation, because v6 is a method-development
  result rather than a formal A/B/C/D/E/F/G condition.
- Behavior repair remains the next bottleneck for SAR/ADC-DAC, PFD/BBPD, and PLL-like tasks.
- The remaining Hard16 failures after v10 are `adpll_timer_smoke`, `gain_extraction_smoke`,
  `pfd_reset_race_smoke`, and `sar_adc_dac_weighted_8b_smoke`.
- `dwa_ptr_gen_smoke` reached PASS in v7, validating the multi-module interface/harness sanity skeleton
  for at least one previously `tran.csv missing` case.
- `sar_adc_dac_weighted_8b_smoke` did not PASS, but v8 converted it from runtime artifact loss to
  behavior-level metrics. The next skeleton should target the sampled-code-to-bit-to-DAC path directly.
- `gain_extraction_smoke` and `pfd_reset_race_smoke` still regress under natural-language repair.
  They likely need structured code/harness templates rather than broader prose guidance.
- Long DWA prompts are slow because the model has to regenerate many files and long bus wiring.
- SAR/ADC-DAC and PFD show that natural-language repair policies are sometimes too soft; these may
  need structured code skeletons or verifier-harness templates.
- Small-matrix reproducibility depends on the round-0 anchor. For example, sample-hold passed in a
  targeted single-task run but did not pass in the `16`-task matrix when started from the older matrix
  round-1 anchor.

## Full92 Kimi Matrix Snapshot

Run date: `2026-04-25`

Local result roots:

- `results/evas-scoring-condition-A-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-B-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-C-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-D-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-E-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-F-kimi-k2.5-full86-2026-04-25-overnight-kimi`
- `results/evas-scoring-condition-G-kimi-k2.5-full86-2026-04-25-overnight-kimi`

Outcome:

| Condition | Pass | Pass@1 | Main interpretation |
| --- | ---: | ---: | --- |
| A | `35/92` | `0.3804` | Raw prompt baseline. |
| B | `43/92` | `0.4674` | Checker contract alone is a strong baseline improvement. |
| C | `37/92` | `0.4022` | Skill alone does not reliably improve Kimi and can degrade end-to-end behavior. |
| D | `46/92` | `0.5000` | One-round EVAS repair gives a small but real gain over B. |
| E | `45/92` | `0.4891` | Adding skill to one-round repair is slightly worse than D. |
| F | `53/92` | `0.5761` | Three-round EVAS repair with baseline-pass reuse is the best current full92 result. |
| G | `51/92` | `0.5543` | Three-round + skill remains positive but underperforms F. |

Important deltas:

- B to F gains `11` tasks: `adc_dac_ideal_4b_smoke`, `clk_burst_gen_smoke`, `clk_div_smoke`, `clk_divider`, `comparator_offset_search_smoke`, `comparator_smoke`, `cross_interval_163p333_smoke`, `ramp_gen_smoke`, `sample_hold_droop_smoke`, `serializer_8b_smoke`, `strongarm_reset_priority_bug`.
- B to F loses `1` task: `pfd_deadzone_smoke`.
- F to G loses `2` tasks: `clk_divider`, `sample_hold_droop_smoke`.
- G adds no new PASS over F in this run, suggesting current skill content is not yet a net-positive repair add-on for Kimi full92.

Infrastructure findings from this run:

- EVAS simulation timeout alone is insufficient. A task can finish `evas simulate` but hang in Python-side CSV/checker evaluation. `runners/simulate_evas.py` now wraps behavior evaluation in a child-process watchdog so a pathological CSV becomes `behavior_eval_timeout` instead of blocking the matrix.
- Missing generated samples must count as failures. `runners/score.py` now records `missing_generated_sample` as `FAIL_INFRA` so all matrix rows use the same denominator.
- Repair scoring should reuse existing B EVAS results when possible. The overnight D/E/F/G run manually reused the completed B result root as the inner feedback source to avoid repeated baseline scoring.

Next repair-policy implication:

- Multi-round repair already keeps the EVAS best-so-far candidate and early-stops on PASS. The next policy improvement should therefore target wasted calls after repeated no-progress rounds, model-specific compile-stability templates, and provider-specific concurrency/rate-limit controls.
- Hierarchy must be contract-driven rather than size-driven. A large ADC-like task that exposes one analog input and one digital/analog output can be a single behavioral module; a task that explicitly asks for ADC/DAC/SAR/sample-hold subblocks should emit separate modules and preserve independently meaningful block contracts during repair.

## Full92 Qwen Matrix Snapshot

Run date: `2026-04-25`

Local result roots:

- `results/evas-scoring-condition-A-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-B-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-C-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-D-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-E-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-F-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`
- `results/evas-scoring-condition-G-qwen3-max-2026-01-23-full86-2026-04-25-overnight-qwen`

Outcome:

| Condition | Pass | Pass@1 | Main interpretation |
| --- | ---: | ---: | --- |
| A | `25/92` | `0.2717` | Raw prompt baseline. |
| B | `24/92` | `0.2609` | Checker contract does not help qwen in this run. |
| C | `25/92` | `0.2717` | Checker + skill roughly returns to A. |
| D | `29/92` | `0.3152` | One-round EVAS repair is the best clean qwen condition. |
| E | `26/92` | `0.2826` | Skill weakens one-round repair relative to D. |
| F | `28/92` | `0.3043` | Three rounds do not improve over one round for qwen. |
| G | `25/92` | `0.2717` | Rate-limit contaminated; not a clean comparison point. |

Qwen-specific interpretation:

- Qwen has many more DUT/TB compile failures than Kimi, especially in end-to-end tasks. This makes behavior-level EVAS feedback less actionable because many candidates never reach stable CSV observability.
- EVAS repair still helps qwen: D improves B by `+5` PASS tasks. However, multi-round repair does not amplify the gain the way it does for Kimi.
- The current skill text is not a reliable repair add-on for qwen; it likely needs to be narrowed into stricter compile-stability and Spectre-friendly syntax rules.
- G hit provider-side rate limits even with sequential retry after the 8-worker run saturated the API. `runners/run_model_assisted_loop.py` now retries transient API failures with exponential backoff, but this run should still treat G as contaminated because many samples were generated before the retry fix and during an exhausted rate window.

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
