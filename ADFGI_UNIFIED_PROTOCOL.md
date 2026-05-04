# ADFGI Unified Protocol

**Date**: 2026-05-01

This document freezes the mainline vaEVAS ADFGI experiment vocabulary for
`benchmark-balanced`. It supersedes ad-hoc condition names in historical run
directories when building the current paper table.

## Scope

The current mainline benchmark is `benchmark-balanced`:

| Slice | Count | Description |
| --- | ---: | --- |
| `original92` | 92 | Original 92 benchmark tasks, represented in the balanced benchmark schema. |
| `completion92` | 35 | Task-form completion set derived from the original 92 benchmark. |
| `supplement` | 16 | Four new circuit families represented in structured task forms. |
| **Total** | **143** | Mainline balanced benchmark size. |

All ADFGI rows must use the same benchmark, validator, accounting, and reporting
format. Non-strict EVAS/fixed-stage-lite results are retired from the mainline
because they can pass candidates that real Spectre would reject.

## Shared Evaluation Contract

| Field | Unified requirement |
| --- | --- |
| Benchmark | `benchmark-balanced`, full 143 tasks for main table. |
| Required slices | Report full 143, plus `original92`, `completion92`, and `supplement`. |
| Task-form breakdown | Report `bugfix`, `dut-only/spec-to-va`, `end-to-end`, and `tb-generation`. |
| Model label | Record the exact model name in run metadata and tables, e.g. `kimi-k2.5`. |
| Model thinking mode | Cross-model comparisons must explicitly record and, when supported, control the provider reasoning/thinking mode. Examples: `thinking=disabled`, `reasoning_effort=low`, `default/provider-unknown`, or `none` for deterministic no-new-LLM rows. |
| Generation accounting | Record input tokens, output tokens, hidden reasoning tokens when the API reports them, cached input tokens when available, total tokens, per-task elapsed time, and total API elapsed time. |
| Per-group cost columns | Every reported slice or task type must include average tokens per task and average API time per task. |
| Validator | Use **spectre-strict EVAS**: Spectre-aligned preflight, then EVAS simulation, then checker. |
| Result status | Main pass metric is spectre-strict EVAS `PASS / total`; also report failure categories and axis rates when available. |
| Retry policy | One-shot unless the condition definition explicitly includes repair. Artifact retry must not be mixed into A/D one-shot rows. |
| Compile-guarded rows | A row that claims compile closure must report `FAIL_DUT_COMPILE`, `FAIL_TB_COMPILE`, and compile-pass rate explicitly. |
| Archival runs | Historical `full92`, partial, pilot, or non-fixed-stage runs may be cited only as archival diagnostics, not as current ADFGI mainline results. |

## Model Thinking / Reasoning Control

Model comparisons are valid only when the generation mode is part of the
experimental condition. Some OpenAI-compatible reasoning models can spend most
or all of their output budget on hidden reasoning tokens before emitting final
code. That behavior changes both cost and artifact extraction probability, so it
must not be silently mixed with ordinary code-generation mode.

| Case | Protocol |
| --- | --- |
| Same model, same ADFGI condition | Keep `temperature`, `max_tokens`, `top_p`, endpoint, and thinking/reasoning controls fixed. |
| Different AI models | Prefer the closest common mode: code-only final answer, no visible reasoning, and provider reasoning disabled or set to the lowest supported effort. If a provider cannot disable reasoning, label the row as `default/provider-unknown` and do not treat it as directly equivalent to a controlled row. |
| Deterministic no-new-LLM rows (`C-PLUS`, `C-SKILLPLUS`, `C-ULTRA`) | Record `reasoning_mode=none` for the local fixer layer and inherit the source candidate's model/thinking mode in the manifest. |
| Repair-loop rows | Record the thinking mode for every LLM repair call; do not mix default-thinking and thinking-disabled repair rounds in one row. |

For Xiaomi MiMo runs, the runner supports generic provider knobs through
`MIMO_EXTRA_BODY_JSON`, plus convenience environment variables
`MIMO_THINKING_TYPE` and `MIMO_REASONING_EFFORT`. The exact accepted values are
provider-specific and must be smoke-tested before a full 143 run.

## Prompt Input Optimization Track

Prompt input size is a follow-up optimization axis, not a replacement for the
current ADFGI definitions. Any compressed prompt row must preserve the public
task contract exactly: module names, port names/order, required waveform
columns, numeric constants, and Spectre-strict compatibility rules that affect
compile/simulation behavior.

The intended route is a segment-aware compression study:

| Segment | Compression policy |
| --- | --- |
| Public task contract, interfaces, observables, numeric thresholds | Lossless; do not paraphrase or token-drop. |
| Public Spectre/Verilog-A compatibility rules | Compress into a short hard-ban card, then ablate against the full rule set. |
| Generic output discipline | Compress aggressively; keep code-fence and file-order requirements. |
| Mechanism/skill guidance | Retrieve only task-relevant cards and cap top-k/character budget. |
| Buggy source or candidate repair context | Use code-aware compression only if identifiers, literals, and module signatures are preserved. |

Candidate methods and literature are tracked in
`docs/PROMPT_TOKEN_OPTIMIZATION_RESEARCH.md`. A compressed-prompt result must
report the same pass/failure metrics as ADFGI plus `prompt_chars`,
`prompt_tokens`, `reasoning_tokens`, no-code rate, and EVAS/Spectre parity on a
small audit slice before it can be promoted.

## Unified ADFGI Conditions

| Condition | Definition | Current balanced status |
| --- | --- | --- |
| `A` | `prompt-only`; one-shot generation; no checker, no skill, no repair. | Rerun complete: `31/143` under spectre-strict EVAS after parity fixes. |
| `D` | `spectre-strict-v3` public-rule prompting; one-shot generation; no repair. | Rerun complete: `68/143` under spectre-strict EVAS after parity fixes; corrected Spectre audit is `68/143` with `143/143` pass/fail parity. |
| `F` | `D` plus EVAS loop / repair. | Rerun complete: `70/143` under spectre-strict EVAS after parity fixes. |
| `C` | `D` plus LLM-based compile-first closure; no mechanism guidance and no behavior repair. The loop uses public prompt/spec, current candidate files, validator compile/runtime/observable notes, and same-task short repair history. | Rerun complete after parity fixes: `75/143`; residual compile failures are `18/143`. |
| `C-SKILL` | `D` plus LLM-based compile-first closure with public compile-skill guidance injected into compile repair prompts; no mechanism guidance and no behavior repair. | Diagnostic rerun complete: `78/143`. After strict-front-end parity fixes, targeted EVAS+Spectre audit on the 35 D residual compile/interface failures gives EVAS `11/35`, Spectre `11/35`, pass mismatch `0/35`. |
| `C-PLUS` / `C-SKILLPLUS` | `C` plus compile-skill routed deterministic local compile guards applied only to C residual compile/interface failures; no new LLM calls, no mechanism guidance, and no behavior repair. Skills are selected from public validator notes through `runners/compile_skills/registry.json`; fixer and judge-only actions are recorded in the manifest. | Skillized rerun complete under the current validator: `80/143`; residual compile failures are `8/143`. Targeted EVAS+Spectre audit on the earlier 17 C residual compile failures gives pass mismatch `0/17`. This is a compile-skill ablation, not an official G row. |
| `C-ULTRA(full)` | `C` plus compile-skill routed deterministic local fixers with per-action EVAS quick accept/reject and batch fallback transaction for coupled safe fixes; no new LLM calls, no mechanism guidance, and no behavior repair. | Full ULTRA rerun complete: `81/143`; residual compile failures are `7/143`. Targeted EVAS+Spectre audit on the 18 C residual compile/interface failures after parity fixes gives EVAS `6/18`, Spectre `6/18`, pass mismatch `0/18`. This remains the conservative Spectre-audited maintained compile-skill ablation. |
| `C-ULTRA-ADVANCED` | `C-ULTRA(full)` plus advanced public compile skills for sourced port-role repair, missing testbench generation, and dynamic scatter/index materialization; no new LLM calls and no mechanism guidance. | Strict-EVAS result: `83/143`. R6 targeted EVAS+Spectre audit on the 7 advanced residual tasks after adding the backslash module-header guard gives EVAS `2/7`, Spectre `2/7`, pass mismatch `0/7`, and matching failure taxonomy (`FAIL_SIM_CORRECTNESS=4`, `FAIL_DUT_COMPILE=1`). Both advanced PASS deltas are Spectre-confirmed; the remaining compile failure is `completion92_calibration_bugfix`, which requires wrong-function regeneration for missing `v2b_4b`. |
| `G` | Circuit-mechanism guidance plus hard compile guard / compile closure. Mechanism-card retrieval must use only `prompt.md`, public port/observable text, event clues, and public functional labels; it must not use `task_id`, `task_name`, directory names, source task ids, gold code, or checker internals for routing. The accepted candidate for each task must pass Spectre-strict preflight and EVAS compile before behavior scoring. Compile repair may use compiler/preflight diagnostics but must not use gold/checker behavior feedback. | Public-only rerun complete: `G0_public=65/143`; `G_public_v2=76/143` with `FAIL_DUT_COMPILE=2`, `FAIL_TB_COMPILE=5`. This does **not** satisfy the official G compile KPI. The earlier `75/143` and `88/143` runs used the old identity-routed mechanism retrieval and are diagnostic only. |
| `I` | Functional-IR / materialized-IR enhanced condition. | Full balanced rerun complete: `67/143` under spectre-strict EVAS. |

### Official G Acceptance Rule

The balanced mainline keeps only one official `G` experiment. `G` is accepted
only if it materially closes compile failures relative to `F`:

| Target | Requirement |
| --- | --- |
| Primary compile KPI | `FAIL_DUT_COMPILE + FAIL_TB_COMPILE <= 2/143` after final selection. |
| Stretch compile KPI | `FAIL_DUT_COMPILE = 0` and `FAIL_TB_COMPILE = 0`. |
| Feedback boundary | Compile repair can use generated artifacts, public prompt/spec content, Spectre-strict preflight notes, compiler diagnostics, and EVAS compile/runtime notes before checker execution. |
| Forbidden feedback | Compile repair must not use gold implementation code, hidden checker internals, or behavior-checker pass/fail details to repair circuit behavior. |
| Mechanism routing boundary | Mechanism guidance retrieval must be public-functional: prompt text, public ports/observables, event clues, and public functional labels only. Hidden identity fields such as task id, task name, directory name, source task id, source paths, or result/checker artifacts are forbidden. |
| Final scoring | After compile closure, score the final candidates once with the same spectre-strict EVAS validator and report normal `PASS/143`, axis rates, and cost. |

## Current Mainline Results

The maintained A/D/F/G/I pass under the unified validator, after EVAS
source/parser/kernel parity fixes, plus the current compile-guard ablations, is:

| Condition | Model | Validator | PASS / 143 | Pass rate | Result summary |
| --- | --- | --- | ---: | ---: | --- |
| `A` | `kimi-k2.5` | spectre-strict EVAS | `31/143` | 21.7% | `results/adfgi-balanced-spectre-strict-evas-final-2026-05-01-mainline.md` |
| `D` | `kimi-k2.5` | spectre-strict EVAS | `68/143` | 47.6% | `results/adfgi-balanced-spectre-strict-evas-final-2026-05-01-mainline.md` |
| `F` | `kimi-k2.5` | spectre-strict EVAS | `70/143` | 49.0% | `results/adfgi-balanced-spectre-strict-evas-final-2026-05-01-mainline.md` |
| `C` | `kimi-k2.5` | spectre-strict EVAS | `75/143` | 52.4% | `results/adcgi-ablation-C-compile-guarded-v2-2026-05-02.md` |
| `C-SKILL` | `kimi-k2.5` | spectre-strict EVAS | `78/143` | 54.5% | `results/adfgi-ablation-compile-skill-series-2026-05-03.md` |
| `C-SKILLPLUS` | `kimi-k2.5` | spectre-strict EVAS | `80/143` | 55.9% | `results/adfgi-ablation-CSKILLPLUS-compile-skills-2026-05-03.md` |
| `C-ULTRA(full)` | `kimi-k2.5` | spectre-strict EVAS | `81/143` | 56.6% | `results/adfgi-ablation-compile-skill-series-2026-05-03.md` |
| `G public-only` | `kimi-k2.5` | spectre-strict EVAS | `76/143` | 53.1% | `results/balanced-G-public-compile-guarded-v2-kimi-k2.5-spectre-strict-evas-2026-05-02` |
| `I` | `kimi-k2.5` | spectre-strict EVAS | `67/143` | 46.9% | `results/adfgi-balanced-GI-full-2026-05-02.md` |

The public-only G rerun supersedes the older mechanism-routed G numbers for
mainline claims. The old mechanism-only `G` run (`75/143`) and compile-guarded
`G` run (`88/143`) used the previous mechanism retrieval path, which included
task identity in the routing text. They remain useful diagnostics, but they must
not be claimed as public-only mechanism retrieval results.

The strict public-only rerun generated a one-shot mechanism seed
`G0_public=65/143` with `FAIL_DUT_COMPILE=24`, `FAIL_TB_COMPILE=9`, and
`FAIL_SIM_CORRECTNESS=45`. Compile-only closure improved it to
`G_public_v2=76/143` with axis rates `dut_compile=0.9851`, `tb_compile=0.9580`,
`sim_correct=0.4766`, but `FAIL_DUT_COMPILE=2` and `FAIL_TB_COMPILE=5` remain.
Therefore this rerun fails the official G compile KPI and should be treated as
the current public-only diagnostic result, not an accepted main-table G row.

The D row has also been audited with real Spectre through
`virtuoso-bridge-lite`: the historical audit found one apparent mismatch on
`original92_simultaneous_event_order_smoke`. On 2026-05-02 this was resolved as
a benchmark/checker stability issue rather than an EVAS kernel target: the task
now rejects exact-threshold touch / same-time race artifacts and requires a
roughly evenly spaced timer-then-true-cross plateau ramp. A targeted rerun of
the previous D candidate now fails under both EVAS and Spectre; the gold task
passes under both. Because this changed only one task's checker/contract,
targeted revalidation is sufficient: the corrected D audit is EVAS `68/143`,
Spectre `68/143`, pass/fail parity `143/143`, mismatch `0/143`. Targeted A/F
EVAS reruns of this task remain failing, so the A/F EVAS pass counts are
unchanged.

Cost caveat: this F run includes D one-shot tokens plus repair-round tokens, but
the historical repair-round metadata did not record API elapsed time for the 72
repair calls. The adaptive repair runner has been patched to record repair API
elapsed time in future F/G/I repair runs.

## Retired Result Policy

The previous `fixed-stage EVAS` balanced results are not maintained as a second
mainline metric. They may remain on disk as archival diagnostics, but they must
not be used in the ADFGI main table or compared against historical `full92`
results.

Retired examples include:

| Artifact/result family | Status |
| --- | --- |
| Balanced `fixed-stage EVAS` A/D/F summaries, including `56/143`, `77/143`, and `78/143` | Archival only; not a maintained metric. |
| Balanced old `G mechanism-only one-shot` result `75/143` | Diagnostic only; generated with identity-routed mechanism retrieval. |
| Balanced old `G compile-guarded` result `88/143` | Diagnostic only; generated from the old identity-routed mechanism seed. |
| Balanced public-only `G_public_v2` result `76/143` | Current strict rerun, but not accepted as official G because compile KPI fails (`7/143` residual compile failures). |
| Historical `full92` rows | Archival diagnostics unless rerun through the unified spectre-strict EVAS entry. |
| Partial repair or targeted closure runs | Diagnostics only. |

The current maintained path is to rerun A/D/F/G/I through
`validate_benchmark_v2_gold.py --backend evas`, whose EVAS path now includes the
Spectre-aligned strict preflight.

## Mainline Run Status

1. Maintain the completed `A/D/F/G/I` rows only under spectre-strict EVAS.
2. Use `C`, `C-SKILL`, `C-SKILLPLUS`, and `C-ULTRA(full)` as compile-guard /
   compile-skill ablations. They isolate compile closure effects and should not
   be described as mechanism-guided `G`.
3. Treat public-only `G` as not yet accepted for the main table because the
   current rerun leaves `7/143` residual compile failures.
4. Treat the old identity-routed mechanism-only and compile-guarded `G` runs as
   diagnostics, not main paper rows.
5. Treat `I` as a diagnostic functional-IR branch unless a later rerun improves
   the `original92` and `end-to-end` regressions.

## Table Policy

Main paper tables should use only unified ADFGI rows:

| Row | Allowed in main ADFGI table? | Notes |
| --- | --- | --- |
| `A(prompt-only, balanced, spectre-strict EVAS)` | Yes after rerun | Main baseline row. |
| `D(strict-v3, balanced, spectre-strict EVAS)` | Yes after rerun | Public-rule one-shot row. |
| `F/I(balanced, spectre-strict EVAS)` | Yes after rerun | Must follow the shared evaluation contract. |
| `C/C-SKILL/C-SKILLPLUS/C-ULTRA(full) compile-skill ablations` | Ablation table only | Isolates compile-closure, prompt-side compile skill guidance, deterministic skill judge/fixer effects, and EVAS accept/reject; not mechanism-guided G. |
| `G(mechanism-guided compile-guarded balanced, spectre-strict EVAS)` | Yes after accepted rerun | Must satisfy the official G compile KPI. |
| `G mechanism-only one-shot` | No | Diagnostic seed only; compile failures are too high for unified G. |
| Historical `full92` A/D/F/G/I | No | Use as archival or debugging context only. |
| Partial repair or targeted closure runs | No | Use for diagnosis or appendix only if clearly labeled. |
| Non-strict/fixed-stage-lite EVAS | No | Retired to avoid confusion with Spectre-aligned EVAS. |

Required columns for the main slice and task-form breakdown tables:

| Column | Meaning |
| --- | --- |
| `Count` | Number of benchmark tasks in the group. |
| `PASS` | EVAS pass count over `Count`. |
| `Pass Rate` | `PASS / Count`. |
| `Generated` | Number of tasks with extracted generated artifacts. |
| `Avg Tokens / Task` | Total input plus output tokens divided by `Count`. |
| `Avg API Time / Task` | Total API elapsed seconds divided by `Count`. |
| `Notes` | Short caveats such as no-code, pilot-only, or relabeling notes. |
