# Remaining native harness functionality

Date: 2026-08-30. Base: `0f014c39e1016e8c6877ff7c48dbddb2733d8f93`.
Status: approved implementation in progress; no completion claim yet.

Progress: AA-VAE-043 native Testbench authority and three-form nine-cell
connectivity are locally verified (2026-08-30). The stronger invocation identity
gate also fixed cwd-dependent telemetry hashing. Remaining items below are not
implicitly completed. AA-VAE-044 evidence/metering is now runtime-integrated and
locally verified. AA-VAE-045 now integrates opt-in infrastructure retry with
all-attempt costs and nine-cell Docker verification. Reasoning and Evolution
still require shared wiring.

## Brief and scope

Layer: behavioral-veriloga-eval. The user approved closing the remaining
functionality discussed after AA-VAE-042: native Testbench, attempt recovery,
metering/evidence, Reasoning, Evolution, result generation and experiment gates.
Reuse the existing controller, exporters, model transport, Bash environment,
authority profiles, immutable stores, evolution reducers and score reader.
This is not permission to redesign r53 or the evaluator.

Non-goals: r53/EVAS changes, legacy default replacement, domain/RAG/waveform
tools, SFT/RL, Spectre runs, new dependencies, private AlphaApollo material,
old-worktree changes, or silently restoring compacted historical assets.
Paid model execution waits for an explicit model/service and budget. Deterministic
provider and real Docker/EVAS tests may proceed without that input.

## Acceptance and KPIs

1. Native Testbench supports all three conditions. Only reference-DUT public
   execution is exposed; certified faults/checkers stay final-only. Nine
   representative form/condition cells have joined trajectory/freeze/sidecars.
2. Infrastructure retries use frozen policy, new attempt IDs and clean exports;
   no candidate/protocol/agent-deadline or score-driven retries, no overwrite,
   no silent resumption, no duplicate counted terminal result.
3. Runtime-owned model/tool/evaluator counts and resource evidence are joined;
   unavailable provider metrics are explicitly unknown, not invented zeroes.
   R53's wall-clock stopping policy is unchanged by token accounting.
4. Sensitive evidence remains private and immutable. Versioned public exports
   allowlist safe fields and bind source hashes without exposing messages,
   secrets, hidden diagnostics or terminal outcomes to model memory.
5. A distinct Reasoning policy uses existing structured proposal/controller
   contracts and API/local-compatible transport. It is runnable, not just a
   backend label, and has matched-capability differential tests.
6. Evolution executes independent multi-model branches under frozen limits,
   consumes immutable public round snapshots, reuses deterministic reducers,
   records candidate ancestry and total costs, and judges only the selected
   terminal submission. Completion order never changes the information set.
7. Record-level ledgers and generated comparisons/claim indexes preserve the
   complete schedule, null infrastructure scores, attempt selection and source
   hashes. Single-trajectory and evolution estimands remain separate.
8. Focused tests, real integration gates and independent review validate each
   published slice. Real model quality and full-r53 results require actual runs,
   not deterministic smoke success.

## Execution sequence

1. Native Testbench public authority and launcher/campaign support; nine-cell
   smoke and leakage/regression gates (AA-VAE-043).
2. Infrastructure attempt orchestration and immutable attempt-selection
   receipts; crash/discard handling and denominator joins.
3. Unified metering, private evidence capture and versioned safe exports.
4. Reasoning policy and concrete launcher/campaign integration.
5. Candidate-only branch execution, public validation, multi-model round
   orchestration and selected-submission-only final replay.
6. Result ledger, paired/cost/deadline summaries, claim index and pilot entrypoint.
7. Comprehensive applicable tests, independent review, hosted CI and authorized
   pilot. Keep model-quality evidence separate if credentials/budget are absent.

Each slice follows one behavioral RED test -> minimal GREEN implementation ->
next behavior -> review/refinement -> focused commit -> fork-only publication.
Independent leaf modules may be implemented in parallel only after exact file
ownership is recorded; shared runtime wiring and all publication stay with main.

## Risks and stop conditions

- Final evidence is not public feedback, including during retries/evolution.
- Testbench final replay and public reference execution must not share hidden
  input mounts, candidate selection metrics or mutable workspaces.
- An incomplete/corrupt attempt is preserved and must not be treated as success.
- No new terminal or denominator semantics are inferred from process exit code.
- Stop affected work on ownership drift, evaluator/release mutation, missing
  experimental authority, or a design choice that changes the agreed estimand.
- Record partial closure honestly: infrastructure implementation, deterministic
  connectivity and real model evaluation are distinct acceptance levels.

## Required records

Exact files, public source references, RED/GREEN commands, evidence locations and
hashes, review findings and publication status belong in the migration feature
notes and decision/verification logs. Native writers return unstaged changes;
the coordinator alone integrates and commits. Outputs remain under the existing
ignored `benchmark-vabench-release-v4/reports/` tree.
