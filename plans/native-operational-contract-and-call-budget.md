# Native operational contract and optional model-call budget

Date: 2026-08-30. Base: `32b63963bd2c71a9076f7d36066512f6a191c464`.
The user approved implementation of both changes after confirming the budget
semantics. Main owns implementation, integration and fork-only publication.

## Brief and acceptance KPIs

Layer: behavioral-eval native harness. Repair the missing Reasoning shell and
submission guidance, then support an optional positive integer model-call cap
without turning the DeepSeek pilot's choice of eight into a benchmark rule.

Required behavior:

1. Interactive Reasoning receives the actual public workspace and submit
   contract, correct for Agentic versus No-EVAS and for its proposal format.
   OneShot retains its output-only contract; legacy defaults remain unchanged.
2. An omitted call limit adds no call-count stopping rule. A configured positive
   integer N is frozen before execution, reported to the model with trusted
   remaining calls, and enforced before another model call can start.
3. The Nth admitted response may execute its legal action, including submission.
   No automatic final scoring is introduced for an unsubmitted call-limit stop.
4. Failure/attempt reconstruction cannot refund an admitted call. Logical model
   calls and underlying HTTP transport attempts remain distinct measurements;
   existing independent cost/transport protections still apply.
5. The result preserves limit, actual admitted calls and `model_call_limit` as
   the stop reason; it is not a generic provider outage or a scored model zero.
6. Parameterized free tests cover small and non-eight limits, missing/invalid
   configuration, the final legal action, exact stop boundaries, prompt/history
   consistency and attempts. Real Docker/EVAS fixtures cover freeze/score joins.

Primary KPI: all six contracts verified through real public interfaces and
immutable evidence joins. Secondary KPI: existing no-cap/default fixtures and
strict read-only score validation remain compatible. No model-quality target.

## Scope and non-goals

Main may modify native launcher/policy/controller/budget/state/evidence and
the existing campaign/pilot integration seams plus their focused tests. Reuse
existing budgets and schemas; do not build a second agent loop. Shared plans,
AGENTS, migration notes, logs and CI are main-owned. Adviser/reviewer lanes
are read-only and cannot write files or Git state.

No r53 task/manifest/policy changes, EVAS changes, legacy default replacement,
new dependencies, domain/RAG tools, live provider calls, credential reads,
paid reruns or edits/rejudging of the stopped pilot. Old evidence is immutable.
An explicit optional operational limit is not a change to sealed r53 wall time.

## Execution and evidence

1. Map existing seams and record boundary decisions. Use the preceding user
   discussion as the completed requirements interview; no new approval loop.
2. AA-VAE-053: one failing outbound-request contract test, minimal repair,
   then condition/proposal-format and real clean-room regressions. Review and
   publish this independently complete fix.
3. AA-VAE-054: vertical RED/GREEN slices for arbitrary cap enforcement and
   model-visible horizon, native entrypoint/manifest/results integration and
   pilot configuration. Review before publication; never publish a red main.
4. Run focused suites, relevant full harness regressions, static checks and
   free Docker smoke under a fresh ignored reports directory. Preserve exact
   outputs/hashes and scope in verification logs and both feature notes.
5. Stage exact files, inspect secrets and remotes, commit and push only to
   BucketSran origin/main; retain private test outputs outside Git.

Risks: Nth-action off-by-one, hidden implicit retries, stale budget prompts,
No-EVAS misleading instructions, changed history/score compatibility and cap
exhaustion being mislabeled as infrastructure failure. Stop the affected lane
on concurrent edits, unexplained release drift or required scoring-policy
expansion; do not expand the experiment or spend to validate the repair.
