# vaEVAS Agent Contract

## Project Mission

This repository is the benchmark, agent-harness, evaluation, and evidence side
of vaEVAS. The current development and evaluation mainline is:

> **vaEVAS = VABench v4/r53 + an AI-native generation harness + public EVAS
> feedback + strict EVAS trusted replay + reproducible evidence.**

Spectre is not the routine development scorer. It is a conditional
compatibility and audit backend used when EVAS changes or when an explicitly
named external/final protocol requires it. This keeps the normal experiment
loop fast without turning EVAS-backed results into unqualified Spectre claims.

The active release is
`benchmark-vabench-release-v4/release/benchmarkv4-r53/`. Its canonical
manifest, not older prose, defines the release identity and denominator. The
current expected release contains 400 matched families, 1,200 tasks, 2,000
certified faults, and uses `evas-sim==0.8.7` for the public EVAS runtime.

V3, `tasks/`, `vabench-main-v1-main120`, and the earlier EVAS-only closure are
historical provenance unless the user explicitly requests legacy work. Do not
let V3-oriented plans, READMEs, skills, or comments override this contract.

## Source And Repository Boundaries

- `origin` is the writable BucketSran fork. `upstream` is Arcadia-1 and is
  read-only for this project. Never push directly to upstream.
- Verify the current branch, dirty files, remotes, and upstream/fork baseline
  before changing code or publishing claims.
- Preserve unrelated user changes and other worktrees. In particular, do not
  use or modify an older dirty vaEVAS/EVAS worktree as scratch space.
- Treat the released r53 task bytes and manifests as immutable. Changes to a
  sealed release require a new release revision and explicit provenance; do
  not silently repair released evidence in place.
- EVAS is a separate, currently pinned evaluator/runtime repository. Do not
  change it unless a minimized integration case demonstrates a simulator,
  compiler, ABI, or package defect. Benchmark, harness, scoring-policy, or
  evidence problems belong in this repository. Any EVAS change activates the
  conditional Spectre parity gate for the affected semantics before that EVAS
  revision may replace the pinned development scorer.
- The public AlphaApollo project and paper may be used as methodological
  references for structured interaction, tool feedback, memory, and iterative
  refinement. Do not copy private-project code, data, prompts, trajectories,
  credentials, or organization-specific service details into vaEVAS.

## Authoritative Reading Order

Before evaluation or harness work, read in this order:

1. This `AGENTS.md`.
2. `benchmark-vabench-release-v4/release/benchmarkv4-r53/MANIFEST.json` and
   `benchmark-vabench-release-v4/R53_RELEASE_CERTIFICATION.md`.
3. `benchmark-vabench-release-v4/runners/README.md`.
4. `benchmark-vabench-release-v4/operations/calibration_pilot/README.md`, while
   applying the judge-authority correction in this contract.
5. `docs/alphaapollo-migration/00_迁移主线.md` and
   `docs/alphaapollo-migration/01_功能迁移台账.md` when changing the AI-native
   harness, trajectory, memory, tool, or result-generation surfaces.
6. The relevant runner, result protocol, tests, and dated decision/verification
   logs.

Treat plans and logs as dated evidence, not timeless authority. If they still
describe V3, an empty V3 denominator, a different EVAS release, or routine
Spectre scoring as mandatory for the current development mainline, they are
stale. A dated external or paper protocol may still require Spectre, but that
requirement must be explicit and must not silently redefine ordinary runs.

## Two Separate Operating Tracks

### Development And Evolution Track

AI-native development may use iterative `propose -> execute -> observe ->
update` loops, multiple agents, parallel candidates, executable checks, and
selective memory to improve unreleased assets, future release revisions,
runners, tests, diagnostics, and evidence tooling. For sealed r53 content,
these loops may only produce diagnostics, audit notes, or a named successor
release proposal.

Development feedback must remain visibly labeled with its evaluator identity.
Strict EVAS trusted replay is the default score for current development,
regression, ablation, and harness experiments. Such results may support
EVAS-scoped comparisons, but they do not establish Spectre equivalence unless
the conditional parity audit was executed. Private gold/checker/judge
information must never be written into prompts, reusable memories, public
artifacts, or later model-visible tasks.

Model-generated critique, majority vote, or an LLM-as-judge may guide
development or summarize diagnostics. VABench tasks have executable contracts,
so these mechanisms cannot replace simulator execution and the hidden checker
for a formal verdict.

### Frozen Evaluation Track

Formal evaluation is not a self-evolution campaign. Each cell starts in a
fresh sandbox and receives only the declared public task package. Cross-task,
cross-model, and cross-condition memory is forbidden. Multi-round or
multi-branch inference is allowed only as an explicitly named experimental
condition with a frozen budget and memory policy; it must not be compared to a
single-attempt baseline as if the budgets were equal.

Agentic learning, SFT, RL, prompt optimization from scored outcomes, or any
model-weight update is never part of a formal evaluation cell. If studied, it
is a separate training experiment with frozen train/test splits, sealed
checkpoints, and no leakage from hidden judge outcomes, certified faults, or
benchmark test tasks into the trained model.

The current matched conditions are:

- `One-shot`: one frozen generation without EVAS feedback.
- `Agent-NoEVAS` in the paper (`Agent-No-EVAS` in the current runner): the same
  agent harness and budget, with EVAS access blocked by the runtime rather than
  merely discouraged in the prompt.
- `Agentic+EVAS`: the same base model and matched controls, with public EVAS
  feedback available inside the episode.

The allowed differences between conditions must be enumerated in the campaign
manifest. Task package, model/service identity, decoding policy, terminal
budget, workspace image, submission contract, and declared judge remain
matched unless the experiment explicitly studies one of them. The default
declared judge is strict EVAS trusted replay.

For any multi-round, multi-branch, verifier-assisted, retrieval-assisted, or
best-of-k condition, the campaign manifest must freeze the maximum rounds,
branch fanout, verifier count, EVAS/tool-call budget, memory scope, retrieval
corpus, candidate-selection rule, and final-submission rule before the first
model call.

## AI-Native Trajectory Contract

AlphaApollo models a turn as prompt, model output, and environment feedback.
vaEVAS adopts that separation but strengthens it for auditable evaluation.
Every formal episode must produce an append-only, machine-readable event stream
covering at least:

- episode, cell, condition, task, family, model, provider, harness, image, and
  policy identities;
- `attempt_id`, sequence number, wall and monotonic timestamps, actor, and
  event type;
- model request/response identifiers, token counts, finish/terminal reasons,
  and sanitized content hashes;
- parsed tool call, exact public arguments, tool result status, exit code,
  timeout/truncation metadata, and output hash;
- candidate-tree hash before and after every mutating action;
- EVAS invocation identity, inputs, structured result, diagnostics, and
  candidate-tree binding;
- final submission-tree hash, terminal outcome, primary failure, cleanup
  incident, and retry lineage;
- `prev_event_sha256` and `event_sha256`, or an equivalent tamper-evident chain.

Keep raw sensitive trajectories in a private evidence store. Produce public or
reviewer-facing ledgers by a versioned normalizer, and bind every exported row
to the raw evidence hash and normalizer revision. Redaction must remove secrets
and hidden content without destroying event order, outcome, identity, or join
keys. A sanitized case summary is not a substitute for the internal raw trace.

Tool-call success, EVAS-call count, revision count, or trace length are process
metrics, not task correctness. Do not interpret a correlation between a tool
event and success as causal attribution.

## Agent Harness Requirements

- Run each episode in a fresh container or equivalent clean room with network
  disabled unless the frozen provider contract requires a declared endpoint.
- Internet access and retrieval tools are disabled unless explicitly declared.
  Any offline documentation or RAG corpus is a model-visible campaign artifact,
  must be frozen by hash, and must be matched across directly compared
  conditions unless retrieval access is the named intervention.
- Mount only model-visible inputs and the writable submission surface. Never
  mount private references, certified faults, hidden decks, checker internals,
  final scores, or previous episode artifacts into the agent environment.
- Pin and record the container image digest, Python/runtime dependencies,
  harness source revision, prompt/tool schema, model endpoint identity, model
  snapshot, and provider response metadata available at runtime.
- Enforce turn, token, wall-clock, output-size, tool-call, EVAS-call, and disk
  budgets in code. Do not rely on prompts for enforcement.
- Parse actions and tool results structurally. Malformed or missing structured
  output must fail closed in formal mode.
- Preserve the primary episode outcome when cleanup also fails. Record cleanup
  as a separate incident and include it in infrastructure accounting.
- Do not silently resume unfinished trajectories. A retry starts a new
  `attempt_id` from the same frozen inputs and clean state.
- Parallel execution must not share mutable candidate state or memory across
  cells. Record scheduling and concurrency because they can affect latency and
  provider behavior.

## Submission Freeze And Retry Lineage

The final submission is content-addressed and append-only. Once frozen:

- scoring verifies the stored tree hash and never deletes, rebuilds, or
  overwrites the frozen submission;
- score reports are immutable sidecars bound to the submission hash, campaign
  manifest, evaluator inputs, judge runtime, and scoring code revision;
- any repair creates a new freeze record with explicit parent lineage;
- every scheduled cell has exactly one counted terminal disposition: pass,
  candidate failure, invalid submission, or infrastructure failure;
- infrastructure retries use the same frozen configuration, receive a new
  attempt identifier, and record why the selected terminal record is counted;
- task replacement, silent denominator shrinkage, outcome-based retry, and
  reuse of candidate state are forbidden.

Deadline and post-deadline completions must remain separate named analyses.

## Evaluator And Judge Authority

The evaluator roles are deliberately asymmetric:

- **EVAS 0.8.7** is the pinned public in-loop evaluator and the default strict
  trusted-replay scorer for current development and evaluation runs.
- **Private Spectre plus the hidden checker** is a conditional compatibility or
  external-protocol audit backend. It is required when EVAS itself changes and
  may be required by an explicitly named final/paper protocol; it is not part
  of every ordinary experiment.
- **Spectre X** is an optional audit comparator and never becomes a primary
  score source implicitly.

Benchmark release qualification, EVAS-backed model scoring, and Spectre parity
are separate claims. R53 is release-certified by its declared EVAS gate, and
the current experiment pipeline may report EVAS-backed scores when every row is
explicitly bound to `judge_engine=evas`. This does not authorize describing an
EVAS result as Spectre-backed or simulator-independent.

Do not label an EVAS trusted replay as a Spectre-backed result. A formal score
row must bind `judge_engine`, observed judge/runtime version, judge input
manifest, submission hash, checker revision, score sidecar hash, and structured
verdict. A zero exit code without structured judge output is invalid in formal
mode, never an implicit pass.

When EVAS code, compiler behavior, simulator semantics, ABI, packaging, or the
pinned EVAS version changes, minimize the affected regression and run Spectre
parity on the impacted semantics before adopting the new EVAS revision. The
certified gold/fault EVAS-Spectre audit is evaluator-conformance evidence; it
does not by itself prove agreement on arbitrary model submissions. Preserve all
disagreements and classify compile, runtime, metric, checker, and infrastructure
causes before making an equivalence claim.

## Result Generation And Claim Boundaries

The result pipeline must be derivable from immutable record-level ledgers, not
manually assembled tables. Freeze one source-of-truth evidence package and
record hashes for any paper or reviewer export.

At minimum, generate and validate:

- scheduled, started, terminal, counted, invalid, and infrastructure counts;
- the complete denominator for every model, condition, task form, and slice;
- overall and task-form pass rates, matched per-task deltas, and the declared
  common-300 versus full-1,200 scope;
- paired Agentic+EVAS versus One-shot results and the Agent-NoEVAS workflow
  control, with uncertainty or paired tests where claims require them;
- deadline-primary and post-deadline sensitivity results as separate tables;
- model calls, tokens, wall time, EVAS calls, revisions, terminal reasons,
  failure taxonomy, and cleanup incidents;
- EVAS-Spectre agreement, disagreement cases, and speedups when a conditional
  Spectre audit is in scope, using explicitly defined comparable time
  intervals; otherwise mark this analysis as not executed, not silently zero;
- a claim-to-evidence index that binds every reported number to manifests,
  ledgers, analysis revision, and generated table/figure hashes.

`Agent-NoEVAS` supports a workflow-level claim about access to EVAS. It does
not isolate the causal effect of an individual diagnostic, waveform, or
revision step. Best-of-k, Pass@k, multi-branch evolution, and single-attempt
pass rate are different estimands and must never be merged under one label.

Missing identity, missing rows, missing structured evidence, judge mismatch,
or an unresolved denominator blocks the affected claim. Infrastructure
failures are reported separately and are never silently converted into model
failures or removed from the scheduled set.

## Repository Hygiene And Coding

- Follow `docs/REPO_LAYOUT_POLICY.md`. Do not create new top-level
  `generated-*`, `results-*`, `results_*`, `runlogs/`, `experiment-logs/`,
  `refine-logs/`, `scratch/`, or `tmp/` directories.
- Keep credentials, endpoints, raw provider payloads, unrestricted
  trajectories, simulator work roots, waveform dumps, and licensed/private
  judge artifacts out of Git. Commit only intentional, sanitized, reviewable
  fixtures or evidence indexes.
- Use existing utilities and schemas before adding abstractions or
  dependencies. Keep changes small, reversible, and owned by one layer.
- Follow the repository's Python style: four-space indentation, `snake_case`,
  type hints where useful, and single-purpose functions. Preserve existing
  JSON/YAML formatting unless a canonical formatter is already configured.
- Use short imperative commit subjects and focused commits. Pull requests must
  name the affected release/harness surface, claim scope, tests executed, and
  unresolved validation gaps.
- Run `python3 scripts/check_repo_layout.py` after layout or experiment-output
  changes when that checker is present. Otherwise run the repository's current
  layout/runtime-contract tests and record the missing dedicated layout gate.

### Commit And Publication Discipline

- Deliver harness evolution as a sequence of focused commits, not one
  repository-wide implementation dump. Protocols/tests, controller/state,
  backend adapters, capability policy, validation/final-test separation,
  evolution, evidence/results, and documentation are separate commit slices
  unless a smaller inseparable change is required for correctness.
- Every commit must be independently reviewable and safely revertible. Its
  subject names the feature slice, and its body or accompanying log records
  the contract changed, focused verification, and any remaining gap.
- Use RED -> GREEN locally, but do not publish a knowingly broken intermediate
  state to `main`. A tests-only contract commit is allowed only when it is
  intentional, CI-safe, and does not make the supported path fail.
- Before each commit, stage only the exact slice, inspect the staged diff, run
  its focused tests plus applicable static/repository checks, and exclude raw
  trajectories, generated experiment outputs, caches, credentials, and
  unrelated user changes.
- Push completed commits only to the writable BucketSran `origin`. Never push
  to Arcadia-1 `upstream`. Recheck branch, ahead/behind state, remotes, and the
  committed diff before every push.
- Keep planning/contract changes separate from runtime implementation when
  practical. Update the decision and verification logs in the commit that
  establishes the corresponding evidence so history remains reconstructable.

### Development Task Ownership And Integration

These rules govern coding tasks, not benchmark model/candidate concurrency.
The user-facing main coordinator is the sole integration and publication
owner. Read `plans/work-ownership.md` before resuming or delegating work.

- Delegated tasks are read-only by default. Before any delegated edit, the
  coordinator records the task/owner, exact files, base commit, forbidden
  surfaces, acceptance tests, and handoff in the ownership register. Only one
  active writer may own a file; a component label alone is not write authority.
- Only the coordinator may stage, commit, amend, merge, cherry-pick, rebase,
  switch branches, push, or otherwise mutate the shared Git index/history.
  Delegates return unstaged changes and evidence; they do not publish commits.
- The coordinator owns shared interfaces/exports, schemas, CI, `AGENTS.md`,
  plans, decision/verification logs, and migration ledgers. Delegates propose
  changes to these surfaces in their handoff instead of editing them.
- Do not start a second writer on a task's files until the previous owner has
  ended or explicitly handed them back. A resumed historical task must obtain
  a fresh assignment; old delegation text does not override this contract.
- On unexpected edits, index changes, or base drift, stop the affected writes
  and report the conflict. Never revert another task's work or apply a stale
  patch to recover ownership. Do not run repository-wide formatting or cleanup
  from a delegated task.
- Before integration, all delegated writers hand back their files and stop
  editing. The coordinator inspects the exact diff, runs focused and applicable
  integration checks on a stable tree, obtains independent read-only review,
  updates shared records, and publishes one reviewable slice to the fork.
- This is a workflow agreement, not an OS lock or proof that an independent
  Codex task was stopped. Record tool/status uncertainty rather than claiming
  that changing this file terminates another task.

## Implementation And Verification Workflow

1. State the exact claim or contract being changed and its stop condition.
2. Inspect the public solver surface before private evaluation assets.
3. Add or update a regression that fails for the identified gap.
4. Make the smallest change in the owning layer: benchmark, harness, evidence,
   scorer, or EVAS.
5. Run targeted tests, then the relevant v4 campaign/result protocol suite,
   static checks, and `git diff --check`.
6. For a formal-path change, run a one-task clean-room smoke that exercises
   generation, trajectory capture, frozen submission, strict EVAS scoring
   sidecar, and claim gating. Add Spectre parity only when the conditional gate
   is active.
7. Independently review leakage boundaries, denominator completeness, retry
   lineage, score authority, and result reproducibility before closure.
8. Record what was tested, what was not tested, external blockers, and the
   exact evidence hashes. Do not promote connectivity or ingestion smoke tests
   into model-performance evidence.

Primary v4 entry surfaces include:

- `benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py`
- `benchmark-vabench-release-v4/operations/calibration_pilot/run_campaign.py`
- `benchmark-vabench-release-v4/operations/calibration_pilot/result_protocol.py`
- `benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py`
- `benchmark-vabench-release-v4/operations/calibration_pilot/score_spectre_campaign.py`

## Minimum Closure Criteria

Evaluation closure requires all of the following:

- the r53 release, model roster, conditions, denominator, budgets, and runtime
  identities are frozen and machine-checkable;
- matched clean-room smoke evidence covers all declared conditions;
- raw trajectory provenance can be joined through submission freeze and the
  strict EVAS score sidecar to each published aggregate;
- when EVAS changed or an explicit external protocol requires it, the affected
  submission/evaluator evidence also joins to a Spectre parity sidecar;
- retries, invalids, infrastructure failures, cleanup incidents, and deadline
  boundaries are complete and explicit;
- formal scoring fails closed on missing structured evidence;
- current CI and targeted closure tests are green;
- paper claims stay within the executed judge, sample, condition, and evidence
  scope;
- no EVAS modification is claimed or made without a minimized evaluator defect.

Until these conditions hold, report the status as evaluation hardening or
partial closure, not as a completed formal evaluation.
