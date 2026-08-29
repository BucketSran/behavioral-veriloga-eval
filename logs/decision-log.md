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
