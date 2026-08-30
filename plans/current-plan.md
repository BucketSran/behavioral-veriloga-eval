# vaEVAS AI-Native Harness Evolution Plan

Updated: 2026-08-30

Completed detail and the original design matrix are preserved in the
[dated plan snapshot](archive/2026-08-30-harness-plan-snapshot.md).
This file is the active queue, not a cumulative execution log.

## Current Status

- Phase 0/1/3/4 bounded contracts and compatibility work are complete.
- Phase 2/5 are **in progress**: the opt-in native single-cell path works,
  but campaign/form/retry/content/ledger closure remains open.
- Phase 6-10 are **pending**. Reasoning/Evolution are not implemented.
- Legacy mini-swe remains default. Native format recovery, multi-action and
  deadline behavior intentionally differ; see [AA-VAE-038](../docs/alphaapollo-migration/features/AA-VAE-038-mini-swe-behavior-differential.md).
- Last local full regression retains **625 passed / 6 skipped / 1 failed**
  (the legacy one-second timeout case). Hosted CI success is separate evidence,
  not a replacement for that failure. Exact results: [verification log](../logs/verification-log.md).

## Objective

Evolve the current VABench r53 evaluation harness into a reusable AI-native
agent harness by combining:

- AlphaApollo-style reasoning, round-based multi-model evolution, explicit
  memory, and verifier-driven refinement;
- coding-agent workspace, shell, editing, sandbox, and event-loop patterns;
- vaEVAS-owned validation/test authority, submission freeze, trusted replay,
  evidence, and claim boundaries.

The first production target is not SFT or RL. It is a differential harness with
the existing mini-swe backend retained, a new single-trajectory AlphaApollo
reasoning backend, and a separately named AlphaApollo evolution condition.

## Frozen boundaries

- Benchmark: immutable VABench v4/r53 at
  `benchmark-vabench-release-v4/release/benchmarkv4-r53/`.
- Evaluator/runtime: `evas-sim==0.8.7`.
- Do not modify r53 task bytes, manifests, evaluator fixtures, or EVAS.
- Spectre remains outside the routine path unless EVAS changes or an explicit
  external protocol activates the compatibility gate.
- Write only to the BucketSran behavioral-eval fork. Do not push upstream.
- Preserve the older dirty EVAS worktree and its existing
  `fix/dynamic-zero-period-timer` changes.
- Use only public AlphaApollo and public coding-agent implementations and
  documentation. Do not read or copy private AlphaApollo project material.

## Development ownership and integration

The main coordinator owns shared interfaces, plans/logs, integration, and all
Git publication. Delegated tasks are read-only unless assigned exact,
non-overlapping files in [work-ownership.md](work-ownership.md). No delegated
writing lane is currently active. The historical result-store task is complete;
the unfinished dispatch task's interface question is reassigned to the main
coordinator for review, not automatic implementation. This workflow change
does not alter benchmark model/evolution concurrency or complete Phase 5.

## Approved architecture decisions

1. Keep mini-swe as a supported backend and regression baseline.
2. Add AlphaApollo reasoning as a matched single-trajectory backend.
3. Add AlphaApollo evolution as a separate, explicitly budgeted condition.
4. The first evolution version uses different models in parallel, immutable
   round feedback snapshots, and deterministic candidate selection.
5. Keep Bash as a sandboxed coding tool. Bash is an action capability, not the
   action serialization protocol.
6. Use versioned JSON/native function calls as the canonical action and
   observation protocol. XML may delimit prompt context but is not an
   authoritative tool protocol; regex extraction is not accepted in formal
   mode.
7. Add a capability-controlled tool registry with reserved vaEVAS extension
   points. The concrete domain-tool inventory is not approved yet and requires
   a separate design discussion and per-tool ablation decision.
8. Use public validation feedback for all evolution and candidate selection.
   Run the model-invisible final test only after submission freeze.
9. If a final-test outcome is used for further generation or selection, that
   invocation must be reclassified as a verifier call and cannot remain the
   terminal score for the same episode.
10. Keep final scoring EVAS-backed and explicitly bound to EVAS 0.8.7. Do not
    imply Spectre equivalence.

## Target component model

```text
campaign / evaluation authority
    |
    +-- condition and budget manifest
    +-- clean-room factory
    +-- public-validation profile
    +-- model-invisible final-test profile
    +-- result and claim gate
    |
episode controller
    |
    +-- backend adapter
    |     +-- mini-swe
    |     +-- AlphaApollo reasoning
    |     +-- AlphaApollo evolution policy
    |
    +-- canonical JSON action / observation protocol
    +-- capability-controlled tool registry
    +-- attempt-owned state and candidate lineage
    +-- append-only trajectory recorder
    |
public environment
    |
    +-- sandboxed shell
    +-- current public EVAS capability
    +-- current submission transport
    +-- reserved domain-tool extension points
    |
submission freeze
    |
model-invisible EVAS 0.8.7 final test
    |
immutable score sidecar and claim-to-evidence join
```

## Coding-Agent Design References

The approved SWE-agent/mini-swe interface, OpenHands controller/runtime, Aider
editing/checkpoint and Codex CLI sandbox-policy transfer matrix is preserved in
the [design snapshot](archive/2026-08-30-harness-plan-snapshot.md#coding-agent-framework-transfer-matrix).
These are design references, not new runtime dependencies or blanket reuse
approval. Land each adopted pattern through the [feature ledger](../docs/alphaapollo-migration/01_功能迁移台账.md)
with source, exact code, tests, experimental impact and rejected assumptions.
Domain editing, waveform and retrieval tools still require their own gate.

## Functional Work Plan

### Phase 0 - Reconcile the paused prototype

Status: `completed`

The prototype was reconciled into the common contracts/controller/state/event
surface (AA-VAE-015). Do not restart the old untracked-prototype assignment.

### Phase 1 - Freeze canonical protocols and manifests

Status: `completed`

Action/observation, backend/tool/authority profiles, memory/lineage and evolution
manifest contracts are implemented (AA-VAE-016 through AA-VAE-022).
Contract/reducer tests do not constitute an operational evolution backend.

### Phase 2 - Build the common controller, state, and event core

Status: `in_progress`

Goal: one controller contract serves mini-swe and AlphaApollo without changing
the evaluator authority.

Responsibilities:

- controller owns the bounded propose -> act -> observe -> update loop;
- environment owns workspace, tools, candidate state, budgets, and done state;
- backend owns model requests and action production only;
- candidate store owns immutable snapshots and parent lineage;
- public validator owns model-visible executable feedback;
- scoring coordinator/final judge owns terminal replay after freeze;
- trajectory recorder owns ordered, append-only evidence.

Implemented: capability-aware dispatch, classified rejections, effect checks,
tool/public-validation budget accounting, semantic trajectory validation and
CI selection (AA-VAE-023 through AA-VAE-026). Deadline finalization and decoded
provider evidence have an opt-in launcher implementation (AA-VAE-037), not
complete campaign coverage. Detailed contracts remain in the migration notes.

Remaining Phase 2 gaps:

- model request/response identity and model token accounting need a backend
  adapter source of truth;
- wall-time, disk, and evaluator-runtime budgets need trusted runtime meters,
  not model- or tool-reported values;
- postcondition checks detect an incorrect environment mutation but cannot
  roll it back; production adapters need transactional candidate snapshots or
  fresh-workspace discard semantics;
- candidate lineage events still need production candidate-store/runtime joins;
- the immutable trajectory/submission/authority/score-sidecar artifact now
  has an opt-in native episode / production replay writer and r53 smoke;
  complete campaign CLI, raw-content archives and aggregate ledgers remain open.

Required event types include:

- episode and attempt lifecycle;
- model request/response identity and token accounting;
- action proposed, parsed, rejected, or executed;
- tool observation with output/truncation hashes;
- candidate created, modified, forked, validated, selected, and frozen;
- public-validation invocation and feedback snapshot;
- budget update and terminal reason;
- final-test invocation and immutable sidecar join;
- retry, cleanup, and infrastructure incidents.

Tests first:

- deterministic state transitions;
- hard turn/token/wall/tool/EVAS/disk budgets;
- candidate hash changes only after declared mutating actions;
- retry receives a fresh attempt and workspace;
- cleanup cannot overwrite the primary outcome;
- trajectory validation detects deletion, reordering, or mutation.

### Phase 3 - Preserve mini-swe through a backend adapter

Status: `completed` (bounded compatibility slice)

The typed policy/environment bridge and opt-in single-cell launcher reuse the
existing model, Bash, submission and freeze surfaces (AA-VAE-027/037).
AA-VAE-038 compares deterministic legacy/native behavior and fixes rejected
proposals misclassified as infrastructure failures. This is not blanket parity:
legacy format recovery/multiple actions and native deadline handling differ.
Provider failure taxonomy remains coarse; keep these differences frozen before
any matched model comparison. Legacy campaign selection stays unchanged.

### Phase 4 - Reserve domain-tool extension points and run a design gate

Status: `completed` (reservation/design gate only)

AA-VAE-028 reserves five non-callable namespaces: candidate, public validation,
retrieval, submission and waveform. Every concrete tool family is deferred.
Before activation, record the addressed failure/cost, why Bash is insufficient,
public/licensed information source, state/authority effects, matched conditions,
budget and evidence contract, leakage audit, ablation, RED test and clean-room
acceptance. A reserved name does not promise its future API or implementation.

### Phase 5 - Implement public validation / final test separation

Status: `in_progress`

Goal: allow strong iterative feedback without converting the terminal judge
into an adaptive oracle.

Public-validation behavior:

- callable inside the episode under a frozen budget;
- uses EVAS 0.8.7 and only declared public fixtures/observables;
- may return sanitized compile, runtime, property, metric, log, and waveform
  diagnostics;
- binds every result to candidate hash and validation-profile hash;
- may enter the next-round memory snapshot.

Final-test behavior:

- callable only by the harness after submission freeze;
- uses the model-invisible final profile and checker;
- runs once for the selected terminal submission, subject only to explicit
  infrastructure retry policy;
- writes an immutable sidecar and never a model observation;
- cannot participate in candidate repair, ranking, selection, or later r53
  tasks.

r53 interpretation:

- Testbench tasks already provide strong separation: reference-DUT public
  validation versus evaluator-only certified faults.
- DUT and bugfix tasks currently provide a shared visible stimulus deck with a
  held-out checker. Report this as `shared_stimulus_heldout_checker`, not as a
  fully held-out stimulus/test set.
- A future disjoint DUT/bugfix stimulus profile would require a named successor
  protocol/release and is not part of this r53 plan.

Tests first:

- final checker paths and outputs are unavailable to the model container;
- final-test results are absent from policy and evolution memory;
- using a final result for another generation step invalidates terminal-score
  classification;
- candidate selection uses public-validation evidence only;
- final sidecar binds submission, judge, profile, checker, and result hashes.

Implemented bounded slices: public/final authority profiles, immutable sidecar
store, production final replay receipt, candidate-bound public simulation,
native result join, single-cell mini-swe launcher, and behavior differential
(AA-VAE-029 through AA-VAE-038). Real r53 Docker smokes verify the composed path
with deterministic providers; they are not model-quality or full-campaign
experiments. Legacy defaults and r53/EVAS bytes remain unchanged.

The current score contract labels EVAS replay `development_only`; formal
authority is not inferred from terminal position. DUT/bugfix public simulation
remains the existing Bash capability, not activation of a reserved domain tool.

Still required before Phase 5 completion:

- Testbench reference-only support and campaign integration beyond the bounded
  DUT/bugfix public-simulation adapter;
- full campaign CLI authority/profile distribution beyond the new opt-in
  Python scoring API, plus explicit infrastructure-only retry orchestration;
- clean-room evidence that final outputs never enter generation, candidate
  selection, or shared memory;
- a real campaign result join using native typed trajectory evidence rather
  than a fabricated conversion from incomplete legacy traces.

Recommended execution order after the generic store:

1. production final executor + receipt integration (opt-in slice verified);
2. production public-validation adapter (opt-in DUT slice verified);
3. broader resume/checkpoint/retry lineage verification (bound runtime's
   persistent no-reentry gate implemented);
4. native typed campaign result join (opt-in episode writer verified; full
   campaign launch/distribution and aggregate ledger still pending);
5. only then start the AlphaApollo reasoning/evolution backend comparison.

### Phase 6 - Add the AlphaApollo single-trajectory reasoning backend

Status: `pending`

Goal: compare AlphaApollo-style reasoning with mini-swe under matched task
capability and budget.

Adapt from public AlphaApollo:

- agent/environment turn separation;
- tool-group registration pattern where useful;
- explicit short-term memory;
- local and OpenAI-compatible model adapters;
- structured trajectory collection.

Replace rather than copy:

- informal-math environment;
- XML answer/tool parsing;
- math ground truth and answer scoring;
- math Python/RAG corpus defaults;
- LLM verifier voting as score authority.

Matched comparison requirements:

- same task bytes and clean-room image;
- same model/provider/snapshot and decoding policy;
- same public prompt information;
- same effective Bash, candidate, EVAS, waveform, RAG, and submission
  capabilities;
- same turn, token, wall, tool, and EVAS budgets;
- same submission freeze and final-test judge.

Tests first:

- backend contract tests with deterministic fake models;
- local and API model adapter normalization tests;
- matched-capability manifest test against mini-swe;
- one-task clean-room reasoning smoke per task form.

### Phase 7 - Add round-based multi-model evolution

Status: `pending`

Goal: implement the first explicitly named AlphaApollo-Evolution+EVAS
condition without scheduling-dependent feedback exposure.

Reuse/adapt from public AlphaApollo with license/NOTICE preservation:

- branch configuration and result records;
- parallel branch execution and failure isolation;
- multi-round orchestration;
- shared solution/candidate memory concepts.

vaEVAS-specific evolution protocol:

1. Freeze model roster, branch IDs, rounds, budgets, validation profile, and
   selection rule before the first call.
2. At round `r`, every branch starts from the same immutable feedback snapshot.
3. Branches run independently and cannot read in-flight peer state.
4. Wait for all branches or apply a predefined timeout/failure policy.
5. Run public validation on eligible candidates.
6. Canonically sort candidates and feedback, then freeze the round snapshot.
7. Begin round `r+1` with the same snapshot visible to every surviving branch.
8. Select the final candidate using only declared public-validation metrics and
   a deterministic hash tie-break.
9. Freeze that candidate and run the model-invisible final test once.

Memory restrictions:

- memory scope is one task, cell, and episode;
- no cross-task, cross-model-cell, or cross-condition memory;
- candidate source and sanitized public diagnostics may be shared;
- model identity need not be exposed to peer models unless it is a named
  intervention;
- final-test outcome never enters the evolution snapshot.

Tests first:

- provider latency/order cannot change the round-`r+1` visible snapshot;
- candidate ordering and selection are stable under completion-order changes;
- failed/timeout branches follow the frozen policy;
- no mutable candidate directory is shared across branches;
- total budget equals the sum of recorded branch/tool/model budgets;
- final-test output cannot trigger another round.

### Phase 8 - Complete trajectory, evidence, and result generation

Status: `pending`

Goal: make every model result derivable from raw trajectory through frozen
submission and final score.

Required joins:

- campaign -> cell -> episode -> attempt -> branch -> round;
- model request/response -> action -> tool result;
- action -> before/after candidate hashes;
- public validation -> candidate and validation profile;
- feedback snapshot -> member candidate/result hashes;
- selected candidate -> immutable submission freeze;
- final test -> submission, evaluator, checker, profile, and sidecar hashes;
- record-level ledger -> aggregate table/figure and claim index.

Export policy:

- retain raw sensitive traces in the private evidence store;
- generate public ledgers through a versioned normalizer;
- preserve event ordering and join keys after redaction;
- report tool use, revisions, and EVAS calls as process metrics, not correctness;
- classify model, candidate, protocol, infrastructure, timeout, and cleanup
  outcomes separately.

Tests first:

- every aggregate row resolves to an immutable terminal record;
- no row has a missing denominator or silent retry/replacement;
- redacted exports validate against the raw hash-bound index;
- score reports reject missing identity, missing structured verdict, hash drift,
  and judge/profile mismatch.

### Phase 9 - Define experimental conditions and ablations

Status: `pending`

Primary conditions:

- existing `One-shot`;
- existing `Agent-No-EVAS`;
- existing mini-swe `Agentic+EVAS`;
- new `AlphaApollo-Reasoning+EVAS`, matched to mini-swe;
- new `AlphaApollo-Evolution+EVAS`, separately budgeted and reported.

Required ablations after core parity:

- backend only: mini-swe versus AlphaApollo reasoning with matched tools/budget;
- evolution only: AlphaApollo single trajectory versus round-based evolution;
- Bash-only versus structured candidate/edit helpers;
- raw EVAS logs versus waveform/diagnostic helpers;
- no retrieval versus frozen documentation RAG;
- single-model versus multi-model evolution;
- deterministic round barrier versus asynchronous sharing only as a separately
  named exploratory condition.

Reporting rules:

- never merge pass@1, best-of-k, multi-branch, and oracle-guided estimands;
- report total model, token, wall, validation, tool, and branch costs;
- compare matched conditions only where capability and budget equality holds;
- report r53 Testbench held-out faults separately from DUT/bugfix
  shared-stimulus held-out-checker results;
- do not promote single-task smokes into model-quality claims.

### Phase 10 - CI, clean-room smoke, documentation, and merge gates

Status: `pending`

CI layers:

1. schema and canonicalization tests;
2. controller/state/trajectory unit tests;
3. backend contract tests;
4. tool security/capability tests;
5. validation/final-test leakage tests;
6. deterministic evolution tests with fake models and reordered completions;
7. mini-swe regression suite;
8. one-task-per-form clean-room smoke;
9. result/claim protocol suite;
10. Ruff, bytecode/type/static checks where configured, workflow parsing, and
    `git diff --check`.

Documentation updates:

- maintain `docs/alphaapollo-migration/` as the feature migration ledger;
- add one feature note per migrated capability with public source, idea,
  implementation files, deviations, tests, status, and license notice;
- add a coding-agent comparison note covering the exact SWE-agent/mini-swe,
  OpenHands, Aider, and Codex CLI patterns, landing files, tests, and rejected
  assumptions recorded in this plan;
- update `AGENTS.md` only after the implemented runtime and tests support the
  corresponding contract;
- update runner documentation and campaign examples without changing sealed
  r53 artifacts.

Merge gates:

- review architecture and duplicated abstractions before integration;
- independently review leakage, final-judge authority, schedule determinism,
  retry lineage, denominator handling, and claim scope;
- commit each independently reviewable feature slice after its focused tests;
  never bundle the full harness migration into one history entry and never
  commit the paused prototype as-is;
- keep local RED steps unpublished, publish only CI-safe GREEN commits, and
  push each completed slice only to the BucketSran fork after review passes.

## Suggested implementation slices

1. Protocol schemas and RED tests.
2. Common state/event/controller core.
3. mini-swe adapter and parity smoke.
4. Capability registry, non-callable extension points, and tool-design gate.
5. Public-validation/final-test split.
6. AlphaApollo reasoning backend.
7. Round-based multi-model evolution.
8. Any separately approved domain tool as its own feature and ablation slice;
   waveform and RAG remain deferred examples, not scheduled commitments.
9. Campaign conditions, ablations, evidence joins, and claim gates.
10. Final clean-room verification, independent review, and fork-only merge.

Each slice follows RED -> minimal implementation -> focused tests -> affected
v4 suite -> clean-room smoke when the formal path changes -> independent
review -> documentation/evidence update.

## Stop condition

This plan is complete only when:

1. mini-swe remains reproducible through the common harness;
2. AlphaApollo reasoning runs as a matched backend;
3. AlphaApollo evolution runs as a separately budgeted multi-model condition;
4. Bash and any separately approved domain tools use one capability policy;
   unapproved tools remain reserved, not mandatory implementation work;
5. all continued generation uses public-validation information only;
6. final-test results are terminal, model-invisible, and sidecar-bound;
7. round scheduling cannot change the declared shared feedback snapshot;
8. trajectories join every model/tool/candidate event to the frozen submission
   and EVAS 0.8.7 result;
9. r53 and EVAS 0.8.7 remain byte-for-byte unchanged;
10. CI, targeted tests, clean-room smokes, independent review, and claim gates
    are green with unresolved risks explicitly recorded.

## Open risks

- New backends must reuse the integrated controller/runtime boundaries rather
  than revive the reconciled prototype or duplicate the existing runner.
- Public validation diagnostics can overfit the visible profile; final claims
  must retain the held-out-checker/fixture distinction.
- Multi-model evolution changes compute budget and estimand even when the base
  model is unchanged.
- Local/API model endpoints may not expose identical token or sampling
  controls; unmatched metadata must be reported rather than silently ignored.
- RAG licensing, corpus contamination, embedding nondeterminism, and hidden
  benchmark overlap require explicit audit.
- Structured helper tools may improve results independently of the reasoning
  backend and therefore require separate ablations.
- Round barriers improve information-set reproducibility but do not eliminate
  model-sampling or provider nondeterminism.
