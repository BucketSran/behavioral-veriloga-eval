# Literature-Guided EVAS Repair Plan

Date: 2026-04-26

This note records the hardware-repair literature basis for the next closed-loop EVAS repair design. The goal is to avoid continuing with ad-hoc prompt tuning and move toward a reusable repair policy backed by prior work in RTL/HDL repair.

## Local PDFs

Downloaded papers are stored under `literature/hardware_repair/`:

| Paper | Local PDF | Why it matters here |
|---|---|---|
| Automatically Improving LLM-based Verilog Generation using EDA Tool Feedback | `2411.11856_autochip_eda_feedback.pdf` | Supports the idea that compiler/simulator feedback can improve HDL generation, but the gain depends strongly on how feedback is used. |
| ARSP: Automated Repair of Verilog Designs via Semantic Partitioning | `2508.16517_arsp_semantic_partitioning.pdf` | Supports semantic partitioning and fragment-level repair instead of whole-module rewriting. |
| HWE-Bench: Benchmarking LLM Agents on Real-World Hardware Bug Repair Tasks | `2604.14709_hwe_bench_hardware_bug_repair.pdf` | Identifies hardware-agent failure modes: localization, hardware semantics, and cross-artifact coordination. |
| CirFix: Automatically Repairing Defects in Hardware Design Code | `asplos22_cirfix_hardware_repair.pdf` | Supports fault localization, patch candidates, simulation fitness, and minimization. |

## Short Evidence Excerpts

Only short excerpts are copied here; use the paraphrased notes for longer writing.

| Paper | Short excerpt | Implication for this project |
|---|---|---|
| AutoChip | "EDA tool feedback proved to be consistently more effective" | EVAS feedback is a valid core mechanism, but feedback alone is not enough. |
| ARSP | "bug signal dilution in long contexts" | Whole-file repair hides the real bug signal; we should reduce repair scope. |
| HWE-Bench | "fault localization, hardware-semantic reasoning, and cross-artifact coordination" | Our failures match known hardware-agent bottlenecks, not only prompt wording issues. |
| CirFix | "Fault localization is critical" | The loop needs localization before asking the model to edit code. |

## Directly Adoptable Method

Adopt an EVAS-guided localized patch repair loop:

1. Generate or reuse the best current candidate.
2. Run EVAS and convert checker notes into an observation signature.
3. Classify the failure by observable evidence, not by task name.
4. Localize a small editable fragment in DUT/TB/harness only when the evidence justifies that layer.
5. Ask the model for a patch intent first: target file, target region, expected metric movement, forbidden edits.
6. Ask for a bounded replacement snippet or diff for that region only.
7. Run static guards before EVAS: module name, ports, file count, save/tran observables, forbidden Spectre-hostile constructs.
8. Run EVAS as the fitness function.
9. Accept only if the candidate passes or improves without regressing a solved layer.
10. Minimize or reject broad rewrites that change unrelated code.

## Why This Is Better Than Current Full Rewrite Repair

Current repair asks the LLM to regenerate too much code from a compact failure message. This causes two recurring failures:

| Current failure | Literature-backed fix |
|---|---|
| A behavior-level candidate regresses to compile/runtime failure after repair. | Use patch-level edits plus static guards. |
| The model sees a metric mismatch but edits unrelated logic. | Use observation-driven fault localization before editing. |
| Large modules dilute the useful bug signal. | Use semantic fragments or submodule/harness-local repair. |
| Multiple artifacts drift out of sync: DUT, TB, save list, tran setup. | Use evidence-gated edit permissions and cross-artifact guards. |

## Proposed Implementation Scope

Start with a constrained prototype rather than changing the full matrix runner:

| Component | Proposed file | Purpose |
|---|---|---|
| Observation policy | `runners/observation_repair_policy.py` | Already exists; reuse failure signatures as repair evidence. |
| Region locator | `runners/patch_region_locator.py` | Find reset blocks, event blocks, timer blocks, output assignments, state updates, and module interfaces. |
| Constrained patch runner | `runners/constrained_patch_repair.py` | Run intent generation, snippet replacement, static guard, EVAS validation, and candidate selection. |
| Static guard | inside constrained runner first | Reject module/header/port/save/tran regressions before expensive EVAS runs. |

## First Experiment

Use a small but representative subset before returning to full92:

| Failure pattern | Example tasks | Expected repair target |
|---|---|---|
| Wrong event cadence or edge count | `clk_divider`, `divider_*` | Counter terminal count, toggle cadence, edge event block. |
| Missing pulse window | `pfd_reset_race_smoke`, `bbpd_*` | Latch/reset sequencing and pulse width logic. |
| Stuck digital sequence | `lfsr_smoke`, `nrz_prbs_*` | Reset release, state update, output mapping. |
| Low code coverage or stuck code path | `sar_adc_dac_weighted_8b_smoke` | Input-to-code path, bit update, DAC output path. |
| Runtime/observable artifact loss | `gain_extraction_smoke`, CSV-missing cases | Interface/harness/save/tran layer, not behavior logic first. |

Success metrics:

| Metric | Why |
|---|---|
| Pass count on the subset | Primary repair effectiveness. |
| Layer regression count | Measures whether patch guard prevents compile/runtime regressions. |
| EVAS runs per accepted improvement | Measures efficiency, central to the paper value. |
| Closeness movement | Shows whether failed repairs move toward the target. |
| Diff size and touched layer | Checks that the method is not overfitting by broad rewriting. |

## Prototype Result: Constrained Patch Repair v1

Implementation:

- Added `runners/constrained_patch_repair.py`.
- The runner builds a normal EVAS-guided repair prompt, appends a localized patch protocol, runs static guards, and accepts the repaired candidate only if its EVAS rank improves.
- For behavior-layer repair, the runner uses the verifier harness but prunes extra gold/helper Verilog-A modules that are not part of the anchor DUT. This prevents cross-artifact confusion where an extra helper `.va` is sorted before the repaired DUT and becomes the staged DUT.

Small probe:

| Task | Previous v13 round-1 candidate | Constrained v1 candidate | Constrained final best | What changed |
|---|---|---|---|---|
| `lfsr_smoke` | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | No behavior improvement. |
| `pfd_reset_race_smoke` | `FAIL_INFRA`, 0.0 | `FAIL_INFRA`, 0.0 | `FAIL_SIM_CORRECTNESS`, 0.6667 | Candidate still timed out, but final best did not regress. |
| `clk_divider` | `FAIL_DUT_COMPILE`, 0.3333 | `FAIL_DUT_COMPILE`, 0.3333 | `FAIL_SIM_CORRECTNESS`, 0.6667 | Candidate still failed compile/runtime, but final best did not regress. |
| `final_step_file_metric_smoke` | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | No behavior/runtime improvement. |
| `sar_adc_dac_weighted_8b_smoke` | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | `FAIL_SIM_CORRECTNESS`, 0.6667 | No code-path improvement. |

Interpretation:

- This prototype improved candidate selection safety, not end-to-end repair success.
- It validates one part of the literature-guided design: do not let a worse repair candidate replace a compile-clean behavior-level anchor.
- It does not yet solve the harder part: generating a truly local, metric-moving patch.
- The remaining gap is that the LLM still receives full-file context and returns full-file code blocks; the runner guards the result, but does not yet mechanically constrain the edit to a selected region.

Next implementation step:

Build a mechanical region-locator and snippet-replacement path. The model should output a patch intent plus replacement for one located region, and the runner should apply that replacement into the anchor file. This is closer to ARSP/CirFix than the current file-level extraction path.

## Prototype Result: Mechanical Region Patch v1

Implementation:

- Added `runners/patch_region_locator.py`.
- Added `runners/mechanical_patch_repair.py`.
- The locator scores event/timer/analog regions using EVAS observation patterns.
- The patch runner copies the best anchor sample, replaces only the selected region, checks module signatures, and runs EVAS.
- Later patch attempts include failed local-patch feedback so the model can avoid repeating the same mechanism.

Probe:

| Task | Selected region | Candidate result | Final best | Interpretation |
|---|---|---|---|---|
| `lfsr_smoke` | `lfsr.va:43-53`, clock event block | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | Scope was local and compile-clean, but output stayed stuck. |
| `pfd_reset_race_smoke` | `pfd_updn.va:35-45`, REF event block | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | Local patch avoided compile regression, but still no valid UP/DN pulse behavior. |
| `clk_divider` | `clk_divider_ref.va:98-125`, counter/toggle event block | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | Local patch avoided the previous undefined-module regression. It changed `out_edges` from 13 to 8 but did not satisfy the ratio metric. |

Three-round `clk_divider` check:

- Round 1/2/3 all remained compile-clean behavior failures.
- The model repeatedly changed the terminal count toward `counter >= div_ratio`, producing `interval_hist={10: 6}` instead of the expected `interval_hist={5: ...}`.
- This shows the runner now constrains *where* the model edits, but the model still needs better metric-to-patch reasoning or multiple candidate search.

Interpretation:

- Mechanical replacement is a real improvement over full-file repair for stability: module names, ports, and testbenches were not rewritten.
- It did not yet improve pass rate on the probe set.
- The next gap is candidate diversity and fitness search: for each localized region, generate several alternative snippets, evaluate all with EVAS, and keep the best metric-moving patch. This is closer to CirFix-style patch variants than single-shot local repair.

## Prototype Result: Multi-Candidate Region Patch v2

Implementation:

- Extended `runners/mechanical_patch_repair.py` with `--candidates-per-round`.
- For each selected region, the runner now generates multiple replacement snippets, applies each snippet to a fresh copy of the same anchor, runs static guard + EVAS, and selects the best candidate by repair rank.
- Added observation-pattern-specific candidate diversity hints. For cadence failures, the prompt now explains that `interval_hist={K: ...}` means the measured input-edge interval between adjacent output rising edges, with target `K == ratio_code`.

Probe:

| Task | Candidates | Best candidate result | Final best | Observation |
|---|---:|---|---|---|
| `clk_divider` | 4 | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | Candidates produced distinct behaviors: `interval_hist={4}`, `{10}`, and one compile-regressed candidate. None reached target `{5}`. |
| `lfsr_smoke` | 4 | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | All candidates remained stuck with `transitions=0 hi_frac=0.000`. |
| `pfd_reset_race_smoke` | 4 | `FAIL_SIM_CORRECTNESS`, 0.6667 | 0.6667 | All candidates remained behavior-timeout or pulse-missing failures. |

Interpretation:

- Multi-candidate search is operational: it can generate and evaluate different local patches without corrupting the anchor candidate.
- It still did not improve pass rate on the three-task probe.
- The most informative case is `clk_divider`: EVAS now exposes a searchable fitness landscape (`interval_hist={4}`, baseline `{6}`, candidates `{10}`), but the current rank treats all compile-clean behavior failures equally. The next repair-policy improvement should add metric-specific closeness scoring so EVAS can select the closest candidate even before a full pass.
- For `lfsr` and `pfd`, region localization may be too narrow: replacing only one event block does not repair the state/output interaction. The next locator should support multi-region patches when EVAS evidence implicates coupled state update plus output assignment or paired REF/DIV event blocks.

## Prototype Result: Closeness Ranking and Multi-Region Patch v3

Implementation:

- Added metric-specific fitness ranking inside `runners/mechanical_patch_repair.py`.
- Cadence closeness parses `ratio_code=N` and `interval_hist={K: ...}` and ranks candidates by smaller `abs(K - N)` after compile/runtime layer rank.
- Sequence closeness parses `transitions` and `hi_frac` so future sequence candidates can be ranked by actual toggling before full pass.
- Pulse closeness parses UP/DN amplitudes and pulse counts when those metrics are available.
- Added `--regions-per-patch` to allow one candidate to replace multiple non-overlapping regions.
- Extended `runners/patch_region_locator.py` to locate output-assignment regions in addition to event/timer/analog blocks.

Probe:

| Task | Setting | Candidate behavior | Result |
|---|---|---|---|
| `clk_divider` | 4 candidates, 1 region | Fitness rank selected the compile-clean candidate with cadence gap 1 and rejected timeout/compile-regressed candidates. | No pass; selected candidate tied the baseline gap (`interval_hist={6}`, target 5). |
| `lfsr_smoke` | 4 candidates, 2 regions (`output_assignment` + clock event) | One candidate moved output from stuck-low to stuck-high (`hi_frac=1.000`), but all kept `transitions=0`. | No pass; multi-region reached relevant output logic but still did not create toggling. |
| `pfd_reset_race_smoke` | 4 candidates, 3 regions (output + REF event + DIV event) | Two candidates hit `conditional_transition` compile restrictions; two remained behavior-timeout/pulse-missing. | No pass; multi-region exposed syntax-guard and pulse-logic gaps. |

Interpretation:

- Closeness ranking is now functioning as a selection mechanism: EVAS metrics can rank local candidates more finely than `weighted_total=0.6667`.
- Multi-region patch is now mechanically supported and can open coupled regions without full-file rewrite.
- The current bottleneck shifted again: candidate generation still does not reliably propose the correct local mechanism. This motivates lightweight, metric-triggered skill cards after the ranking/region machinery is stable, not a full RAG system yet.

## Prototype Result: Metric-Triggered Skill Cards v4

Implementation:

- Added `runners/repair_skill_cards.py`.
- This is a minimal retrieval layer, not a full vector/GraphRAG system.
- Cards are triggered by EVAS observation patterns and metrics:
  - `ratio_code` + `interval_hist` -> divider edge-interval card.
  - `transitions` + `hi_frac` -> state/output sequence card.
  - UP/DN pulse metrics -> paired PFD pulse card.
- `runners/mechanical_patch_repair.py` injects only the top relevant cards into the local patch prompt.

Probe:

| Task | Setting | Result | Observation |
|---|---|---|---|
| `clk_divider` | 4 candidates, 1 region, divider skill card | No pass. Best candidate had `interval_hist={10}`, while baseline was `{6}` with target 5. | The card did not help Kimi generate the right local mechanism in this probe. |

Interpretation:

- Lightweight retrieval is easy to integrate, but it is not automatically beneficial.
- For this probe, the divider card made candidate generation no better and arguably worse than the previous no-card run.
- The priority remains: improve closeness ranking and candidate generation/search mechanics first. Skill-card retrieval should stay optional and ablated, not become the default until it shows measurable benefit.

## Paper-Writing Claim We Can Support

The proposed method can be framed as:

> We use EVAS not merely as a pass/fail oracle, but as a fast fitness function for localized HDL repair. Prior hardware-repair work shows that feedback is useful only when paired with fault localization, semantic scope reduction, and patch-level candidate selection. Our contribution is to adapt this principle to behavioral Verilog-A by converting EVAS CSV/checker observations into bounded repair actions.

This keeps the project thesis intact: EVAS is fast enough to support many small verification-guided repair attempts before moving promising candidates to Spectre.

## Prototype Result: Template-Guided EVAS Search v5

Date: 2026-04-26

Question:

- We already tried localization, multi-candidate LLM patches, and EVAS fitness. Why did that not pass?
- Hypothesis: the previous loop could rank candidates but did not reliably generate the right mechanism. A bounded mechanism-template search should improve candidate coverage.

Implementation:

- Added `runners/template_guided_repair.py`.
- This first probe is deterministic and model-free.
- It starts from the same Kimi condition-A `clk_divider` anchor that failed with `interval_hist={6}` while the target ratio was `5`.
- It generates a small set of generic divider mechanisms:
  - alternating floor/ceil segment lengths
  - alternating ceil/floor segment lengths
  - one-cycle pulse every ratio
  - count-phase variants
- EVAS evaluates every candidate and selects by pass status plus cadence closeness.

Result:

| Candidate | Status | EVAS note | Interpretation |
|---|---|---|---|
| Baseline Kimi A | `FAIL_SIM_CORRECTNESS` | `interval_hist={6: 11}` | Off by one input edge versus target 5. |
| `segment_floor_low_ceil_high` | `FAIL_SIM_CORRECTNESS` | `interval_hist={6: 11}` | Same failure as baseline. |
| `segment_ceil_low_floor_high` | `PASS` | `interval_hist={5: 14}` | Correct odd-ratio phase choice. |
| `pulse_every_ratio_reset_zero` | `PASS` | `interval_hist={5: 13}` | Checker passes, but duty-cycle fidelity is weaker than the segment template. |
| `pulse_every_ratio_reset_one` | `FAIL_SIM_CORRECTNESS` | `interval_hist={4: 17}` | Opposite off-by-one direction. |
| `pulse_every_ratio_minus_one` | `FAIL_SIM_CORRECTNESS` | `interval_hist={4: 17}` | Opposite off-by-one direction. |

Artifacts:

- Runner: `runners/template_guided_repair.py`
- Results: `results/template-guided-clk-divider-kimi-2026-04-26/summary.json`
- Generated candidates: `generated-template-guided-clk-divider-kimi-2026-04-26/`

Interpretation:

- This validates that EVAS can distinguish the correct mechanism quickly once the repair space includes it.
- The earlier LLM-only local patch loop failed because correct candidates were missing from the candidate distribution, not because EVAS/checker could not identify success.
- The useful next direction is not "more free-form LLM patches"; it is metric-triggered, bounded template search.
- For `clk_divider`, the repair space should include counter phase, terminal threshold, reset value, and odd-ratio segment ordering.

Short literature excerpts supporting this direction:

| Source | Short excerpt | How it maps to this project |
|---|---|---|
| GenProg, TSE 2012 | "using existing test suites" | EVAS checker results can serve as the validation oracle for generated variants. |
| SemFix, ICSE 2013 | "layered space of repair expressions" | Our mechanism templates are a layered repair-expression space, not unrestricted code generation. |
| SyGuS, FMCAD 2013 | "syntactic set of candidate implementations" | Divider/PFD/LFSR skeletons should be candidate grammars/templates. |
| CirFix, ASPLOS 2022 | "fitness function tailored to the hardware domain" | EVAS cadence/sequence/pulse metrics are the behavioral Verilog-A fitness function. |
| Long and Rinard, 2016 | "correct patches are sparse" | Explains why random/free LLM patches often miss the correct mechanism. |

## Prototype Result: Template-Guided Small Set v6

Date: 2026-04-26

Purpose:

- Check whether the `clk_divider` success is a one-off or whether bounded mechanism templates help across several clear failure families.
- Keep this smaller than Hard16 because the first goal is interpretability, not benchmark coverage. Hard16 mixes behavior, interface, compile, and large-system failures, so it is better as the second-stage regression set.

Implementation:

- Added `runners/template_guided_smallset.py`.
- The runner starts from Kimi condition-A generated candidates and compares baseline EVAS status with the best template candidate.
- Fast small set:
  - `clk_divider`: cadence/off-by-one family.
  - `lfsr_smoke`: stuck sequence/state-update family.
  - `pfd_updn_smoke`: pulse-window family where baseline was already passing.
  - `multimod_divider`: base/mod cadence switch family.
  - `serializer_frame_alignment_smoke`: frame/load/bit-order alignment family.

Fast-set result:

| Task | Baseline | Best template | Best EVAS note | Interpretation |
|---|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `interval_hist={5: 14}` | Counter phase/odd-ratio segment template repairs the cadence. |
| `lfsr_smoke` | `FAIL_SIM_CORRECTNESS` | `PASS` | `transitions=187 hi_frac=0.479` | Non-zero state-update template repairs stuck-low output. |
| `pfd_updn_smoke` | `PASS` | `PASS` | `up_frac=0.149 dn_frac=0.000 up_pulses=15` | Baseline already passed; immediate-reset template also passes. |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `base=4 pre_count=9 post_count=9` | Base-plus-mod pulse template repairs the switch behavior. |
| `serializer_frame_alignment_smoke` | `FAIL_SIM_CORRECTNESS` | `PASS` | `w0_mm=0 w1_mm=0 mismatch_total=0` | Load-high, MSB-first, one-bit-frame template repairs alignment. |

Aggregate:

- Baseline: `1/5` pass.
- Best template candidate: `5/5` pass.
- Improved tasks: `4/5`.

Important negative evidence:

- `pfd_updn_smoke` delayed-reset template failed with `overlap_too_long=4645`.
- `multimod_divider` reset-to-one count phase failed while reset-to-zero passed.
- `serializer_frame_alignment_smoke` load-low polarity failed with `frame_rises=1`.
- This supports the core idea of EVAS fitness search: templates should propose a bounded set of plausible mechanisms, but EVAS must still reject the wrong variants.

Slow-case observation:

- `pfd_reset_race_smoke` was attempted separately with a 180s budget.
- Its baseline timed out under this runner: `evas_timeout>180s`.
- This case should not block the first-stage method conclusion. It belongs to a follow-up runtime-budget experiment because its testbench uses dense transient settings (`maxstep=10p`, `stop=300n`).

Artifacts:

- Runner: `runners/template_guided_smallset.py`
- Fast-set summary: `results/template-guided-smallset-fast5-kimi-A-2026-04-26/summary.json`
- Fast-set candidates: `generated-template-guided-smallset-fast5-kimi-A-2026-04-26/`
- Slow PFD-reset timeout evidence: `results/template-guided-smallset-pfd-reset-kimi-A-2026-04-26/pfd_reset_race_smoke/baseline/result.json`

Interpretation:

- The method is not just rescuing `clk_divider`; it rescued four distinct condition-A failures across cadence, sequence, multi-modulus cadence, and serializer alignment.
- Hard16 is not too small for the next stage; it is appropriately sized as a regression set after this small-set proof. The right next comparison is `Hard16 old best 12/16` versus `Hard16 + template-guided policy`.
- Before Hard16, the template library should be converted from full-module probes into reusable repair branches that only activate when EVAS notes match the corresponding failure family.

## Prototype Result: G-Anchor Template-Guided Probe v7

Date: 2026-04-26

Question:

- The fast-set v6 used Kimi condition-A anchors. Since condition G is the current strongest closed-loop baseline, does template-guided search still add value on top of G?

Implementation:

- Reused `runners/template_guided_smallset.py`.
- Added `--anchor-root` so the runner can start from `generated-table2-evas-guided-repair-3round-skill/kimi-k2.5`, i.e. the condition-G generated artifacts.
- Tested the G-failed fast candidates:
  - `clk_divider`
  - `multimod_divider`
  - `serializer_frame_alignment_smoke`

Result:

| Task | G-anchor rescore | Best template | EVAS movement | Interpretation |
|---|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `interval_hist={10: 6}` -> `interval_hist={5: 14}` | Template search fixes a case that G still could not repair. |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `pre_count=4 post_count=4` -> `pre_count=9 post_count=9` | Template search fixes base/mod cadence switching. |
| `serializer_frame_alignment_smoke` | `PASS` on rescore | `PASS` | Already `mismatch_total=0` | Historical G result said fail, but current G artifact rescored as pass; do not count as rescued. |

Aggregate on this G-anchor probe:

- Rescored baseline: `1/3` pass.
- Best template candidate: `3/3` pass.
- Strict G-failed rescues: `2` confirmed (`clk_divider`, `multimod_divider`).

Artifacts:

- Summary: `results/template-guided-gfailed-fast3-kimi-G-2026-04-26/summary.json`
- Generated candidates: `generated-template-guided-gfailed-fast3-kimi-G-2026-04-26/`

Interpretation:

- This is the strongest evidence so far that template-guided EVAS search is not merely a replacement for the old loop. It can repair failures left over after condition G.
- The method specifically addresses the candidate-generation gap: G's LLM repair loop had EVAS feedback but did not generate the correct counter/cadence mechanism, while bounded templates did.
- The serializer discrepancy means future comparisons should always rescore the exact anchor artifact before counting a rescue. This avoids inflated claims from stale result metadata.

## Prototype Result: Expanded Condition-H Probe v8

Date: 2026-04-26

Purpose:

- Expand the `G + template-guided EVAS search` probe beyond the first three fast cases.
- Treat this as a prototype condition `H`: start from condition-G artifacts, rescore them, then apply bounded mechanism templates only where useful.

Implementation:

- Extended `runners/template_guided_smallset.py` with additional single-module templates:
  - `dff_rst_smoke`: synchronous reset DFF with complementary output.
  - `clk_div_smoke`: divide-by-4 clock.
  - `gray_counter_4b_smoke`: binary counter to Gray output.
  - `gray_counter_one_bit_change_smoke`: active-high-reset Gray counter.
  - `dac_binary_clk_4b_smoke`: clocked 4-bit binary-weighted DAC.
  - `flash_adc_3b_smoke`: 3-bit clocked flash quantizer.
- Also retained the earlier templates for `clk_divider`, `multimod_divider`, and `serializer_frame_alignment_smoke`.

Expanded H probe result:

| Task | G-anchor rescore | Best H candidate | Best note | Count as H rescue? |
|---|---|---|---|---|
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `interval_hist={5: 14}` | Yes |
| `multimod_divider` | `FAIL_SIM_CORRECTNESS` | `PASS` | `base=4 pre_count=9 post_count=9` | Yes |
| `serializer_frame_alignment_smoke` | `PASS` | `PASS` | `mismatch_total=0` | No, already passes on rescore |
| `dff_rst_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | `q_mismatch=4` | No |
| `clk_div_smoke` | `PASS` | `PASS` | `edge_ratio=4.29` | No, already passes on rescore |
| `gray_counter_4b_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | baseline `bad_transitions=96`; template hit checker timeout | No |
| `gray_counter_one_bit_change_smoke` | `PASS` | `PASS` | `unique_codes=16 bad_transitions=0` | No, already passes on rescore |
| `dac_binary_clk_4b_smoke` | `PASS` | `PASS` | `levels=16 aout_span=0.801` | No, already passes on rescore |
| `flash_adc_3b_smoke` | `FAIL_SIM_CORRECTNESS` | `PASS` | `codes=8/8 reversals=0` | Yes |

Aggregate:

- Re-scored G baseline on this expanded set: `4/9` pass.
- Best H candidate: `7/9` pass.
- Strict H rescues over re-scored G: `3/9`.
- Confirmed rescued tasks: `clk_divider`, `multimod_divider`, `flash_adc_3b_smoke`.

Artifacts:

- Summary: `results/template-guided-H-expanded-kimi-G-2026-04-26/summary.json`
- Generated candidates: `generated-template-guided-H-expanded-kimi-G-2026-04-26/`
- Condition definition update: `docs/project/EXPERIMENT_CONDITIONS_AND_MODEL_MATRIX.md`

Interpretation:

- H is currently the most convincing repair direction: it improves on G by fixing failures that G's free-form repair did not solve.
- The gain is not universal. `dff_rst_smoke` and `gray_counter_4b_smoke` remain unresolved in this prototype, so H needs more precise template matching and/or checker/runtime optimization.
- Several historical G failures now rescore as PASS from the available artifact. Future H evaluation must always use the re-scored artifact as the denominator, not historical metadata alone.
- Next step is to run H on a larger G-failed set with template families gated by EVAS failure signatures, then decide which families are robust enough for full92.

## Prototype Result: Signature-Gated Condition-H Smoke v9

Date: 2026-04-26

Purpose:

- Convert the earlier exploratory template probes into a cleaner H prototype.
- Avoid selecting repair templates by task id.
- Require both EVAS failure evidence and DUT interface evidence before a
  mechanism template can run.

Implementation:

- Added `runners/signature_guided_h.py`.
- The runner starts from a condition-G artifact, re-scores it with EVAS, and
  classifies the failure notes.
- It then checks the generated DUT module/interface signature.
- Only matching `(failure signature, interface signature)` pairs can enable a
  bounded candidate family.
- EVAS ranks candidates and accepts the first passing candidate or the best
  metric-moving candidate.

Initial smoke results:

| Test | Tasks | Eligible | Rescued | Unsupported | Interpretation |
|---|---:|---:|---:|---:|---|
| Report-only gate | 6 | 4 | 0 | 2 | PFD/DWA timeout-only cases were not repaired because the evidence was too weak. |
| Supported H repair | 3 | 3 | 3 | 0 | `clk_divider`, `multimod_divider`, and `flash_adc_3b_smoke` were rescued from G-failed anchors. |

Interpretation:

- The v9 runner preserves the useful v8 finding while reducing overfitting
  risk: repair is now gated by observable signatures rather than task names.
- The conservative unsupported decisions are valuable. They show the method is
  not blindly applying templates when EVAS only reports a checker timeout.
- The next bottleneck is diagnostic quality for timeout-heavy cases. PFD/DWA
  need either safer checker/runtime handling or richer non-streaming notes
  before they should become formal H repair targets.

Follow-up checker finding:

- `dff_rst_smoke` initially looked like an unresolved sampled-latch repair case.
- Direct gold validation showed the gold implementation failed the checker too:
  `q_mismatch=4`.
- The issue was a checker sampling-window bug: sampling `idx + 3` CSV rows after
  a clock edge can mean sampling only about 1.9 ps after the edge, before a
  public `transition(..., 10p)` output has settled.
- `check_dff_rst` now samples by time about 100 ps after the detected clock
  edge. The gold now passes with `q_mismatch=0 qb_mismatch=0`.

Updated H evidence after this checker fix:

| Test | Tasks | Best pass | Strict rescues | Note |
|---|---:|---:|---:|---|
| G-failed report-only sweep | 41 | 10 re-scored G PASS | 0 | 4 tasks eligible for templates; 37 unsupported. |
| Eligible-4 H repair | 4 | 4 | 3 | `clk_divider`, `multimod_divider`, and `flash_adc_3b_smoke` are strict H rescues; `dff_rst_smoke` passes at baseline after checker fix. |
