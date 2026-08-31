# vaEVAS Development Work Ownership

Updated: 2026-09-01

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

2026-09-01, base `c4f2f93e89dddf3cf91ec7716872c5554524921a`: main owns
`plans/adversarial-and-result-adapter.md`, the new read-only Inspect adapter and
its tests, adversarial integration tests, shared docs/logs/CI and Git. The
`adversarial_test_map` and `adapter_framework_research` advisers are read-only.
No evaluator/release/old-tree writes, paid calls or external framework scheduler
activation. Exact delegated leaves, if any, must be recorded before handoff.
Acceptance is the linked plan's KPI; all previous assignments below are closed.

`adversarial_e2e_impl` owns only new
`tests/test_agent_harness_adversarial_e2e.py`, based on `c4f2f93e89` plus the
main-owned plan. Reuse active r53 Docker/native launcher fixtures, no source
runtime edits. Cover forged success diagnostics, forbidden private/sibling reads,
and frozen-evidence tamper/no replay with a real selected final EVAS path; add
Testbench bypass if supported by existing fixtures. Main owns CI and docs.
Delegate returns unstaged tests plus exact commands/results and stops editing;
no Git, release/EVAS/old-tree mutation, paid models or broad cleanup.

Current activation at `30d1efa956`: main owns the static corpus manifest,
authorization/usage notes, its regression tests and shared records/Git under
`plans/veriloga-corpus-activation.md`. `corpus_source_review` is a read-only
public-source adviser. The user has now authorized veriloga-skills reference
use; the earlier no-ingestion handoff below is historical. No paid run,
delegated writer, evaluator/release or old-worktree mutation is authorized.
Activation source `7313f98507` is committed after independent review and local
GREEN. Both read-only advisers are complete; main closes the documentation and
fork publication slice. Downloaded reference files remain local/ignored, with
no delegated edit or paid lane active.

AA-VAE-073/074/075 starts at `025276c6fc8acef2ef4377498d667494065baa4a`.
Follow `combined-tools-acceptance.md`. Main owns new calibration-pilot
`run_combined_tools.py`, its exact tests, shared CLI/native integration hooks,
schemas outside the two assigned leaves, CI, docs/plans/logs and Git.

`resume_evolution_impl` owns only calibration-pilot `run_native_evolution.py`
and `tests/test_agent_harness_evolution_waveform.py`. Reuse existing waveform
executor and receipt rehydration; propose any other shared-file change to main.
Acceptance: absent option preserves old behavior; candidate/profile-bound bounded
waveform feedback crosses only the next-round barrier, charged once; corruption,
final-feedback and late-candidate changes fail closed. No selection/scorer change.

`synthetic_training_adapter_impl` owns only
`runners/agent_harness/tools/offline_docs.py`,
`runners/agent_harness/tools/offline_docs_tool.py`, and new
`tests/test_agent_harness_reviewed_docs.py`. Implement the reviewed-v2 leaf
contract while preserving synthetic-v1 and tool boundaries. Main approves the
schema/interface before writing. Acceptance includes rights/remote-use gates,
provenance/hash/path validation and deterministic compatible retrieval.

Both delegates use vertical TDD, are not alone in this worktree, must not revert
others, and return unstaged edits before stable-tree integration. No Git/index,
other files, real credentials/paid calls, source corpus copying, EVAS/release or
old-tree writes. `comparison_runner_design` and `live_provider_contract_review`
remain read-only advisers; an independent reviewer has no writing authority.
All earlier assignments below are closed historical records, not active grants.

Additional bounded writer `paired_report_impl` owns only calibration-pilot
`combined_tool_evidence.py` and `tests/test_agent_harness_combined_tool_evidence.py`.
Implement read-only feature-use projection from existing native/Evolution
trajectory and sealed public receipts: retrieval, waveform, next-round exposure.
Main owns its calling/manifest/result integration. No scoring or runtime calls,
raw content in output, Git, other files or corpus/credential access. Tests use
synthetic fixtures. Hand back code and validation before root integration.

All AA-VAE-073/074/075 writers have handed back, including the reopened feature
projection repair. Main now owns all files for stable-tree integration and
focused publication. Reviewers remain read-only. No delegated edit/Git/paid
lane is active; the earlier assignment paragraphs are retained for traceability.
Source publication through `6ac7482d4b` and all three exact-source hosted gates
are complete. Main owns only the evidence-record follow-up; all delegate lanes
remain closed. This handoff does not authorize real-corpus ingestion or paid runs.

AA-VAE-072 starts at `f1c78b3dd7b9b0913a626661158c816c55091667`.
Main exclusively owns calibration-pilot `comparison_live.py`,
`run_legacy_native_comparison.py`, `tests/test_agent_harness_comparison_live.py`,
related comparison/CI regression tests, CI, README, feature note, ledger, plans,
logs and Git. Follow `legacy-native-live-entrypoint.md`. No delegated writing
lane: `live_provider_contract_review` is read-only official documentation
research; the final reviewer is also read-only. No actual keys, paid generation,
provider metadata calls, old-tree writes, r53/EVAS edits or historical-run reuse.
Implementation, independent read-only review and source publication are complete.
All three exact-source hosted workflows passed at `58829c7172`. Main closes the
evidence-only documentation follow-up; no delegated writer is active, and this
handoff opens no paid execution lane.
All earlier assignments below remain closed historical records.

Current follow-up starts at `e2498952bb25d46d28b97765df9963a113113cde`:
follow `legacy-native-comparison-engineering.md`. Main owns all shared
contracts/orchestration, optional budget parameters, runner hooks, integration
tests, CI, docs/logs/plan/ledger and Git. Prior assignments remain closed.
Prospective independent leaf ownership is reserved for `comparison_results.py`
and its exact test file, and `comparison_surface.py` and its exact test file
(all runtime leaves under calibration_pilot). Writers need an explicit new
assignment before editing. No delegated shared-file/Git/paid/private-evidence
authority. Main will publish GREEN slices only to BucketSran origin/main.

Active bounded writer `comparison_surface_impl` owns only
`benchmark-vabench-release-v4/operations/calibration_pilot/comparison_surface.py`
and `tests/test_agent_harness_comparison_surface.py`, on intake `e2498952bb`.
Implement vertical RED/GREEN for public-tree/request fingerprints and actual
Docker mount/security/image observations; return unstaged edits and commands.
APIs are `snapshot_public_runtime(runtime)`, `observe_environment(env)`,
`snapshot_request(payload, timeout_s=...)`, and `compare_surfaces(left, right)`.
Only safe public content hashes and observed metadata; never read private tree
contents or environment secret values. No shared files, runner hooks, Git,
credentials, paid execution, or other writer files. Main wires these APIs.
Read-only adviser `comparison_runner_design` owns no files.

Active bounded writer `comparison_results_impl` owns only
`benchmark-vabench-release-v4/operations/calibration_pilot/comparison_results.py`
and `tests/test_agent_harness_comparison_results.py`, intake `e2498952bb`.
Implement read-only legacy/native evidence readers and complete six-row,
three-pair projections by vertical RED/GREEN. Main supplies/seals a
`evidence/comparison-legacy-final.json` after the existing bound scorer runs
once; the reader reuses the existing frozen-submission and final-receipt
validators. No generation/freeze/judge/repair execution, shared files, docs,
Git, credentials, paid calls or other writer files. Return unstaged code and
verification evidence; main owns the integration receipt schema and hooks.

Both AA-VAE-071 leaf writers have handed back and stopped editing. Main now
owns all comparison files and three opt-in lifecycle-hook changes in
`run_campaign.py`, `mini_swe_vabench.py`, and `run_native_mini_swe.py`.
`comparison_gate_review` reviews read-only; main runs integration on a stable
tree. Source drift during the first concurrent diagnostic correctly retained
the remaining unstarted rows; do not reuse that incomplete diagnostic as GREEN.

Review-fix assignment on `e05ca61089`: `comparison_surface_impl` again owns
only `comparison_surface.py` and `tests/test_agent_harness_comparison_surface.py`.
Preserve the coordinator's empty-submission hash repair; use vertical TDD for
provider-option matching, finite numeric controls, and fail-closed observation
validation. No other file/Git/live writes. Hand back before integration runs.
Main retains results, coordinator, integration tests, CI and shared records.
The surface review-fix assignment is now handed back. Main owns all files;
`comparison_gate_review` reports no remaining source-level blocker after the
independent second pass. Stable-tree free Docker, active local regressions,
fork publication and exact-source hosted gates are complete through `8609747ccb`.
The final documentation-only evidence update remains main-owned; no delegated
writer or paid/live assignment remains active under this brief.

The AA-VAE-070 and cap-fix local-only handoffs below are historical: publication
through `e2498952bb` and all three exact-source hosted gates are now complete.

AA-VAE-070 integration on `e46a9d6719893d500071f6cf5ce744d4dc7f439a`:
main owns `runners/agent_harness/batch_resume.py`,
calibration-pilot `run_native_batch.py`,
`tests/test_agent_harness_batch_resume.py`, calibration-pilot `run_campaign.py`,
`benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py`,
`tests/test_agent_harness_native_campaign_dispatch.py`, both runner READMEs,
`plans/batch-resume.md`, current-plan/this register, decision/verification logs,
`docs/alphaapollo-migration/features/AA-VAE-070-batch-resume.md` and migration
ledger. `resume_attempt_impl` owns only `runners/agent_harness/attempt_sequence.py`,
calibration-pilot `run_native_attempts.py`,
`tests/test_agent_harness_attempt_sequence.py` and
`tests/test_agent_harness_native_attempts.py`. Base and acceptance are in the
linked brief. `resume_code_map` and `resume_upstream_research` are read-only
advisers; no delegated Git, shared docs, benchmark/evaluator, credential, private
evidence or paid execution authority. Delegates hand back unstaged source/tests
and RED/GREEN evidence; main performs independent review and local commits.
`resume_evolution_impl` owns only calibration-pilot
`run_evolution_campaign.py`, new `evolution_batch.py`, and
`tests/test_agent_harness_evolution_batch.py`. Preserve the old one-cell path;
add an explicit opt-in batch path using the shared journal described in the
brief. No round/agent/final engine changes. Free test fixtures only; hand back
unstaged changes to main. The main-owned shared batch API is coordinated by
message; delegates must not edit that module or shared records.
The attempt writer has handed back; main owns its four files for integration.
The Evolution writer is continuing a bounded review-fix pass on the same three
files (frozen runtime identity, complete preflight, safe retry and real-result
joins). Main additionally owns `.github/workflows/evaluator-closure.yml` and
`tests/test_agent_harness_ci_gate.py`. `resume_native_review` reviews shared/native
batch and attempt recovery read-only; no edits, Git, credentials or paid calls.
Both implementation writers are now handed back. Main owns all integration
files, including `run_native_evolution.py` for the test-confirmed missing public
validation image-ID binding (no reducer/selection/score policy change). The old
setup-failure xfail did not reproduce on the final handed-back fixture; it is
removed, not accepted as a CI substitute or grounds for an export-engine edit.
Main also owns `native_episode.py` for extracting its existing sidecar-receipt
verification into a read-only helper shared by live judging and batch recovery.
The independent review's 12 new adversarial cases are RED before this repair;
no second judge or alternative scoring implementation is authorized.
`resume_evolution_review` independently reviews the three Evolution batch files
read-only; `resume_evolution_setup_map` investigates the real Docker setup failure
read-only. No delegated implementation, Git, private evidence or paid execution.
Both source reviews are complete: shared/native has no remaining required
correction, and Evolution re-review is APPROVE after the config/receipt/setup
fixes. The setup diagnosis confirmed a Docker-invisible macOS temporary path,
not an export defect. All advisory/writer assignments are closed; main owns
only final local tests, records and focused commits. No push is opened here.

Closed bounded integration request from audit task
`01a05640-c83b-7223-8da0-738af106d023`, base
`dee9ccfeb09cc41baf1982d1ee7882f92aef5d72`: main alone owns
`benchmark-vabench-release-v4/operations/calibration_pilot/run_deepseek_pilot.py`,
`tests/test_agent_harness_deepseek_pilot.py`, `plans/current-plan.md`, this
register, both decision/verification logs,
`docs/alphaapollo-migration/features/AA-VAE-052-guarded-six-cell-pilot.md` and
`docs/alphaapollo-migration/01_功能迁移台账.md`. Bind the frozen manifest cap
to the existing guard; prove smaller-cap HTTP rejection and manifest-cap drift
rejection with free fixtures. No guard algorithm, r53/EVAS, credentials, raw
private evidence, paid calls or push. Audit task remains shared-source read-only;
`cap_binding_review` owns only independent read-only review of these changes
and the existing guard/client context. Return a clean local commit and test evidence;
no coordinator transfer or historical writer reactivation.
Implementation and free verification are complete; `cap_binding_review` has
returned no required corrections and its read-only assignment is closed.
Main owns only local commit/handoff; no further source or paid-run lane opens here.

Closed protocol preparation on `2c07dca529`: follow
`legacy-native-comparison-protocol.md` for exact ownership and acceptance.
Main owns documentation and bounded offline evidence tests, not production
runtime changes or a paid experiment. `case_study_code_map` and
`portable_contract_review` have returned their read-only advice; independent
`case_study_review` reports no required correction (`COMMENT`, static tooling
limitations explicit). Source `8ccb616fe7` is published to fork/main and both
exact-source hosted workflows pass. All advisory assignments are closed;
main owns this final evidence-record publication. Historical
assignments remain closed. No delegated writes, Git operations, provider/
credential or hidden-content access. Live-run implementation is not opened here.

Completed main-only follow-up on `e5f2e9dcec`: follow
`legacy-native-r53-contract-compatibility.md` for exact scope and KPIs.
Source `08f2c9310f` is published to fork/main; local tests, independent code/docs
review and both exact-source hosted gates pass. Main owns only evidence-record
closeout. `portable_contract_review` and `portable_fix_review` have returned
their read-only advice/review; assignments are closed. No source/Git/provider/
private-content authority was delegated. This closes the old sensitivity
contract residual, not any separately gated scoring/tool/experiment proposal.

Completed main-only repair on `1c73e519bd`: follow
`r53-public-contract-compatibility.md` for exact runtime/test/document ownership,
acceptance and forbidden surfaces. Source `2e1ec6ba32` is published to fork/main;
focused/real Docker verification and both exact-source hosted workflows pass.
The repair and advisory assignments are closed; main owns this final record.
`portable_contract_review` and `portable_fix_review` have returned their read-only
advice/review (no blocking finding). No delegate has write, provider,
private-content or publication authority. Historical assignments remain closed.

Completed documentation-only assignment: `single-task-harness-case-study.md`
on `87c10cb65e`. Plan `21159e3c09` and notebook `6063cfc5ca` are published;
their exact hosted gates pass. Main owns only final verification-record closure.
`case_study_code_map` and `case_study_review` have returned and stopped their
read-only advisory work; all runtime implementation assignments remain closed.
No raw evidence edits,
paid execution, hidden checker/gold inspection or delegated Git authority.

N1–N5 implementation assignments are closed and returned to main. Published
AA-VAE-061–066 end at `8d782880c7`; independent reviews and final local tests
are complete (1013 harness passes / 25 skips; 12 real Docker passes). No
delegated writer remains active. Main alone owns N6 documentation/navigation
tests, hosted verification, final audit records and fork publication. N6 review
APPROVE and source/audit hosted gates are green; final closeout is published as
`87c10cb65e`. The assignment details below are historical
scope records, not authorization to resume a writer.

N4/N5 main-only slice followed `evolution-extension-surface-closure.md` for exact
runtime/test leaves. Branch export repair `9e98100cd1`, synthetic Evolution docs
`72a9f8614d` and surface/failure reporting `8d782880c7` are published.

`paired_report_impl` (N2 / AA-VAE-063) handed back calibration-pilot
`result_ledger.py` and `tests/test_agent_harness_result_ledger.py` and stopped
writing. Main owns their final production-path repairs, integration and Git.
`synthetic_training_adapter_impl` (N3 / AA-VAE-062) handed back
`runners/agent_harness/training_trace_adapter.py` and its test, now published as
`811d82e806`. Both old writer assignments are closed. Current N4/N5 advice and
N1/N2 re-review are read-only; no delegate has file, index or push authority.

Overnight closure on `961fa99fdc`: main owns N1 / AA-VAE-061 native waveform
wiring. Exact writable runtime/test files: calibration-pilot
`run_native_mini_swe.py`, `public_waveform.py`, `score_campaign.py`;
`runners/agent_harness/tools/public_waveform_tool.py` (new);
`tests/test_agent_harness_public_waveform.py`,
`tests/test_agent_harness_waveform_integration.py` (new),
`tests/test_agent_harness_ci_gate.py`; applicable runner README, CI and shared
plans/logs/migration docs. Existing controller/budget APIs are reused unchanged
unless a separately reviewed amendment is required. The three `waveform_*`
advisers inventory N2–N5 read-only; no delegated writes or Git authority.
Follow `overnight-engineering-closure.md` and the accepted N1 plan. Main alone
integrates, verifies and publishes; all historical writer assignments stay closed.

AA-VAE-057–059: the three exact synthetic module/test leaves below have handed
back and stopped writing. Main owns all remaining shared integration, review
repairs, documentation and Git. `docs_runtime_review` and
`extension_boundary_review` are independent read-only reviewers; no delegate has
index/history/push authority. Their source/provenance findings are covered by
regressions, not treated as permission to expand into real data or training.

AA-VAE-055 follow-up on `8467af3d38`: main alone writes public EVAS feedback,
native bridge/launcher, operation-aware summary tests and shared records.
Scope/KPIs: `public-evas-feedback-and-extension-design.md`. Three advisers
(`rag_design`, `waveform_design`, `training_design`) read current public harness
code and return designs only. They have no source/Git/data-export/credential/
provider/training authority. Main integrates their suggestions into separate
reviewable notes; no reserved tool becomes callable in this slice.
The three read-only designs have returned. `public_feedback_review` owns only
independent review; its marker-forgery finding is addressed by explicit
unauthenticated diagnostic quarantine, not a new isolated executor. No delegate
has source, index or publication authority. Main owns final tests and commits.
Runtime repair is committed as `9da787b638`. The separate AA-VAE-056 design note
consolidates all three advisers; they are closed/read-only, not active feature
implementers. Future leaf implementation needs an exact file assignment here.

AA-VAE-053/054 (base `32b63963bd`): main owns native operational-contract
and optional model-call-budget implementation, existing controller/budget/state,
launcher/campaign/pilot/scorer seams, related tests and shared records listed in
`native-operational-contract-and-call-budget.md`. AA-VAE-053 is published as
`ad40f11496`; AA-VAE-054 is implemented and independently reviewed by
`native_campaign_impl` and `deepseek_driver_review`. Reviewers are read-only;
main owns final verification and publication. All old writers remain closed;
no delegated write/Git/credential/provider authority is granted. This repair
does not authorize a paid rerun, including the historical pilot below.

AA-VAE-052 implementation is owned and verified by main. `pilot_budget_surface`
and `deepseek_driver_review` completed independent read-only reviews; no blocker
and no delegated writes. Main alone commits and launches the bounded live run.

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
| Production public-validation adapter and campaign wiring | main coordinator | none; native three-form/three-condition campaign, fresh attempts and Evolution composition integrated |
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

DeepSeek live-driver slice on `07b1f33e2a`: main owns new calibration
`run_deepseek_pilot.py`, its new tests, CI selectors and records. All earlier
writers remain closed. `deepseek_price_contract` refreshes official API facts
read-only; `pilot_budget_surface` reviews driver/budget/denominator boundaries
read-only before launch. No delegated credential access or provider calls.

GLM preference update on `2aea03a828`: main owns the local-only credential
helper/tests, CI selector and GLM pilot plan/records. `deepseek_price_contract`
researched public GLM documentation; `native_campaign_impl` mapped existing
driver/scorer seams; `pilot_budget_surface` reviewed the credential helper.
All three lanes were read-only, with no real credential-file access or Git
authority. No delegated writer is open. Platform confirmation and GLM live
budget/driver integration remain pending; no authenticated API call occurred.

Budgeted DeepSeek pilot on `306eb45c9b`: main owns all new
`deepseek_budget.py`, its two test files, CI selector/workflow updates and
shared records. `deepseek_price_contract` verified official provider semantics
read-only; `pilot_budget_surface` reviewed the guard read-only. No delegated
writing lane was opened. Real paid execution still awaits credentials and a
fresh guarded live schedule; free fixtures are not model experiments.

Current closeout: all delegated implementation lanes are handed back and stopped.
The coordinator verified and published the integrated runtime as `164131a8a4`;
all three triggered hosted workflows passed. No writing lane remains open.
AA-VAE-049 includes the bounded candidate-store helper lane
and `tests/test_agent_harness_evolution_candidate_store.py` handed back by
`alpha_public_reference`; main owns subsequent integration repairs. Independent
boundary and result/cost reviewers are read-only. The entries below are dated
assignment history, not active permission to restart a writer.

On `c313ba679a`, `alpha_public_reference` reopens only its Evolution composition
module and original test file for production-default repairs (actual profile
bootstrap, public-only branch memory, shared capture, budgets and cleanup).
Main owns new `run_evolution_campaign.py` under calibration and new
`tests/test_agent_harness_evolution_campaign.py`, providing real provider CLI
composition and real Docker coverage. Neither writer touches the other's files.

On `4460b9f7b4`, all previous leaves are handed back. Main retains shared
launcher/campaign/scorer wiring. `alpha_public_reference` owns only new
calibration `run_native_evolution.py` and new
`tests/test_agent_harness_native_evolution.py`: runnable candidate-only
Reasoning branches, fixed public validation, sealed round memory and exactly one
selected-submission final replay. Reuse existing controller/transport/export/
authority and round-runtime APIs; do not write shared files or Git. Main owns
CLI integration and records. `tb_surface_map` reviews the repaired round runtime
read-only. `case_trajectory_delta` reviews the ledger leaf read-only. All writers
must preserve concurrent changes and return interface blockers to main.

`reasoning_policy_impl` reopens only `runners/agent_harness/attempt_sequence.py`,
calibration `run_native_attempts.py` and their two original unit test files for
the final AA-VAE-045 review findings: real `sandbox_cleanup_failure` must block
retry; cancellation/SystemExit must propagate without a terminal selection.
All other paths and Git remain unassigned to this delegate.

`evidence_export_impl` reopens only calibration `result_ledger.py` and
`tests/test_agent_harness_result_ledger.py` for explicit single-trajectory backend
and condition eligibility, rejecting candidate-only/Evolution records and
unannounced mixed-backend pairing. Main keeps scorer integration ownership.

Integration on `51dea24715`: AA-VAE-044 leaves are closed. Main owns all shared
runtime/CLI/scorer wiring and the handed-back attempt files. `native_campaign_impl`
reviews attempts read-only; `alpha_public_reference` advises candidate-only
controller integration read-only. `reasoning_policy_impl` reopens only its two
original reasoning leaf files for deadline-bounded provider requests and explicit
strict-JSON/tool-schema prompting, with focused RED/GREEN tests. No shared files
or Git operations transfer. All delegates are concurrent with main and must
preserve others' edits, stop at handback and report conflicts upward.

Reasoning deadline/prompt handback is complete. `reasoning_policy_impl` now
reopens only `run_native_attempts.py` (calibration) and its original
`tests/test_agent_harness_native_attempts.py` for independent-review repairs:
physical terminal-marker blocking, confined derived runtime paths, row/context
receipt verification and accurate all-attempt costs. Main owns integration tests
and shared wiring concurrently. `alpha_public_reference` owns only
`runners/agent_harness/{controller,state,contracts,trajectory}.py` and new
`tests/test_agent_harness_candidate_episode.py` for a candidate-only terminal
seam reusing the existing loop. Existing final episode semantics must remain
unchanged; no fake final judge or relaxed final trajectory validation. All other
tests/schemas/package exports/launcher/Git remain main-owned.

`evidence_export_impl` is assigned only new calibration `result_ledger.py` and
new `tests/test_agent_harness_result_ledger.py` on `4460b9f7b4`. Build a read-only
deterministic campaign-ledger/report projection over frozen schedule and already
verified native rows: denominator/identity checks, selected/all-attempt costs,
explicit unknown metrics, matched-pair coverage, deadline outcomes and bounded
claim/source index. No scoring/provider execution, no free-text/raw-content
export, no cross-backend/evolution pooling, no inferred model-quality claims.
Main owns actual scorer/CLI invocation and all records. Vertical TDD and handback;
no other writer's edits, dependencies, assets or Git operations may be changed.

Result-ledger leaf is handed back. `evidence_export_impl` is reassigned only
`runners/agent_harness/evolution_runtime.py` and its original
`tests/test_agent_harness_evolution_runtime.py` for review repairs: safe branch
path segments/confinement and explicit unknown/partial observed failure costs.
The candidate controller writer remains on its non-overlapping files. No shared
schema, reducer, launcher, ledger or Git writes are delegated by this repair.

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

Follow-up integration assignments on `67d1b55f4e` (2026-08-30): the attempt
sequence leaf is `handed_back`; `tb_surface_map` re-reviews it read-only.
`reasoning_policy_impl` is active only on its original two reasoning leaf files:
repair strict-JSON multi-turn history, remove duplicate native observations,
bind action IDs to the launcher's existing attempt-number format, and test
numeric request/usage validation. No launcher or transport ownership transfers.
`evidence_export_impl` is active only on its original two evidence leaf files:
accept legitimate optional null terminal fields, allowlist counter keys,
reject malformed hashes/nonfinite or negative usage, and retain truthful
unknown-usage semantics. Main owns launcher/scorer wiring and integration tests.
Each delegate must stop at handback; all records/Git operations stay with main.

`native_campaign_impl` owns only
`benchmark-vabench-release-v4/operations/calibration_pilot/mini_swe_vabench.py`
and new `tests/test_agent_harness_private_tool_capture.py` during the bounded
private-output capture follow-up on `67d1b55f4e`. Add an optional native private
sink retaining the bounded pre-model output plus full-stream byte/hash and
truncation/completion evidence, without changing legacy/model-visible output.
Main binds this sink to action IDs and immutable private events. No controller,
launcher/scorer, provider transport, shared docs, release or evaluator edits.

Reasoning leaf follow-up is `handed_back`. `reasoning_policy_impl` reopens only
its two attempt-sequence files to repair exact retry-index/adjacent-decision
verification, recompute decisions from frozen policy/outcome, and reject typed
outcome boolean drift. This is a review repair, not campaign integration.

Private tool-capture leaf is `handed_back`. Main owns provider transport capture
in calibration `run_campaign.py`, native callback wiring, new
`tests/test_agent_harness_private_provider_capture.py`, and existing launcher /
campaign tests. `evidence_export_impl` reopens only its original two leaf files
to normalize joined per-request transport attempts and per-action bounded tool
captures, with explicit unobserved/incomplete/truncated counts and safe structural
metadata. Raw outputs never enter reviewer payload or shared model memory.

`alpha_public_reference` now owns only new
`runners/agent_harness/evolution_runtime.py` and new
`tests/test_agent_harness_evolution_runtime.py`. Implement a bounded round
coordinator over the existing manifest/reducers and memory/lineage contracts,
using a caller-owned candidate-branch callback (no final judge callback exposed
to branches). Freeze each prior-round information set, preallocate deterministic
branch budgets, await the strict barrier, persist write-once receipts and count
all branches/costs. Concrete Bash/provider/candidate/final wiring stays with main.
No shared interfaces/schema/launcher/Git/dependency edits; TDD and handback apply.

Attempt verifier leaf is `handed_back`. `reasoning_policy_impl` next owns only
new `benchmark-vabench-release-v4/operations/calibration_pilot/run_native_attempts.py`
and new `tests/test_agent_harness_native_attempts.py`. Compose the fresh-attempt
journal with the existing campaign single-cell runner and read-only scorer;
main supplies context/CLI dispatch wiring. Each journal runtime contains one
fresh cell export, preserving existing no-reentry guards. Select one terminal
attempt per cell while preserving all source receipts and all-attempt costs.
Only typed, positively classified pre-final transport/startup failures qualify;
cleanup uncertainty, final reservation and model/protocol failures do not.

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
## Trusted public waveform executor (2026-08-31, implemented)

Main owns `benchmark-vabench-release-v4/operations/calibration_pilot/public_waveform.py`,
`tests/test_agent_harness_public_waveform.py`, the minimal read-only mount option
in `mini_swe_vabench.py`, parser byte-input reuse in `waveform_summary.py`, related
regressions, CI and shared records/Git. `waveform_executor_map` and
`waveform_boundary_review` are read-only, with no source/index/history authority.
`waveform_code_review` independently reviewed the implementation without edits.
Follow `trusted-public-waveform-executor.md`; no legacy/default/model-tool activation.
Main owns publication and the separate `native-public-waveform-feedback.md` design;
no delegated native-integration writing lane is opened by the read-only mapping.

## Synthetic extension leaves (2026-08-31, handed_back)

Dispatched on base `7004ee095f`, now handed back. Main owns shared
interfaces, launcher/controller/registry wiring, docs, integration tests and all
Git. Three exact non-overlapping assignments:

- `rag_impl`: `runners/agent_harness/tools/offline_docs.py` and
  `tests/test_agent_harness_offline_docs.py` only.
- `waveform_impl`: `runners/agent_harness/tools/waveform_summary.py` and
  `tests/test_agent_harness_waveform_summary.py` only.
- `training_impl`: `runners/agent_harness/training_export.py` and
  `tests/test_agent_harness_training_export.py` only.

Follow [the controlled brief](rag-waveform-training-implementation.md) and
vertical TDD. No other file writes, Git operations, dependencies, credentials,
paid calls, private project access, old-worktree edits or sealed r53/EVAS changes.
Writers are concurrent, must preserve others' changes, report interface conflicts
upward and stop writing at handback. This newer assignment supersedes earlier
read-only extension-design lanes; it does not reopen any historical writer.
