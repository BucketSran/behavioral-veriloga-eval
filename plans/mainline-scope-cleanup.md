# Mainline scope cleanup

Date: 2026-09-01. Base: `5d2a39fe0dde076654e362716456b1a8cedc1547`.

## Brief and scope

Reduce inactive implementation and conflicting status documents, without
changing supported evaluation behavior. The user approved this conservative
cleanup after the feature-value review; it is not a new harness redesign.

Remove only the synthetic SFT/RL prototypes and their exclusive tests:

- `runners/agent_harness/training_export.py`
- `runners/agent_harness/training_trace_adapter.py`
- `tests/test_agent_harness_training_export.py`
- `tests/test_agent_harness_training_trace_adapter.py`

Keep their dated engineering notes with an explicit retirement banner and the
base revision as an exact Git recovery point. No production consumer, package
export, external schema or shared fixture may be removed with them.

Condense `current-plan.md` into the single active queue. Retain historical
audits, feature notes and decision/verification logs; link the pre-cleanup plan
in Git rather than adding another full local snapshot. Update current roadmap,
navigation and stale corpus/training descriptions. Document existing default,
opt-in experiment and diagnostic entrypoints without adding a new dispatcher.

## Frozen boundaries

Keep r53, EVAS 0.8.7, legacy default, Reasoning/Evolution, optional docs/waveform,
runtime isolation, authority, budgets, trajectory capture/safe export, freeze,
final scoring, retry/batch recovery and result readers unchanged. Tiny reserved
tool descriptors remain; this pass does not replace actual tools or protocols.
No new dependencies, paid calls, Spectre work, private imports or old-tree edits.

## Acceptance and sequence

1. Main records scope; independent read-only review checks dependency closure.
2. Run the existing prototype and retained runtime/entrypoint regressions before
   deletion. Add a regression only for an uncovered accepted behavior; do not
   replace runtime assertions with tests that merely count deleted files.
3. Delete the four exact files, mark historical notes, rerun retained regressions
   and commit this independently reviewable slice.
4. Keep current-plan at no more than 150 lines, with a clear active queue,
   deferred experiments and history links. Check active navigation and CLI
   help, not exact prose. Record corpus activation without claiming quality.
5. Run active harness/result/layout regressions, Ruff and diff checks. Obtain
   independent stable-tree review, record actual test-count changes/skips,
   commit documentation and push only BucketSran origin/main.

Main is the sole writer/integrator. Advisers may read and report only. Stop the
affected change if an unexpected consumer, unrelated edit or behavior change
appears; do not widen deletion scope. Completion means reduced active surface,
working retained paths and explicit verification gaps, not new model evidence.

## Outcome

Implemented in `1f6de2fda9` after baseline locks and independent review. Exact
four-file retirement is recoverable at the base; current-plan is 103 lines.
Expanded validation: 1,461 passed / 68 optional skips / 1 existing historical
fixture excluded. Seven CLI help checks and static/navigation checks pass.
Maintenance rules and ownership closure are recorded separately; detailed
commands and publication status live in the verification log. No paid calls.
