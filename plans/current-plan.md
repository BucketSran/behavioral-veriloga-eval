# vaEVAS AI-Native Harness Evolution Plan

Updated: 2026-08-30

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

## Coding-agent framework transfer matrix

The coding-agent references are not planned as runtime dependencies. Each one
contributes a bounded design pattern with an explicit vaEVAS landing surface,
test obligation, and rejection boundary.

### SWE-agent / mini-swe - agent-computer interface

Borrow:

- a deliberately small, model-legible action surface instead of exposing every
  host capability;
- concise command observations with explicit exit, timeout, and truncation
  metadata;
- a terminal submission action that is distinct from ordinary shell success;
- history/context handling that preserves recent actionable evidence.

Planned landing:

- existing
  `benchmark-vabench-release-v4/operations/calibration_pilot/mini_swe_vabench.py`;
- `runners/agent_harness/backends/mini_swe.py` for the future adapter;
- the canonical action/observation schemas and observation normalizer;
- the submission terminal-state contract.

Proof required:

- the adapted mini-swe path is behaviorally equivalent on deterministic
  fixtures;
- shell exit, timeout, truncation, and submission remain different events;
- context reduction never removes the latest candidate/validation/submission
  identity needed to reproduce the next action.

Do not inherit:

- SWE-bench issue, GitHub, patch-target, or repository assumptions that are not
  part of a VABench task;
- host-level repository access or implicit network capability.

### OpenHands - event-driven controller and isolated runtime

Borrow:

- explicit `Action -> execution -> Observation` events;
- a step-oriented controller that derives state from recorded history rather
  than hiding mutable state inside the model adapter;
- separation among agent, conversation/event history, tools, and runtime;
- pre-execution capability/security validation.

Planned landing:

- `runners/agent_harness/controller.py` for the bounded step loop;
- `runners/agent_harness/state.py` and `trajectory.py` for event-derived state
  and append-only evidence;
- planned `runners/agent_harness/runtime.py` for clean-room ownership;
- planned `runners/agent_harness/capabilities.py` for pre-dispatch policy.

Proof required:

- every accepted action has exactly one ordered execution disposition and
  observation event;
- replaying the event stream reconstructs the same attempt state;
- denied actions produce evidence without mutating candidate state;
- runtime cleanup and controller outcome remain independent.

Do not inherit:

- OpenHands server/UI deployment, interactive confirmation workflow, or
  persistent cross-task conversation;
- unrestricted browser/network/runtime modes.

### Aider - candidate editing and checkpoint semantics

Borrow as a future tool-design input:

- explicit edit formats rather than ambiguous prose-based file replacement;
- exact-match/atomic patch application with actionable failure observations;
- compact candidate diffs;
- checkpoint semantics, mapped to content-addressed candidate snapshots rather
  than hidden Git commits.

Planned landing, only after the tool-design gate approves it:

- planned `runners/agent_harness/candidate_store.py`;
- a candidate-edit tool family placeholder in the capability registry;
- candidate before/after hashes and parent lineage in the trajectory.

Proof required if adopted:

- a failed edit leaves the candidate tree unchanged;
- an accepted edit records canonical diff plus before/after tree hashes;
- checkpoint restore creates explicit lineage and never rewrites frozen
  evidence.

Do not inherit:

- automatic Git commits, repository-wide maps, or broad source-tree context by
  default; VABench candidate artifacts are smaller and clean-room scoped.

### Codex CLI - sandbox and tool-policy evidence

Borrow:

- treat sandbox, filesystem, and network policy as runtime capabilities rather
  than prompt requests;
- separate ordinary shell execution from atomic structured edits;
- record tool identity, arguments, policy decision, result, and state effects;
- fail explicitly when a capability is absent instead of silently falling back
  to a broader execution mode.

Planned landing:

- planned `runners/agent_harness/capabilities.py` and `runtime.py`;
- tool-dispatch and trajectory evidence contracts;
- campaign manifests that freeze per-condition capabilities.

Proof required:

- forbidden paths, evaluator mounts, and undeclared network/tool access fail
  before execution;
- no fallback broadens a condition after a denial;
- directly compared backends resolve to the same effective capability set.

Do not inherit:

- user-approval UI, general MCP/plugin ecosystem, desktop state, or interactive
  production workflows that cannot be reproduced in unattended benchmark
  cells.

### Transfer acceptance rule

A coding-agent pattern enters production only when its source, intended vaEVAS
behavior, landing files, regression tests, experimental impact, and rejected
upstream assumptions are recorded in the migration ledger. Similarity to a
popular framework is not itself an acceptance criterion.

## Functional work plan

### Phase 0 - Reconcile the paused prototype

Status: `completed`

Goal: decide what to retain from the untracked `runners/agent_harness/`
prototype before any production integration.

Required changes:

- Retain the useful boundaries already demonstrated by tests:
  freeze-before-score, cleanup incidents, attempt lineage, and a tamper-evident
  JSONL event chain.
- Replace the current generic `Verifier` boundary with two asymmetric roles:
  a model-visible `PublicValidator` and a model-invisible `FinalJudge`.
- Replace `AgentAction(kind, payload: str)` with a versioned structured action
  carrying action ID, tool name, typed JSON arguments, source backend, and
  optional candidate binding.
- Expand `Observation` with tool status, public payload/hash, truncation,
  candidate binding, and budget deltas.
- Materialize formal failure outcomes instead of allowing ordinary protocol,
  budget, or environment errors to escape without classified result evidence.
- Decide whether final scoring is invoked by an outer scoring coordinator or
  by a terminal-only controller phase. In both designs, its result must never
  become a next policy observation.

Tests first:

- public-validator output can become a next observation;
- final-judge output cannot become a next observation;
- final judge receives only the immutable frozen submission snapshot and its
  bound tree hash;
- protocol errors, cleanup incidents, and infrastructure failures retain
  distinct dispositions;
- no production runner imports the prototype until its contracts pass review.

Stop condition: the prototype has an explicit keep/rework/delete disposition
for every module and is not committed as an accidental parallel harness.

Disposition recorded in `AA-VAE-015`:

- keep and rework `contracts.py`, `state.py`, `controller.py`, and `__init__.py`;
- keep the attempt-scoped hash-chain implementation in `trajectory.py`;
- keep and expand the public regression surface;
- keep the package disconnected from production runners until formal schemas
  and mini-swe compatibility are proven in later slices.

### Phase 1 - Freeze canonical protocols and manifests

Status: `in_progress`

Goal: make backend, action, tool, memory, validation, and final-test contracts
machine-checkable before implementation.

Add or extend:

- `vaevas-action-v1` JSON schema;
- `vaevas-observation-v1` JSON schema;
- backend capability and identity schema;
- tool descriptor schema with visibility, allowed conditions, budget class,
  state effects, argument schema, and evidence policy;
- public-validation profile schema;
- final-test profile schema;
- evolution manifest fields for rounds, branch/model roster, per-branch and
  total budgets, feedback scope, failure policy, selection rule, and tie-break;
- memory snapshot and candidate lineage schemas.

Completed slice:

- `vaevas-action-v1` and `vaevas-observation-v1` now have strict JSON schemas
  and trusted state serializers that emit detached JSON-compatible documents;
- argument and payload digests are canonical across mapping insertion order;
- constructors reject non-object roots, non-string object keys, non-finite
  numbers, and invalid budget deltas before a wire document can be emitted.
- provider-native function calls and strict standalone JSON proposals now
  normalize through one fail-closed boundary to the same `AgentAction`;
- action/backend/candidate/digest identity remains harness-owned, while an
  envelope-level syntax allowlist rejects unknown tool names before execution;
- duplicate keys, non-finite JSON constants, missing/extra fields, malformed
  JSON, and zero/multiple native calls are classified protocol rejections.

Still pending in this phase:

- backend, tool, validation/final-test, evolution, memory, and candidate
  lineage schemas;
- capability-aware tool descriptors and dispatch beyond the proposal
  envelope's syntax-only allowlist.

Formal parsing policy:

- prefer provider-native function calls when available;
- accept strict standalone JSON as the local-model fallback;
- validate with a real JSON parser and schema;
- do not use XML plus regex as formal tool authority;
- fail closed on ambiguous, mixed, missing, or extra actions;
- allow development-only parser repair only when explicitly configured and
  visibly recorded in the trajectory.

Tests first:

- native tool calls and strict JSON normalize to identical canonical actions;
- malformed JSON, extra properties, multiple terminal actions, and unknown
  tools fail closed;
- canonical serialization produces stable hashes;
- backend-specific syntax cannot alter the internal event schema.

### Phase 2 - Build the common controller, state, and event core

Status: `pending`

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

Status: `pending`

Goal: route the current mini-swe behavior through the new interfaces without
changing its task capability or score.

Implementation surface:

- adapt `VaBenchMiniModel` and `VaBenchBashEnvironment` to the common backend
  and environment contracts;
- keep sandboxed Bash, direct public EVAS, and `vabench-submit`;
- normalize mini-swe messages/tool calls into canonical action and observation
  events;
- preserve current prompt, provider, decoding, budget, clean-room, and
  submission behavior for the regression condition;
- add a compatibility switch so the existing runner remains recoverable until
  parity is proven.

Tests first:

- current focused mini-swe tests remain green;
- old and adapted paths produce equivalent frozen submissions on deterministic
  fixtures;
- capability isolation for One-shot, Agent-No-EVAS, and Agentic+EVAS remains
  unchanged;
- no evaluator/private path appears in model-visible mounts or events.

### Phase 4 - Reserve domain-tool extension points and run a design gate

Status: `pending`

Goal: make the harness extensible without treating the previously discussed
candidate, waveform, diagnostic, retrieval, or submission helpers as approved
features.

Existing minimum capabilities to preserve:

- sandboxed Bash in the mini-swe path;
- the current fixed public EVAS execution contract;
- the current submission transport and environment-owned freeze;
- model-invisible final judging.

Reserve namespaces only; do not implement them in this phase:

- candidate editing/checkpoint helpers;
- public-validation convenience helpers;
- artifact/log/waveform analysis helpers;
- documentation/retrieval helpers;
- submission convenience helpers.

Every proposed tool requires a separate design record answering:

1. Which concrete model failure or workflow cost does it address?
2. Why is the existing sandboxed Bash/public EVAS interface insufficient?
3. What information source does it expose, and is that source public and
   license-safe?
4. Is it read-only, candidate-mutating, terminal, or evaluator-authoritative?
5. Which conditions receive it, and how is capability matching enforced?
6. Which turn/tool/EVAS/token/wall budget does it consume?
7. What exact action, observation, candidate hash, and result evidence is
   recorded?
8. Can it leak checker/fault/final-test information or broaden network/path
   access?
9. Does it need a separate ablation to distinguish tool benefit from backend or
   evolution benefit?
10. What is the minimal RED test and clean-room smoke that proves its contract?

Outputs of this phase:

- a registry that rejects unregistered or condition-ineligible tools;
- placeholder capability families with no callable implementation;
- a reviewed `accepted`, `rejected`, or `deferred` decision for each proposed
  domain tool before code is added;
- one migration-ledger feature note for every accepted tool.

Tests first:

- an unimplemented placeholder cannot be invoked;
- an unregistered tool fails closed before state mutation;
- final judge can never appear in a model-visible registry;
- capability manifests resolve identically for matched backend comparisons.

### Phase 5 - Implement public validation / final test separation

Status: `pending`

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
4. Bash and structured domain tools coexist under one capability policy;
5. all continued generation uses public-validation information only;
6. final-test results are terminal, model-invisible, and sidecar-bound;
7. round scheduling cannot change the declared shared feedback snapshot;
8. trajectories join every model/tool/candidate event to the frozen submission
   and EVAS 0.8.7 result;
9. r53 and EVAS 0.8.7 remain byte-for-byte unchanged;
10. CI, targeted tests, clean-room smokes, independent review, and claim gates
    are green with unresolved risks explicitly recorded.

## Open risks

- The paused prototype may duplicate existing runner abstractions and must be
  reconciled before it becomes production code.
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
