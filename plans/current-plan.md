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

Status: `completed`

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
- `vaevas-backend-profile-v1` now freezes backend identity, inference mode,
  proposal compatibility, model-interface capability, state scope, and named
  external contract dependencies without copying campaign/environment values;
- backend profiles are content-addressed with a canonical SHA-256 that is
  stable across mapping order and sensitive to contract changes.
- `vaevas-tool-descriptor-v1` and the fail-closed `ToolRegistry` now separate
  parser syntax allowlists from execution authority, deep-freeze resolved
  capability contracts, and content-address effective condition-specific tool
  sets;
- reserved domain-tool placeholders have no handler and cannot be authorized;
  final judging remains outside the ordinary tool registry.
- `vaevas-public-validation-profile-v1` and `vaevas-final-test-profile-v1`
  now freeze the public EVAS feedback authority separately from terminal
  trusted replay, even though both currently bind to r53 and EVAS 0.8.7;
- final replay is classified as infrastructure-only and must reuse the same
  frozen submission with a fresh judge attempt and no model reentry.
- `vaevas-memory-snapshot-v1` admits only public model/tool/validation evidence
  into episode-local memory and rejects final or private feedback sources;
- `vaevas-candidate-lineage-v1` records one artifact parent plus optional
  influence references, freezes terminal candidates, and validates lineage
  order/cycles.
- `vaevas-evolution-manifest-v1` now freezes AlphaApollo-style round-based
  condition contracts, including roster, budgets, tool registry hash, authority
  hashes, memory policy, barrier/deadline policy, and selection rule;
- round snapshots are completion-order invariant, reject final feedback, and
  select candidates only from public metrics plus candidate hash/id tie-breaks.

Review hardening completed for this phase:

- authority profiles bind benchmark, evaluator/judge, checker, runtime,
  campaign, command, structured-result, and immutable-sidecar identities;
- retry memory always starts empty and lineage validation rejects same-round,
  terminal-parent, forged-parent, cyclic, or non-canonical state;
- sealed evolution rounds enforce one terminal record per frozen roster branch,
  exact finite metrics, deterministic winner recomputation, and validated
  last-sealed-incumbent fallback after a global deadline;
- the four focused contract suites pass `114` tests and the complete generic
  harness suite passes `197` tests, without importing the package from the
  production r53/mini-swe runner.

Still pending after this phase:

- capability-aware dispatch and production adapter integration beyond the
  frozen protocol contracts;
- campaign/result joins for backend/tool/profile/manifest hashes;
- CI selection for the new contract tests.

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

Completed slice:

- `EpisodeController` now requires a trusted `ToolRegistry`, resolves the exact
  condition-specific toolset at episode start, and authorizes every
  model-visible action before `environment.step`.
- Authorized actions emit harness-visible `action_authorized` evidence with
  effective capability hash, tool identity, handler identity, descriptor hash,
  candidate hash, and condition; handler/capability evidence stays out of the
  model-visible projection.
- The controller passes the resolved `ToolCapability` into `Environment.step`,
  so execution is bound to trusted registry resolution rather than a second
  lookup of the model-supplied tool name.
- Registry denials emit `action_rejected`, materialize as protocol failures,
  and stop before any environment/candidate mutation while still preserving
  cleanup evidence.
- Descriptor-declared candidate binding rejects missing or stale action
  bindings against the latest trusted environment observation.
- Harness-internal/final-only tools cannot enter model-visible dispatch.
- `FinalJudge` remains outside ordinary tool dispatch and is still reachable
  only through the post-freeze terminal controller phase.
- Tool descriptors now distinguish active, inactive, and reserved lifecycle;
  the complete registry and the condition-effective toolset have separate
  hashes, and missing runtime handlers return classified execution failures.
- Static schema/registry validation rejects inconsistent state, candidate, and
  submission-budget effects before an episode starts.
- Runtime postconditions enforce read/none immutability, require mutating tools
  to report a candidate hash, require freeze tools to terminate as submitted,
  and bind the terminal observation to the frozen submission tree.
- An attempt-scoped `BudgetLedger` derives canonical tool/public-validation
  costs from the resolved capability, blocks the next over-budget dispatch
  before environment mutation, and rejects environment-reported counters that
  are not bound to that capability.
- SHA-chain validation now has a separate semantic layer covering attempt
  identity, lifecycle, action proposal/authorization pairing, required event
  visibility, submission-before-final order, and the no-model-events-after-
  freeze boundary.
- `.github/workflows/evaluator-closure.yml` now triggers on and runs the full
  generic harness contract suite.

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
  exists at the generic harness protocol layer, but still needs to be connected
  to production campaign result writers and real r53 result ledgers.

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

Status: `completed`

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

Completed compatibility slice:

- `MiniSwePolicyBridge` converts one provider-native Bash call into a canonical,
  harness-identified, candidate-bound action.
- `MiniSweBashEnvironmentBridge` wraps the existing `execute(dict)` surface,
  preserves gate rejection as non-terminal feedback, maps only the explicitly
  bound mini-swe `Submitted` exception to the submitted terminal state, and
  delegates candidate identity/freeze to trusted runtime callbacks.
- the generic Bash descriptor freezes handler identity, argument schema,
  candidate effect, evidence policy, and condition eligibility.
- deterministic integration coverage compares the direct legacy environment
  with the typed bridge for candidate creation, submission, artifact hash,
  command disposition, no-EVAS behavior, and immutable freeze.
- production `DefaultAgent` and campaign selection remain legacy-first. This
  phase proves an opt-in differential path; it does not switch formal runs or
  claim hosted-provider trajectory equivalence.

### Phase 4 - Reserve domain-tool extension points and run a design gate

Status: `completed`

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

Completed design-gate slice:

- five harness-internal namespace markers reserve candidate, public-validation,
  retrieval, submission, and waveform families without granting a handler,
  model visibility, budget, state mutation, or evidence-flow authority;
- reserved markers change the complete registry identity but do not change the
  effective capability hash used by matched backend comparisons;
- every reserved family fails closed before dispatch, and final judges remain
  outside the ordinary tool registry;
- all five concrete tool families are `deferred`. Existing sandboxed Bash,
  public EVAS, and `vabench-submit` remain the minimum production surface until
  a family-specific failure analysis, source/licence review, clean-room test,
  and ablation justify activation;
- this phase reserves compatibility space only. It does not promise that the
  placeholder name, arguments, observation schema, or handler will become the
  final active tool contract.

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

Completed authority-binding slice:

- canonical observations now carry an optional
  `validation_profile_sha256`; public-validation observations must bind the
  exact campaign-owned profile before they can enter the next model turn;
- the controller rejects an unbound campaign profile before environment
  dispatch and rejects missing or mismatched observation profiles before
  recording a model-visible observation;
- public-validation capabilities are schema- and registry-constrained to be
  model-visible, candidate-bound, read-only, and free of private evidence;
- trajectory observation events record the validation profile hash for later
  memory, evolution, and result joins.
- `ProfileBoundFinalJudge` accepts only a `FrozenSubmission`, validates the
  returned judgment and immutable score sidecar against the detached final
  profile, computes the exact profile-input identity, and is single-use even
  after an executor failure;
- final sidecar schema identity is now joined to the final profile contract;
  the adapter exposes a detached sidecar document and canonical hash to a
  trusted outer writer without adding it to model-visible controller events.
- final profile also binds `score_authority`; legacy v1 profiles safely default
  to `development_only`, and formal sidecars require an explicit formal
  authority declaration.
- `write_immutable_score_sidecar` now validates before I/O and publishes
  canonical, content-addressed evidence without overwrite using same-directory
  fsync plus exclusive-link semantics; its receipt binds sidecar, profile,
  profile-input, and submission identities without emitting a model event.
- production score reports now label EVAS trusted replay as
  `development_only` and reserve `formal` for the explicit `final_spectre`
  judge kind; terminal position no longer implies formal authority.
- the opt-in production EVAS executor now joins the generic authority adapter
  and immutable writer, returning a typed receipt without generation write-back;
  it rejects pre/post-execution identity drift and reserves terminal execution
  persistently, including failures and legacy rerun/model-resume attempts;
- a deterministic one-task three-arm Docker smoke exercises this bound path
  with unchanged generation evidence. It is not a native typed trajectory,
  model-quality comparison, or complete memory/lineage closure.
- the opt-in public EVAS adapter now emits candidate/attempt/profile-bound
  simulation observations through the existing Docker runtime. A separate
  r53 DUT smoke verifies native controller trajectory and pre-dispatch budget
  enforcement; it neither executes final scoring nor switches campaign routing.

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
4. native typed campaign result join;
5. only then start the AlphaApollo reasoning/evolution backend comparison.

#### Verified slice - production final replay receipt (2026-08-30)

Brief: connect the existing trusted replay executor to the typed final-authority
adapter and immutable sidecar store through an opt-in production scoring path.
Keep legacy mini-swe generation and scoring behavior available for comparison.

Acceptance / KPI:

- real replay returns a verified content-addressed sidecar receipt;
- frozen submission, evaluator, EVAS, command, and runtime identity drift fails
  closed before publication; missing structured output never becomes a pass;
- repeated invocation cannot overwrite evidence or silently rerun the judge;
- scoring leaves generation/checkpoint/trajectory bytes unchanged;
- the deterministic r53 three-arm Docker smoke exercises this path without
  implying model-quality, fully typed trajectory, or Spectre evidence.

Execution: one behavioral RED/GREEN at a time; production adapter and tests,
then smoke/resume boundary and documentation as separate reviewable commits.
Independent review precedes fork-only publication. No new dependencies, domain
tools, r53 edits, EVAS edits, or model API experiments are in this slice.
Explicit infrastructure retry orchestration and native typed campaign ledgers
remain separate follow-ups; do not fabricate them from legacy messages.

Implemented and verified as AA-VAE-033/034. Detailed RED/GREEN, independent
review, clean-room evidence, and validation limitations are recorded in
`logs/verification-log.md`. Phase 5 remains `in_progress`.

#### Verified slice - production public EVAS observation (2026-08-30)

Brief: adapt the existing sandboxed public EVAS execution into canonical,
candidate/profile-bound observations. Preserve mini-swe's default Bash surface;
this is an opt-in environment API, not activation of a deferred domain tool.

Acceptance / KPI:

- freeze the r53 manifest, public inputs, declared command, EVAS 0.8.7 runtime,
  candidate declarations, limits, and campaign identity before validation;
- execute only the declared public command in the existing isolated runtime;
- bind feedback to the exact candidate and attempt; reject authority/input
  drift and refuse validation after submission freeze or final reservation;
- expose only public process diagnostics, never a task-correctness verdict;
- prove canonical observation/trajectory binding using real execution, then a
  Docker r53 smoke; keep legacy regression behavior unchanged.

Scope/ownership: main coordinator owns
`operations/calibration_pilot/public_validation.py`, the minimal inspection
seam in `mini_swe_vabench.py`, focused `test_agent_harness_*` tests, smoke/CI,
and shared records. Parallel exploration/review is read-only. Base is
`3b0a62a9e6`; no delegated writers or new dependencies.

Execute one behavioral RED/GREEN at a time, review the adapter independently,
then add integration/smoke coverage and update the migration ledger in focused
GREEN commits. Preserve all failed-run evidence outside the repository.

Non-goals: no hidden checker, historical feedback oracle, new model tool,
model API campaign, r53/EVAS change, Spectre run, full CLI switch, or fabricated
conversion of legacy traces. Pre/post hashes detect drift but do not prove
transactional rollback or a hostile concurrent-process security boundary.
Stop if execution requires private fixtures, changes scoring semantics, or
cannot preserve the existing isolation/capability contract.

Implemented as AA-VAE-035. The canonical trajectory test uses an explicit
test-only routing seam, not a new production model tool. The real Docker smoke
checks the public adapter, one-call budget, and matching freeze hash; the
existing bound-final smoke remains a separate chain. Full campaign wiring,
complete trajectory content/typed result joins, Testbench support, and retry
lineage remain open. Phase 5 stays `in_progress`; no reasoning/evolution
backend implementation or baseline-quality claim is implied.

#### Active slice - native episode / production final result join (2026-08-30)

Brief: compose the existing controller and trusted replay into an opt-in Python
entry point. Persist its native trajectory and validated scored-result artifact
without translating incomplete legacy traces or changing campaign defaults.

Acceptance / KPI:

- freeze public/final profile and backend/tool identities before policy entry;
- reserve one fresh runtime attempt before generation; never resume it in place;
- accept only the controller's frozen submission for the existing bound replay;
- read and verify the published sidecar receipt, then join the real trajectory,
  submission, profiles and judgment into an immutable result artifact;
- keep unscored failures visible without fabricating a zero or scored row;
- prove public feedback -> submission -> final replay -> result join in one
  deterministic r53 Docker smoke; final output never reaches the policy;
- retain legacy mini-swe, r53, EVAS 0.8.7 and all deferred tool decisions.

Main owns `operations/calibration_pilot/native_episode.py`, the minimal reusable
result-store and legacy reentry gates, focused tests, CI and shared records.
Base: `4879ee64bb`. Native subagents map/review only; no delegated writes.
Implement one RED/GREEN behavior at a time, independently review, and publish
focused GREEN commits only to the BucketSran fork.

The smoke may use explicitly test-only public-tool dispatch; this does not
approve or install `run_evas` in a production model registry. The entry point
accepts trusted caller-supplied policy/environment components; it is not a
full CLI/backend launcher, model API experiment, raw trace archive, aggregate
ledger, retry coordinator, or proof of hostile-host isolation. Existing hash
events do not imply full replayable model/tool content. Authority/provenance
and exclusive workspace ownership remain coordinator responsibilities.

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
