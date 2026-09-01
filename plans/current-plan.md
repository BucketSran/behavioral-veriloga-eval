# vaEVAS Current Plan

Updated: 2026-09-01. This is the single active queue, not an execution history.
The [agent contract](../AGENTS.md) defines authority; the
[verification log](../logs/verification-log.md) records exact tests and CI status.

## Goal and fixed baseline

Maintain a reproducible evaluation chain:
r53 task → isolated generation/feedback → trajectory → submission freeze →
EVAS 0.8.7 trusted replay → verified result/claim evidence.
Improve the harness only where failures or measured experiment needs justify it.

- Keep sealed r53 (400 families / 1,200 tasks / 2,000 faults) and EVAS 0.8.7 fixed.
- Keep legacy mini-swe as the default and a separate differential baseline.
- Public validation may guide the same episode or a declared Evolution round.
  Final-test evidence never becomes model feedback or shared memory.
- No paid rerun, training, new corpus, evaluator change or private-project import
  is authorized by a maintenance plan. Only BucketSran origin is writable.

## Implemented surfaces to maintain

| Surface | Current scope / evidence boundary |
| --- | --- |
| Native harness | Shared controller/environment/tool/state/trajectory, all three forms and matched arms; native-mini-swe and Reasoning are opt-in |
| Recovery and budgets | Fresh-attempt recovery, native/Evolution batch resume, complete failure/cost denominators; no partial-conversation or score-driven retry |
| Evolution | Separate named condition; isolated branches, sealed round-barrier candidate/public feedback, one selected final submission; not pooled with baseline |
| Public tools | Optional reviewed docs and candidate-bound waveform feedback are wired into native/Evolution and combined acceptance; not default tools |
| Corpus | Four authorized general veriloga-skills files pinned at `7c5d3f03a162ee8131103e9551eee842424360bb`; local ignored text, committed provenance; Cadence absent and omitted |
| Evidence/results | Private capture, safe export, record/claim ledgers, comparison readers and optional read-only Inspect logs; no second judge |
| Diagnostics | Adversarial Docker checks, opt-in phase timing and fixed scripted workloads; not proof of model quality, comprehensive anti-hack protection or production speedup |

Code and per-feature evidence: [migration ledger](../docs/alphaapollo-migration/01_功能迁移台账.md).
Corpus activation: [reviewed source scope](veriloga-corpus-activation.md).
These are implemented capabilities, not a to-do list to rebuild.

## Latest completed maintenance slice

[Conservative mainline cleanup](mainline-scope-cleanup.md) is implemented and verified:

1. Retired the two synthetic-only training modules and their exclusive tests.
   Recovery links and historical evidence remain; real trajectory capture/safe
   export is unchanged.
2. Consolidated current status here and documented existing entrypoint tiers.
   Dated feature notes/audits remain; no new wrapper or dependency was added.
3. Retained regressions and independent review pass. Focused commits, publication
   status and explicit skips are recorded in the verification log.

No implementation remains open in this slice; the next study is a separate decision.

## Active study: evidence before more features

The next evidence slice is now preregistered as
[a differential and incremental study](real-model-differential-and-incremental-study.md):
first the family001 six-cell legacy/native workflow comparison, then a separate
family001 DUT 2×2 native-Reasoning/Evolution × baseline/RAG-waveform diagnostic.
The implementation and free Docker gates are complete. A paid launch remains
blocked until the user supplies an exact aggregate fee cap and the path to an
external owner-only DeepSeek credential file.

Before execution, freshly review model/service identity, dated provider profile,
rates/decoding and fee authority; freeze task roster, budget and information
surfaces. The stopped DeepSeek pilot is immutable and grants no new spending.
Combined success checks integration. The new explicit baseline permits matched
single-task contrasts, but does not identify RAG versus waveform individually;
that would require a later RAG-only/waveform-only ablation justified by these
first observations.

Remaining evidence gaps, not missing core wiring:

- Real-model quality, genuine heterogeneous-provider behavior and tool utility
  have not been established by scripted smoke tests. Real-corpus combined
  scoring/quality is not established by source/retrieval checks alone.
- Installed Agentic/No-EVAS examples differ; document/control information
  surfaces before attributing a workflow delta purely to EVAS execution.
- Bash diagnostic markers are forgeable and are not global trusted EVAS-process
  metering. Isolated public-tool receipts and final replay have separate authority.
- EVAS 0.8.7's known v4-102 dynamic-array limitation remains documented, not
  silently repaired in r53 or used to justify an unrelated evaluator upgrade.
- Performance measurements are small and host/order-sensitive; they do not
  establish optimal concurrency. CPU/RAM and provider throttling are unmeasured.
- Inspect export has no whole-Evolution-batch/retry aggregation or paired-delta
  visualization; add these only for a concrete analysis need.

## Deferred rather than mandatory backlog

- SFT/RL, real training-data export, split/reward/trainer design: separate project
  scope. AA-VAE-059/062 were synthetic-format prototypes, now retired.
- New read/edit/math/RAG tools, expanded corpora and learned retrieval: require
  a concrete observed failure and source/ablation contract first.
- Inspect scheduling migration, another scheduler or generic orchestration layer:
  require measured benefit over existing execution and recovery.
- Spectre parity: conditional on EVAS changes or an explicitly named protocol;
  not a routine development step.

## Where to start and where history lives

- [Runner guide](../benchmark-vabench-release-v4/runners/README.md):
  default / opt-in / diagnostic entrypoint map.
- [Calibration reference](../benchmark-vabench-release-v4/operations/calibration_pilot/README.md):
  commands, protocol-specific budgets and constraints.
- [Migration notebook](../docs/alphaapollo-migration/README.md) and
  [single-task case study](../docs/alphaapollo-migration/05_单任务代码与轨迹案例_2026-08-31.md):
  ideas, code maps and trace interpretation.
- [Decision log](../logs/decision-log.md) and
  [work ownership](work-ownership.md): dated decisions and sole integration owner.
- [Pre-cleanup plan at 5d2a39fe0d](https://github.com/BucketSran/behavioral-veriloga-eval/blob/5d2a39fe0dde076654e362716456b1a8cedc1547/plans/current-plan.md)
  and [earlier design snapshot](archive/2026-08-30-harness-plan-snapshot.md):
  historical phases, completed work and old gaps, not the active queue.
