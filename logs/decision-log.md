# Decision Log

## 2026-08-29 - Fork-first development

- Continue development and audit on the `BucketSran` forks.
- Treat `Arcadia-1` repositories as upstream sources, not direct write targets.
- Synchronize fork `main` before creating new audit branches.
- Preserve existing local feature branches and dirty worktrees; use clean
  worktrees for the new evaluation-closure effort.

## 2026-08-29 - Two-repository vaEVAS boundary

- `behavioral-veriloga-eval` owns benchmark/evaluation policy and clean-room
  execution.
- `EVAS` owns simulator/compiler/runtime behavior.
- Cross-repository changes require an integration failure that identifies which
  side of the contract is responsible.
- Shared AlphaApollo insights remain methodological only; no confidential code,
  services, datasets, or artifacts cross into vaEVAS.

## 2026-08-29 - Pinned evaluator execution contract

- Pin formal evaluator execution and the evaluator image to Python `3.11.13`,
  with `evas-sim==0.8.7`, canonical engine `evas-rust`, Rust
  ABI `20260718`, and core version `0.2.4`.
- Bind scoring to an explicit installed EVAS command and disable persistent
  workers by default. Source-tree auto-discovery is not acceptable evidence for
  a formal run because an unbuilt sibling checkout can shadow the installed
  wheel without establishing a simulator defect.
- Treat live environment identity and every per-run `evas_identity.json` as
  required evidence. Missing, unloadable, or mismatched identities are
  infrastructure failures rather than candidate failures.

## 2026-08-29 - Claim and denominator boundary

- A one-task clean-room smoke may claim only pipeline connectivity. It never
  supports a model-quality or aggregate benchmark-score claim.
- Formal model-score scope requires the canonical repository roster, the
  complete unfiltered non-empty frozen `counted_in_score=true` denominator,
  clean source identity, Python exactly `3.11.13`, hashed inputs and results,
  terminal evidence for every row, the same verified EVAS command,
  persistent-worker mode disabled, and no infrastructure failures.
- Candidate compile, testbench compile, and simulation-correctness failures are
  valid zero-score outcomes and stay in the denominator. Infrastructure or
  unknown failures block the claim.
- Pinned strict EVAS is the formal judge. Spectre remains optional,
  non-blocking parity evidence.

## 2026-08-29 - EVAS change decision

- The installed package completed task-014 hidden scoring with all component
  scores equal to `1.0` and a loadable matching Rust core.
- The only observed failing route was evaluator-side source-tree shadowing by
  an unbuilt sibling EVAS checkout. This is an environment-selection defect,
  not evidence of an EVAS compiler, simulator, or package defect.
- Therefore make no changes to the EVAS audit fork in phase one.

## 2026-08-29 - r53 three-arm clean-room smoke

- Freeze the active benchmark/evaluator closure target as
  `benchmarkv4-r53` + `evas-sim==0.8.7`; do not route new closure work through
  the older v3 empty-denominator path.
- Add `scripts/run_v4_r53_clean_room_smoke.py` as a deterministic
  harness/evaluator smoke, not as a model baseline replay.
- The smoke covers one r53 task across the matched `OneShot`,
  `Agent-No-EVAS`, and `Agentic` arms, then joins trajectory evidence to the
  frozen submission tree and an EVAS trusted-replay sidecar.
- `Agent-No-EVAS` must show zero in-loop EVAS calls. `Agentic` may record
  public feedback events, but task correctness still comes only from final
  strict EVAS trusted replay.
- The smoke claim scope is only
  `single_task_three_arm_clean_room_pipeline`; model-score and aggregate
  benchmark claims remain disallowed.
- No simulator/compiler/package defect was observed, so EVAS remains read-only
  and Spectre parity is not activated.

## 2026-08-29 - Frozen r53 smoke baseline

- Freeze all new closure work to VABench r53 at
  `7b5616dc52195ec275ec6d21c71d7763613702cd` and `evas-sim==0.8.7` at
  `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
- Treat both frozen dependencies as read-only. Harness, trajectory, evidence,
  sidecar, and CI changes belong only in the behavioral-eval repository.
- The first r53 milestone is a deterministic integration smoke, not a replay
  of paper baseline scores. Its maximum claim is pipeline connectivity and
  evidence integrity.
- Cover `One-shot`, `Agent-No-EVAS`, and `Agentic+EVAS` with fresh isolated
  state and code-enforced capability differences.
- Use strict EVAS 0.8.7 trusted replay as the smoke judge. Spectre remains out
  of scope unless the evaluator changes or an explicit external protocol
  activates the parity gate.

## 2026-08-29 - r53 smoke evidence and score authority

- Reject evaluator-side solution copying as a smoke implementation: the
  deterministic candidate must be derived only from the public contract and
  must traverse the same `run_cell` entrypoint as a real episode.
- Treat EVAS 0.8.7 sidecars as development-only score authority. A successful
  smoke means the runner, isolation, trajectory, freeze, and scorer join is
  valid; it does not require the intentionally incomplete candidate to pass.
- Preserve paper-facing Spectre authority separately. Neither this smoke nor an
  EVAS sidecar permits a model-performance or paper-result claim.
- Make submission freeze append-only, require structured trusted-replay output,
  and keep closure scoring out of the frozen campaign result by using an
  independent content-addressed sidecar.
- Classify the initially missing local Rust core as an evaluator-environment
  failure, not an EVAS defect. Build evidence in a temporary target directory;
  keep the EVAS fork unchanged.

## 2026-08-29 - Active r53 authority supersession and review hardening

- For the active r53 project, EVAS 0.8.7 is the development smoke, public
  feedback, and fast-scoring authority. It is not paper-facing final-result
  authority. This supersedes the earlier same-day statement that described
  strict EVAS as the formal judge and Spectre as merely optional.
- A paper-facing score remains gated on the separately declared private
  Spectre protocol and its evidence joins. No result from the deterministic
  r53 smoke may be promoted to a model or paper claim.
- Canonicalize multi-file submission manifests before freezing and hashing;
  declaration order is not semantic and must not create false drift.
- Require `immutable=true` in the machine-checkable schema for every available
  frozen submission, and keep the protocol regression surface in closure CI.

## 2026-08-29 - AI-native harness evolution direction

- Keep the existing mini-swe backend and add AlphaApollo reasoning as a
  differential backend rather than replacing mini-swe.
- Add AlphaApollo multi-model evolution as a separately named and budgeted
  condition. The first version uses different models in parallel, immutable
  round feedback snapshots, and deterministic public-validation-based
  candidate selection.
- Learn reasoning, memory, and evolution structure from public AlphaApollo;
  learn workspace, shell, editing, sandbox, and event-loop patterns from public
  coding-agent frameworks. Do not adopt any framework wholesale.
- Keep sandboxed Bash as a first-class coding tool. Use JSON/native function
  calls as the canonical action/observation protocol; do not replace it with
  XML plus regex parsing in the formal path.
- Add structured candidate, public EVAS, waveform, frozen-documentation RAG,
  and submission tools behind one capability and budget registry. Treat helper
  tools as separate interventions where they can affect results.
- Separate model-visible public validation from the model-invisible final
  test. If a final outcome drives another generation or selection step, that
  invocation is a verifier call and cannot remain the terminal score for the
  same episode.
- For r53 Testbench tasks, preserve reference-DUT validation versus
  evaluator-only certified faults. For r53 DUT/bugfix tasks, describe the
  current protocol as shared-stimulus with a held-out checker, not a fully
  held-out test set.
- Keep r53 and EVAS 0.8.7 immutable. A future disjoint DUT/bugfix stimulus
  profile requires a named successor protocol/release, not an in-place r53
  edit.
- The untracked `runners/agent_harness/` prototype is paused evidence, not an
  approved production architecture. Reconcile its useful tests and split its
  conflated verifier authority before any commit or integration.

## 2026-08-29 - Domain-tool deferral and coding-agent transfer mapping

- Supersede the earlier same-day wording that could be read as approving a
  fixed candidate/EVAS/waveform/RAG/submission tool inventory. Preserve only a
  capability registry and non-callable extension points until each proposed
  tool is discussed and receives an explicit accepted/rejected/deferred
  decision, evidence contract, and ablation requirement.
- Map SWE-agent/mini-swe to the model-facing agent-computer interface,
  observation normalization, terminal submission, and mini-swe compatibility
  adapter.
- Map OpenHands to ordered Action/Observation events, an event-derived bounded
  controller, isolated runtime ownership, and pre-dispatch capability checks.
- Map Aider only as a future design input for atomic edit formats, diffs, and
  content-addressed candidate checkpoints; do not adopt automatic Git commits
  or repository-wide context by default.
- Map Codex CLI to sandbox/capability policy, explicit denial, atomic edit
  separation, and tool-policy evidence; do not adopt interactive approval,
  desktop, or general plugin/MCP surfaces into formal cells.
- Treat all coding-agent sources as bounded pattern references, not runtime
  dependencies. Production transfer requires named landing files, RED tests,
  claim impact, and rejected upstream assumptions in the migration ledger.

## 2026-08-29 - Incremental harness commit policy

- Publish the harness migration as multiple focused, independently reviewable
  and revertible commits rather than one repository-wide implementation
  commit.
- Keep planning/contract changes separate from runtime implementation when
  practical. Split controller/state, backend adapters, capability policy,
  validation/final-test authority, evolution, and evidence/results into their
  own verified slices.
- RED tests remain a local development step. Do not push a knowingly broken
  intermediate state to `main`; every published commit must keep the supported
  path and CI-safe checks green.
- Stage and inspect only the intended files for each slice, record focused
  verification with the corresponding change, and push only to the writable
  BucketSran `origin`, never Arcadia-1 `upstream`.

## 2026-08-29 - Phase 0 generic harness disposition

- Retain and rework the paused `agent_harness` prototype instead of deleting
  it or committing it unchanged. Preserve its useful freeze-before-score,
  cleanup-incident, retry-lineage, and tamper-evident trajectory behavior.
- Replace generic `Verifier` authority with an environment-owned,
  model-visible `PublicValidator` and a terminal-only, model-invisible
  `FinalJudge`. A final judgment must bind the exact frozen submission hash.
- Replace stringly typed actions and observations with immutable, versioned,
  structured records carrying backend/tool/candidate/budget identities and
  canonical payload hashes.
- Materialize protocol, infrastructure, and budget failures in
  `EpisodeResult`; keep cleanup failure as an orthogonal incident.
- Do not connect the package to production runners in Phase 0. Formal schemas
  and mini-swe compatibility remain separate, reviewable commits.

## 2026-08-29 - Judge authority supersedes earlier same-day wording

- Supersede earlier same-day language that could be read as making private
  Spectre the routine paper-facing score authority.
- The current default development and evaluation judge is strict EVAS 0.8.7
  trusted replay, with every claim explicitly bound to `judge_engine=evas`,
  the frozen submission hash, checker/runtime identity, and score sidecar.
- Private Spectre is conditional: it is required when EVAS code/version,
  compiler behavior, simulator semantics, ABI, or packaging changes, and when
  an explicitly named external or paper protocol demands Spectre-backed
  evidence.

## 2026-08-30 - Harness evolution phase-1 contract split

- Freeze tool capability, public-validation authority, final-test authority,
  memory snapshot, candidate lineage, and evolution manifest as separate
  protocol contracts before any production runner integration.
- Keep proposal syntax allowlists separate from execution authority. A tool may
  be syntactically accepted by a backend proposal parser and still be rejected
  by the trusted registry when it is unknown, reserved, final-only, disabled for
  the condition, or missing a handler.
- Keep future vaEVAS domain tools as `reserved` descriptors until each tool has
  an explicit semantics, evidence policy, budget impact, and ablation decision.
- Treat public EVAS validation and final EVAS trusted replay as separate
  authorities even when both use `evas-sim==0.8.7`. Public validation may
  produce model-visible feedback and episode-local public memory; final replay
  is post-freeze, trusted-only, cannot select candidates, cannot repair, and
  cannot re-enter model generation.
- Model-visible memory may contain only public candidate summaries, public
  validation, and public tool observations. Final judgments, final score
  sidecars, private checker evidence, and trusted events are forbidden memory
  sources.
- Candidate lineage uses one artifact parent plus multiple influence
  references. This preserves a real edit parent while still recording
  cross-candidate inspiration from shared public feedback.
- Round-based evolution selection is deterministic over public evidence:
  public metrics first, then `candidate_tree_sha256`, then `candidate_id`.
  Completion order, model identity, and final score are not selection inputs.
- This contract slice does not implement a new AlphaApollo backend, does not
  alter mini-swe, does not alter r53, does not alter EVAS, and does not trigger
  Spectre parity.
- EVAS-backed results may not be described as Spectre-backed or
  simulator-independent unless that conditional parity protocol was executed
  and joined to the same frozen submissions.

## 2026-08-30 - Canonical action/observation wire authority

- Freeze `vaevas-action-v1` and `vaevas-observation-v1` as strict internal wire
  documents before adding backend adapters or provider parsers.
- Treat the state constructor/serializer as the authority that computes
  argument and payload hashes. JSON Schema validates document shape and digest
  syntax; it does not claim to recompute or prove digest binding.
- Keep `tool_name` extensible at the wire layer. Tool existence, condition
  eligibility, visibility, budget, and state effects belong to a later
  capability registry and fail-closed dispatcher.
- Reject inputs that cannot have a canonical JSON representation before they
  enter the trajectory: non-object roots, non-string object keys, non-finite
  numbers, and invalid budget deltas.
- Keep this slice disconnected from production mini-swe/r53 runners. Native
  tool-call and strict-JSON normalization remain the next independent Phase 1
  protocol slice.

## 2026-08-30 - Untrusted proposal and trusted action boundary

- Normalize provider-native function calls and strict standalone JSON through
  one protocol boundary before controller or environment execution.
- Limit model-owned fields to `tool_name` and `arguments`. Inject action ID,
  backend identity, candidate hash, and accepted syntax-level tool names from
  a trusted envelope; compute the argument digest in `AgentAction`.
- Require exactly one native function call. Reject malformed/fenced/repaired
  JSON, duplicate keys, non-finite constants, missing or extra fields, and
  unknown tool names without executing any tool.
- Treat the envelope tool-name set as a parser allowlist only, not the future
  capability registry. It does not approve domain tools or define condition,
  visibility, budget, or state-effect policy.
- Keep legacy artifact regex and `submit_artifacts` repair behavior outside the
  formal action protocol. The future mini-swe adapter should reuse the existing
  `BASH_TOOL` and environment rather than duplicate execution semantics.

## 2026-08-30 - Backend profile owns identity, not campaign values

- Add `vaevas-backend-profile-v1` to distinguish mini-swe, AlphaApollo
  reasoning, and round-based evolution by backend identity, inference mode,
  proposal compatibility, model-interface flags, and state scope.
- Keep model/provider/snapshot, decoding, budget, release, condition, concrete
  tool exposure, runtime, and judge values in campaign/environment contracts.
  The backend profile declares only the external contract names it requires.
- Require evolution profiles to name roster, round-budget, feedback-scope,
  selection, and final-submission contracts without embedding their values.
- Forbid cross-task and cross-condition state; memory remains none or
  episode-local.
- Content-address schema-validated profiles with canonical SHA-256. The hash
  helper does not replace schema validation; campaign/result joins are later
  work.

## 2026-08-30 - Tool registry owns execution authority

- Treat proposal `accepted_tool_names` as a syntax gate only. A normalized
  action receives execution authority only after `ToolRegistry` resolves an
  active, condition-eligible descriptor.
- Freeze argument, observation, evidence, budget, state-effect, candidate-
  effect, handler, and visibility contracts into the resolved capability and
  its content hash.
- Keep domain-tool namespaces reserved and non-callable until a separate
  accepted design record and ablation exist.
- Keep final judging outside the tool registry. The public EVAS invocation may
  later be represented as a model-visible validation capability, while final
  trusted replay remains terminal-only authority after submission freeze.
- Reject malformed descriptors at both JSON-schema and operational registry
  boundaries; do not rely on parser allowlists or caller-side validation for
  runtime safety.

## 2026-08-30 - Phase 1 contracts closed before runtime integration

- Freeze public-validation and final-test authority profiles as separate
  schema families even when both currently use r53 and EVAS 0.8.7. Public
  validation may be model-visible and may feed episode-local public memory;
  final trusted replay remains post-freeze, trusted-only, non-adaptive, and
  may replay only for infrastructure failures against the same frozen
  submission with a fresh judge attempt.
- Freeze evolution memory as public-only. Candidate summaries, public
  validation, and public tool observations are allowed; final judgments, final
  score sidecars, private checker evidence, and trusted events are forbidden.
- Freeze candidate lineage as one artifact parent plus optional influence
  references. Failed mutations create explicit lineage records without
  changing the candidate tree hash; frozen candidates are terminal.
- Freeze the first evolution manifest/reducer contract before implementing a
  real AlphaApollo backend. Round snapshots are invariant to provider
  completion order, final/trusted feedback is rejected, and selection uses only
  public metrics followed by `candidate_tree_sha256` and `candidate_id`.
- Phase 1 is now a protocol-contract closure. Runtime dispatch, mini-swe
  adapter parity, real multi-model scheduling, CI wiring, and result-ledger
  joins move to subsequent phases.

## 2026-08-30 - Phase 1 hardening keeps schemas generic and instances frozen

- Keep authority and evolution schemas reusable across later benchmark and
  evaluator releases; freeze the current experiment instance to r53 + EVAS
  0.8.7 through profile/manifest content and regression fixtures rather than
  hard-coding those values into the schema vocabulary.
- Treat final judging as a separate post-freeze authority, not a
  `final_judge_only` ordinary tool lifecycle. The ordinary registry accepts
  only active callable capabilities and reserved non-callable placeholders.
- Make retry isolation absolute: a retry records its parent attempt for audit
  but starts at round 0 with empty memory and no memory parent.
- Make persisted evolution snapshots self-verifying. Reload must validate the
  manifest and snapshot hashes, strict roster barrier, retry contract,
  canonical candidate ordering, exact public metrics, and recomputed winner
  before a prior incumbent can be reused.
- Keep this work at the protocol layer. Production adapter integration, CI
  wiring, real multi-model scheduling, and result-ledger joins remain later
  work and are not implied by Phase 1 completion.
