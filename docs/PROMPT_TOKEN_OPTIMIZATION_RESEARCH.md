# Prompt Token Optimization Research Note

**Date**: 2026-05-05

This note tracks a follow-up optimization axis for vaEVAS: reducing prompt input
tokens without changing the public ADFGI semantics. It is not part of the
current mainline A/D/F/G/I result table until a compressed-prompt row is
separately validated.

## Motivation

The MiMo diagnostic run showed that prompt input length is not the only cost or
failure driver: hidden reasoning tokens can consume the output budget and leave
empty final content. Therefore prompt compression and thinking-mode control are
separate variables:

| Variable | What it affects | Protocol implication |
| --- | --- | --- |
| Thinking/reasoning mode | Output budget, no-code rate, latency, hidden reasoning cost | Must be controlled or explicitly labeled in model comparisons. |
| Prompt input length | Input cost, latency, attention density, long-context robustness | Can be optimized later through a separate compressed-prompt ablation. |

## Initial Literature Map

| Work | Main idea | Result signal | Relevance to vaEVAS |
| --- | --- | --- | --- |
| [LLMLingua](https://arxiv.org/abs/2310.05736) | Coarse-to-fine prompt compression with budget control and token-level filtering. | Reports large compression ratios with limited quality loss across reasoning, ICL, summarization, and conversation tasks. | Useful as a baseline compressor for verbose rule/guidance segments, but unsafe for exact module/port/numeric contract text unless protected. |
| [LongLLMLingua](https://arxiv.org/abs/2310.06839) | Long-context compression that improves key-information density and mitigates position bias. | Reports lower cost/latency and better long-context behavior on QA-style settings. | Relevant when G/I mechanism cards or repair history make prompts long; suggests keeping key constraints near the model's effective attention path. |
| [LLMLingua-2](https://arxiv.org/abs/2403.12968) | Task-agnostic extractive compression via data distillation and token classification. | Focuses on faithful prompt compression rather than free-form summarization. | Attractive for an offline "compressible segment only" pipeline, if exact public contract spans are locked. |
| [Prompt Compression for Large Language Models: A Survey](https://aclanthology.org/2025.naacl-long.368/) | Taxonomy of hard/soft, extractive/abstractive, retrieval-aware, and model-aware prompt compression. | Frames prompt compression as a context-management problem rather than a single heuristic. | Good survey backbone for paper related work and for designing a clean ablation matrix. |
| [Less is More: DocString Compression in Code Generation](https://arxiv.org/abs/2410.22793) | Code-generation-specific docstring compression. | Reports that generic prompt compression may only save about 10% before code quality drops, while ShortenDoc reaches roughly 25-40% with preserved quality. | Important caution: vaEVAS prompts are code/spec-like, so aggressive natural-language compression may damage exact behavior. |
| [CODEPROMPTZIP](https://arxiv.org/abs/2502.14925) | Code-specific prompt compression for RAG coding tasks using type-aware priorities and copy behavior. | Improves coding-task performance over entropy/distillation baselines under compressed contexts. | Relevant for bugfix and repair prompts containing generated code, compiler notes, and snippets. Identifier/literal preservation is the key idea to borrow. |
| [Stingy Context](https://arxiv.org/abs/2601.19929) | Hierarchical code-context compression for auto-coding workflows. | Reports high compression of repository context while preserving task fidelity. | Useful inspiration for future repository/skill-context packaging, but it is newer and should be treated as exploratory until independently useful for vaEVAS. |

## vaEVAS-Specific Compression Principles

1. Keep exact public contracts lossless: module names, port names/order,
   observable column names, numeric thresholds, time windows, and include names.
2. Compress only low-risk explanatory material first: duplicated output
   discipline, verbose Spectre rule prose, repeated mechanism scaffolds.
3. Prefer segment-aware compression over whole-prompt compression. Whole-prompt
   compression can delete the tiny tokens that matter most to a simulator.
4. Preserve identifiers and literals in code-containing prompts. For bugfix or
   repair contexts, use code-aware compression or no compression.
5. Measure behavior, not only tokens. A prompt is better only if it reduces cost
   without increasing no-code, compile failures, EVAS/Spectre mismatch, or
   behavior regressions.

## Candidate Optimization Tracks

| Track | Description | Expected benefit | Risk |
| --- | --- | --- | --- |
| `D-compact-rules` | Replace the full public Spectre rules with a short hard-ban card. | Lower input tokens and sharper compile constraints. | Missing a rare Spectre incompatibility rule. |
| `task-form-adaptive` | Use different minimal prompt templates for `bugfix`, `dut-only`, `end-to-end`, and `tb-generation`. | Avoid forcing every task to carry irrelevant output contracts. | Template drift if rows are not versioned. |
| `rule-card-retrieval` | Retrieve only the top-k public compile/syntax cards triggered by prompt/family/preflight priors. | Scales better as skill catalogs grow. | Retrieval miss can cause compile regressions. |
| `mechanism-card-budget` | Cap G/I mechanism and functional-IR payloads by card count and character budget. | Prevents G/I from becoming prompt-heavy. | Too little mechanism detail can reduce behavior pass rate. |
| `code-aware-repair-compression` | Compress repair history and compiler logs while preserving identifiers/literals. | Lower F/C/G repair cost. | Over-compression can hide the actual compiler error. |

## Minimal Experimental Plan

Run a small pre-mainline ablation before any 143-task compressed prompt run:

| Stage | Tasks | Conditions | Gate |
| --- | --- | --- | --- |
| Smoke | 3 tasks: one no-code-prone, one compile-prone, one behavior-prone | `D-full` vs `D-compact-rules`; for MiMo also compare thinking-disabled/low | Code blocks extracted, no obvious compile regression. |
| Pilot | 12-16 balanced tasks across slices and task forms | Add `task-form-adaptive` | Input tokens reduced by at least 20% without lower pass count. |
| Audit | Same pilot plus EVAS/Spectre paired audit on changed outcomes | Best compact row vs full prompt | EVAS/Spectre pass/fail mismatch stays zero. |
| Promotion | Full 143 only after pilot passes | Frozen compact prompt version | Report as separate row, not silently replacing A/D/F/G/I. |

## Reporting Columns

Compressed-prompt experiments must include the normal ADFGI columns plus:

| Column | Meaning |
| --- | --- |
| `prompt_version` | Exact prompt template/rule-card version. |
| `prompt_chars` / `prompt_tokens` | Input size before API call. |
| `compression_ratio` | Full-prompt input tokens divided by compressed input tokens. |
| `reasoning_mode` | Provider thinking/reasoning setting. |
| `reasoning_tokens` | Hidden reasoning tokens when reported by the provider. |
| `no_code_rate` | Fraction of tasks with no extractable code blocks. |
| `EVAS/Spectre parity` | Targeted parity result for changed or high-risk tasks. |
