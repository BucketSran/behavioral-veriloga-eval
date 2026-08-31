# Single-task harness case study

2026-08-31. Base: `87c10cb65e4bd90f95ba9d1e07492e862d3ad6b6`.

## Brief and acceptance

The user accepted the first follow-up: inspect one existing free smoke through
code, actions, feedback, candidate changes, trajectory, freeze and final score.
This is a documentation/evidence audit, not a runtime feature or a paid pilot.
The preceding discussion supplies the scope; no additional decision is needed.

Primary KPI: one source-bound event timeline, with actual candidate/freeze/score
joins validated by existing readers and no fabricated model-quality conclusion.
Secondary KPI: explain the five component boundaries and distinguish preexisting
legacy protections from native additions and intentional behavioral differences.
Preserve all frozen r53/EVAS assets, default routing, previous evidence and scores.

## Plan and exact ownership

1. Inspect the public fixture and existing AA-VAE-061 native-mini-swe smoke;
   select one existing artifact directory, without reading gold/checker contents.
2. Reuse the production read-only evidence validator; extract only allowlisted
   identities, event sequence, hashes, counts and final verdict for the notebook.
   No raw private trace, candidate source or hidden checker diagnostics in Git.
3. Map policy/controller/environment/trajectory/final responsibilities to code;
   compare legacy behavior using current source and existing differential tests.
4. Write a Chinese code walkthrough under the migration notebook; link it from
   current navigation. Run focused existing tests, link/diff/secret checks and
   independent read-only review. Commit/push only the bounded documentation slice.

Main alone owns this plan, `plans/work-ownership.md`, `plans/current-plan.md`,
decision/verification logs, the migration README and new
`docs/alphaapollo-migration/05_单任务代码与轨迹案例_2026-08-31.md`.
`case_study_code_map` is read-only code/differential advice;
`case_study_review` independently reviews the final notebook and its code claims.
No delegated writer,
runtime/schema/test changes, new abstraction, corpus, model API call or training.

## Evidence and stop boundary

Selected candidate: existing `overnight-final-integration-01/`
`test_real_waveform_feedback_fr0/waveform-runtime` below the ignored v4 reports
directory. Check its backend/cell identity instead of inferring them from pytest
directory numbering. The smoke uses a synthetic campaign digest and scripted
public stub: it is not a formally scheduled experiment or a model baseline.

If hashes/identity fail validation, report the failure without repairing the
stored evidence or silently substituting another run. Unclear authority or a
required scoring/runtime change ends this documentation slice for review.
Exact commands, outcomes, publication and review go in the existing logs.

## Disposition

Documentation/evidence work completed. The production reader, the notebook's
exact read-only command, source hashes and pre-freeze provider ordering pass;
stored evidence remains unchanged. Focused harness tests: 41 passed / three
real-Docker cases deselected; navigation/CI contract tests: 41 passed.
Independent notebook review found zero required changes. Its verdict is COMMENT
because LSP/AST tools are unavailable; Markdown/link/secret/diff and structured
evidence checks substitute for this documentation-only slice.
Both advisory lanes have returned and have no write assignment. Main owns the
bounded fork publication and its source-specific hosted verification record.
No additional runtime or experiment scope is opened by this completed plan.
