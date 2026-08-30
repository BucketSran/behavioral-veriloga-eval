# vaEVAS Development Work Ownership

Updated: 2026-08-30

## Brief, Acceptance, And Scope

The user-facing main coordinator, task
`01a04c45-1431-7001-b859-978f3cf96201`, owns integration and Git publication for
`/Users/bucketsran/Documents/TsingProject/vaEVAS-next/behavioral-veriloga-eval`.
This register governs coding work, not AlphaApollo model/evolution scheduling.

Acceptance KPIs: one active writer per file; zero delegated index/history or
push operations; both historical tasks have explicit dispositions; shared
records and final verification belong to the coordinator. This coordination
slice changes documentation only, not runtime behavior, schemas, or scores.

Frozen boundaries remain r53 + EVAS 0.8.7, fork-only publication, and no edits
to the old `/Users/bucketsran/Documents/TsingProject/vaEvas` worktrees. The EVAS
checkout is read-only; this register does not authorize an evaluator change.

## Current Ownership

`main coordinator` means the task identified above, not whichever task happens
to be checked out on Git branch `main`. New tasks do not become coordinators
simply by reading this file. Any future coordinator transfer must be explicit
and recorded here before the new coordinator starts writing.

| Surface | Current owner | Delegated write assignment |
| --- | --- | --- |
| Shared Git index, branches, integration, commits, and fork pushes | main coordinator | none |
| `AGENTS.md`, `plans/`, `logs/`, migration docs, schemas, CI | main coordinator | none; reviewers return suggested changes |
| Shared harness contracts/state/controller/tool registry, package exports, and their tests | main coordinator | none; old dispatch task is closed |
| `runners/agent_harness/result_store.py` and `tests/test_agent_harness_result_store.py` | main coordinator | none; historical store slice is integrated |
| Production opt-in final replay/scorer receipt path and its tests | main coordinator | none; the bounded receipt integration is verified |
| Production public-validation adapter and campaign wiring | main coordinator | none; bounded native three-form three-condition campaign locally verified; retry remains pending |
| Trajectory/result joins, backend adapters, evolution/memory/lineage, and their tests | main coordinator | none; assign exact leaf files before parallel implementation |
| All other tracked files not explicitly assigned below | main coordinator | none |

Independent
review/advice may run in parallel on explicitly scoped reads. Shared-interface
and documentation suggestions are returned to the coordinator, not written by
reviewers. File ownership may be split for later bounded leaf implementations;
integration and shared-surface ownership do not transfer with a leaf task.

## Historical Task Disposition

| Task | Previous responsibility | Disposition under this agreement |
| --- | --- | --- |
| `01a04f33-6d31-7e22-ba8d-964f26c41471` | Immutable score-sidecar store closeout | Completed. Reuse commits `a8fa0aba2a` and `fdea07dc41`; do not reimplement, recommit, or resume a writing lane. Subsequent production integration is already in `439b97f7a5`. |
| `01a04ec3-d511-79e2-a565-6984d33406d1` | Capability-aware dispatch/controller slice | Execution ended without its own commit after concurrent-write conflict. Its remaining interface question transfers to the coordinator for reassessment against current code; do not replay its withdrawn partial patch. |

The second task requested `Observation | classified rejection`, whereas the
current environment contract returns `EnvironmentStep | ToolExecutionRejection`.
This is an unresolved design comparison, not authorization to replace an
already integrated interface or proof that controller functionality is absent.
Any change needs a separate regression-backed slice.

Evidence: both specified local task logs end in `task_complete`. Direct desktop
task-control tools were unavailable during this update; no task was remotely
interrupted, archived, or notified. This register supersedes old write
assignments for future work but is not a cross-process lock.

## Assignment And Handoff Protocol

Before assigning a writing lane, the coordinator adds one entry containing:

- task ID/name, named owner, and status (`active`, `handed_back`, or `closed`);
- exact existing/new file paths and the observed base commit;
- explicit non-owned files, including shared interfaces and all Git operations;
- approved behavior, RED/GREEN acceptance tests, and isolated test-output paths;
- handoff requirements: changed files, test commands/results, unresolved risks,
  observed external edits, and confirmation that writing has stopped.

The coordinator checks that active file lists do not overlap before dispatch.
Delegates do not create their own assignments or enlarge their file lists.
On overlap, base/index drift, or unexpected edits, suspend the affected writes
and report upward; preserve all other work rather than rolling it back.

Integration sequence:

1. Receive handoffs and confirm all delegated writers have stopped editing.
2. Inspect each diff and reconcile shared API/schema changes in the main task.
3. Run focused tests and applicable integration checks on the stable tree;
   obtain independent read-only review. Revalidate if code changes afterward.
4. Update the plan, migration ledger, and decision/verification logs centrally.
5. Stage exact files, inspect staged diff and secrets, commit a coherent slice,
   verify the fork target, and push only to BucketSran `origin`.
6. Record evidence and close the assignment before reallocating its files.

## Immediate Follow-up

### Remaining harness functionality (2026-08-30)

Status: `active`; base `0f014c39e1016e8c6877ff7c48dbddb2733d8f93`.
Scope/KPIs: [controlled plan](remaining-harness-closure.md). This newer user
authorization supersedes the earlier slice's no-further-implementation closeout.
Main owns native Testbench integration in calibration `public_validation.py`,
`run_native_mini_swe.py`, `run_campaign.py`, the v4 campaign wrapper, related
existing tests, new `tests/test_agent_harness_native_testbench.py`, the nine-cell
smoke, all shared contracts/schemas, CI, docs/logs and Git operations.
Integration evidence additionally authorizes main's minimal `mini_swe_vabench.py`
candidate-root repair and production-public-validation regression: no EVAS
compiler/simulator/package changes are involved.

Read-only advisers: `tb_surface_map`, `retry_evidence_map`,
`reasoning_evolution_map`, `alpha_public_reference`. No write/Git authority.

Leaf assignment `reasoning_policy_impl`: exact ownership of new
`runners/agent_harness/backends/reasoning.py` and new
`tests/test_agent_harness_reasoning_backend.py` only. Implement a single-action
episode-local policy through existing client.complete and proposal contracts;
no model transport dependency, tool activation, package export or launcher edit.
Accept native calls/strict JSON under a frozen format, preserve request/output
metadata and explicit missing usage, and test public-only history/failure.

Leaf assignment `evidence_export_impl`: exact ownership of new
`runners/agent_harness/evidence_export.py` and new
`tests/test_agent_harness_evidence_export.py` only. Implement validated trajectory
and launcher-event safe export plus runtime usage normalization; preserve source
hashes and identity, exclude all raw content by allowlist, report unknown metrics.
Do not change schemas, stores, launcher, controller, scorer or shared docs.

Both leaf assignments are `active` only when dispatched by main. Follow vertical
TDD; no index/history/push, no other file writes, no old-worktree/private reads,
no EVAS/r53 changes, no dependencies. Return changed files, RED/GREEN evidence,
risks and stopped-writing confirmation. Main integrates after handback/review.

Leaf assignment `reasoning_policy_impl` follow-up `attempt_sequence`: `active`
on base `d5d656161b` after the reasoning leaf handback. Exact new files:
`runners/agent_harness/attempt_sequence.py` and
`tests/test_agent_harness_attempt_sequence.py`. Build a bounded fresh-attempt
coordinator with frozen policy, EpisodeContext.next_attempt lineage, exclusive
immutable journal/selection records and a caller-owned execution callback.
Only explicit pre-final infrastructure dispositions permit retry; never inspect
scores to retry, reuse prior candidate/memory or overwrite an existing root.
The callback/runtime wiring and score reader remain main-owned. Vertical TDD,
no Git/shared/dependency/evaluator/release edits; stop writing at handback.

### Native DUT/bugfix three-arm campaign (2026-08-30)

Status: `closed`; base `24f2b834b012271af8d05221cc6e4855e2488f72`.
Both leaf writers handed back and stopped. Main integrated their changes,
repaired review/integration findings and ran the six-cell real Docker gate.
Independent reviews have no substantive blocker; diagnostic gaps are logged.
The coordinator also owns the final wrapper root-reservation regression/fix in
`runners/run_benchmarkv4_campaign.py` and the existing native dispatch test file;
the campaign reviewer checks it read-only. No leaf writing lane is reopened.
Fork publication and hosted verification are complete at runtime commit
`c2da249c8a`. All triggered workflows passed. Main owns only the final evidence
documentation closeout here; no further implementation lane is activated.
Scope/KPIs/stop conditions: [controlled plan](native-three-arm-campaign.md).
The main coordinator owns all shared contracts/schemas/exports, native episode
composition, CI, smoke integration, plans/logs and migration notes. Main-owned
runtime/test files for this slice: `runners/agent_harness/result_artifact.py`,
`authority_profiles.py`,
`result_store.py`, `controller.py`, `trajectory.py` (under that package),
`operations/calibration_pilot/native_episode.py` (under v4),
`schemas/vaevas-result-artifact-v2.schema.json`,
`tests/test_agent_harness_absent_public_authority.py`,
`tests/test_agent_harness_native_campaign_smoke.py` (new),
`scripts/run_v4_r53_clean_room_smoke.py` (public fixture extension), and existing shared
contract/CI tests as required. No evaluator or sealed-release writes.

Delegated leaf assignments (only the named files; paths beginning operations or
runners/run_benchmark are under `benchmark-vabench-release-v4/`):

- `native_conditions_impl`: `handed_back`; owns
  `operations/calibration_pilot/run_native_mini_swe.py` and
  `tests/test_agent_harness_native_conditions.py` (new). Implement/test OneShot
  and No-EVAS with the existing Agentic path preserved. No shared contract,
  schema, campaign, legacy runtime, documentation or Git writes.
- `native_campaign_impl`: `handed_back`; owns
  `runners/run_benchmarkv4_campaign.py`,
  `operations/calibration_pilot/run_campaign.py`,
  `operations/calibration_pilot/score_campaign.py`, and
  `tests/test_agent_harness_native_campaign_dispatch.py` (new). Add explicit
  native routing, frozen campaign identity, terminal accounting and read-only
  strict native summary. Preserve default legacy and do not edit launcher/shared
  contracts/schema/docs/Git. Coordinate the absent-profile reader contract.

Each owner uses vertical RED/GREEN, only isolated test output under a fresh
temporary directory or existing ignored reports root, and returns changed files,
exact tests/results, external edits, remaining risks and a stopped-writing
confirmation. No index/commit/push authority is delegated. Read-only advisers
`docs_publication_review` and `native_absence_contract_review` have no writes.
Main integrates only after handoff and independent review of the stable tree.

### Native campaign evidence bridge (2026-08-30)

Status: `closed`; base `7425d70b728be41f15235f896a5e5be87b31747e`.
Main owns `operations/calibration_pilot/score_campaign.py` (under v4),
`scripts/run_v4_r53_clean_room_smoke.py`, new
`tests/test_agent_harness_native_campaign.py`, smoke/CI tests,
`.github/workflows/evaluator-closure.yml`, calibration README, AA-VAE-039,
feature ledger and shared plans/logs. No delegated writes or Git authority.
`native_campaign_reuse_map` and `native_campaign_design_review` are read-only.

Brief/KPIs: reuse the existing native launcher and score summarizer; exactly
one row per scheduled cell, with explicit backend routing and terminal
disposition. Read native artifacts without rescoring or mutating generation
evidence; reject broken joins. An unscored failure has no fabricated score.
Prove deterministic three-arm Docker connectivity using legacy OneShot and
No-EVAS plus native Agentic, not native parity or model quality. Preserve the
known local legacy timeout-test gap. Native No-EVAS, full campaign CLI, retries,
Testbench, model experiments, Reasoning/Evolution and domain tools are deferred.

Plan: scope commit; vertical RED/GREEN result join and denominator checks;
smoke wiring; independent code/architecture reviews; focused and real Docker
verification; separate verified commits and fork-only push. Use fresh test
outputs under existing ignored `benchmark-vabench-release-v4/reports/`.

Implementation and read-only reviews are complete: code APPROVE, architecture
WATCH for the bounded private-path reader dependency; combined COMMENT, no
blocker. Final local focused checks are 61 passed / 3 skipped, plus the
derived-reference authority check and real Docker three-arm PASS. The broad
legacy one-second timeout failure remains recorded. Scope, implementation and
validation docs are published through `a86586b869` on fork main. All three
triggered hosted workflows pass; Evaluator Closure reports 660 passed / 10
skipped and both mixed-native and legacy Docker smokes pass. This final
coordinator-only record closes the assignment; no delegated writer is active.

### Repository hygiene slice (2026-08-30)

Status: `closed`; implementation and independent review are complete. The final
coordinator publication records only hosted verification and this disposition.

Brief: make current documentation unambiguous and retire only this coordinator's
unused, merged local branch. This is documentation/metadata maintenance, not a
runtime, evaluator, release, or experiment cleanup.

Main owns `README.md`, `docs/README.md`, `docs/REPO_LAYOUT_POLICY.md`, historical
banners in the nine top-level legacy guides, `plans/current-plan.md`, its dated
snapshot under `plans/archive/`, this register, the decision/verification logs,
and `tests/test_v4_r53_active_entrypoints.py`. Base: `892ada7cf1`.
The `docs_hygiene_inventory` child performed read-only inventory and plan review;
no delegated writer or Git authority is granted.

Acceptance/KPIs: current entrypoints use immutable r53 + EVAS 0.8.7; every new
navigation link resolves; legacy guides explicitly prohibit use as current
instructions while retaining their bodies and paths; the shortened plan keeps
all open Phase 2/5 gaps, future Phase 6-10 acceptance, and the legacy local test
failure. No runtime, sealed release, raw evidence, or old worktree is changed.

Plan: run existing entrypoint/layout tests; add failing documentation navigation
checks; correct current entrypoints; label historical guides; snapshot the old
plan before compacting completed records; independently review and rerun the
focused gates; publish small commits only to the fork. No fallback/runtime
refactor or new dependency is in scope. Stop on concurrent edits, unique branch
commits, broken provenance, or an unresolved current-policy decision.

Local branch target only: `audit/vaevas-eval-closure` at
`03cf89415e9a69c6bf94e49ebb1b1a6deb9f3626`, verified merged into `origin/main`
and absent from `git worktree list`. Retain the fork's remote branch, all other
historical refs, every worktree, EVAS's current audit branch and its old dirty
checkout. Deletion is a metadata tidy-up, not a meaningful RAM/disk saving;
the local ref can be recreated from its recorded SHA or retained remote.

Local outcome: the single local ref was removed; current entrypoints/navigation
and nine historical banners pass the 48-test layout subset. The active plan is
552 lines with a reconstructable old snapshot and unchanged Phase 6-10
acceptance. Independent read-only final review has no blocker. No worktree or
evidence files were removed. Exact verification and publication status belong
in the verification log; this slice grants no runtime or EVAS follow-up work.

### Closed implementation slices

The following assignments are closed; their files are back with the main
coordinator. They record completed scope, not instructions to resume a writer.

Bounded differential slice (base `bc7a36b8b9`): the main coordinator owns
`tests/test_agent_harness_mini_swe_differential.py`, minimal repairs in
`runners/agent_harness/controller.py` and
`benchmark-vabench-release-v4/operations/calibration_pilot/run_native_mini_swe.py`,
their focused tests, AA-VAE-038 and shared records. The
`mini_swe_legacy_behavior_map` child maps legacy behavior read-only; subsequent
code/architecture reviewers also have no write or Git authority. Existing
legacy source/defaults are not assigned for modification. Test outputs go
under the already ignored `benchmark-vabench-release-v4/reports/` subtree;
no new repository-root scratch/output directory is authorized.
The `mini_swe_diff_code_review` and `mini_swe_diff_arch_review` children completed
independent read-only reviews without blockers. All implementation remains with
the coordinator. The local legacy one-second telemetry-test failure remains an
explicit validation gap, not permission for an unassigned legacy runtime rewrite.

Locally verified bounded slice (base `bbb76139ee`): main coordinator owns new
`operations/calibration_pilot/run_native_mini_swe.py` (under
`benchmark-vabench-release-v4/`), `tests/test_agent_harness_native_launcher.py`,
and any necessary deadline contract changes in
`runners/agent_harness/{controller,state,trajectory,result_artifact}.py`,
`native_episode.py`, and their focused tests. Main also owns CI, README,
AA-VAE-037 and shared records. The `native_launcher_map`,
`native_launcher_test_design`, and `native_deadline_design` native children
are read-only advisers with no file/index/history authority. They must hand
back findings rather than widen scope or start another writing lane.
The `native_deadline_code_review` and `native_deadline_arch_review` children
also reviewed deadline and launcher slices independently, without write rights.

The public-validation adapter and opt-in native episode / production final
result join and opt-in single-cell mini-swe launcher are verified locally.
Complete campaign/form integration, Testbench, retry, full transport/tool
archives and aggregate ledgers remain follow-ups under the
current plan. The coordinator defines the next bounded files/tests before
implementation; mapping/review stays read-only and no delegated writing lane
is opened by this document.
