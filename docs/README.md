# Documentation Index

Updated: 2026-09-01

## Current Instructions

Read these for new work, in this order:

1. [Agent contract](../AGENTS.md): r53 + EVAS 0.8.7, authority and claim boundaries.
2. [r53 manifest](../benchmark-vabench-release-v4/release/benchmarkv4-r53/MANIFEST.json)
   and [release certification](../benchmark-vabench-release-v4/R53_RELEASE_CERTIFICATION.md).
3. [Campaign runner guide](../benchmark-vabench-release-v4/runners/README.md) and
   [calibration / mini-swe guide](../benchmark-vabench-release-v4/operations/calibration_pilot/README.md).
4. [Current plan](../plans/current-plan.md) and
   [development ownership](../plans/work-ownership.md).
5. [AlphaApollo migration notebook](alphaapollo-migration/README.md),
   including the [feature ledger](alphaapollo-migration/01_功能迁移台账.md).
6. [Repository layout policy](REPO_LAYOUT_POLICY.md).

Start current work with the [active plan](../plans/current-plan.md).
The [overnight engineering audit](alphaapollo-migration/04_夜间工程闭环审计_2026-08-31.md)
is a dated baseline, not the current backlog.
Native campaign/form/retry/result integration and Reasoning/Evolution have
deterministic evidence. Opt-in waveform/docs and reviewed source activation do
not establish model quality or Spectre equivalence. Synthetic training-format
prototypes are retired; their feature notes retain Git recovery points. Actual
training and new domain tools require separate scope, not blanket gap filling.

## Dated Evidence

- [Decision log](../logs/decision-log.md) and
  [verification log](../logs/verification-log.md): exact scope, tests and caveats.
- [Pre-cleanup plan snapshot](../plans/archive/2026-08-30-harness-plan-snapshot.md):
  completed slice detail and original framework transfer matrix, not the active task list.
- [Migration feature notes](alphaapollo-migration/features/README.md):
  preserve each feature's idea-to-code mapping; a later note can supersede an
  earlier status without rewriting that earlier experiment.

## Historical Guides — Not Current Operating Instructions

These remain at their existing paths for provenance and compatibility. Their
commands, counts, missing historical dependencies and judge policies may no
longer apply. Use the current guides above for r53; do not execute old recipes
without an explicit legacy reproduction scope.

| Historical document | Why retained |
| --- | --- |
| [V3 evaluator contract](V3_EVALUATOR_CONTRACT.md) | Prior generation/scoring protocol |
| [V3 source import audit](V3_SOURCE_IMPORT_AUDIT.md) | Source/certification provenance |
| [Task authoring checklist](TASK_AUTHORING_CHECKLIST.md) | Earlier task layout; not valid for sealed r53 |
| [Experiment asset policy](EXPERIMENT_ASSET_POLICY.md) | Earlier directories and retention policy |
| [Validation pipeline](VAEVAS_VALIDATION_PIPELINE.md) | Historical gold/parity/V3 workflow |
| [Labctl Spectre workflow](LABCTL_SPECTRE_WORKFLOW.md) | Historical remote audit operations, not routine scoring |
| [Release taxonomy](VABENCH_RELEASE_TAXONOMY.md) | Earlier release denominator and script input |
| [Top-level positioning](VABENCH_TOPLEVEL_POSITIONING.md) | Earlier paper/release terminology |
| [V4 slimming plan](BENCHMARKV4_REPO_SLIMMING_PLAN.md) | Pre-r53 cleanup proposal, not evidence of completion |

Do not delete release certifications, source audits, feature notebooks or raw
experiment evidence merely because they are old. Branch cleanup is separate:
a branch ref is not a worktree, and merged history is not proof that ignored
files in a worktree are disposable.
