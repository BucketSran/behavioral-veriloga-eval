# Verification Log

## 2026-08-29 - Fork synchronization

- `BucketSran/behavioral-veriloga-eval` `main` equals upstream at
  `7b5616dc52195ec275ec6d21c71d7763613702cd`.
- `BucketSran/EVAS` `main` equals upstream at
  `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
- Clean worktree branch `audit/vaevas-eval-closure` starts from the synchronized
  behavioral-eval fork.
- Clean worktree branch `audit/evas-evaluator-compat` starts from the
  synchronized EVAS fork.
- Pre-existing dirty EVAS branch `fix/dynamic-zero-period-timer` was not
  modified.
- Behavioral-eval audit plan commit
  `a84c0281949742a190f234bcdacf7f4c51755425` was pushed to
  `origin/audit/vaevas-eval-closure`.
- EVAS audit branch `origin/audit/evas-evaluator-compat` points to the clean
  synchronized baseline `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
- The original EVAS worktree still contains only its pre-existing modifications
  to `evas/compiler/linter.py`, `evas/compiler/parser.py`, and
  `tests/test_linter.py` on `fix/dynamic-zero-period-timer`.

## 2026-08-29 - Existing evaluation baseline

- v3 runner CLI help and module import succeed in the current host environment.
- Existing targeted pytest invocation cannot start on the current host because
  `pytest` is absent.
- Existing environment inputs disagree: Docker uses Python 3.10 and installs
  only `evas-sim==0.8.4`, while the project requires Python 3.11+ and additional
  runtime/test dependencies.

## 2026-08-29 - Evaluator environment and clean-room closure

- `uv lock --check` passes with the project dependency pinned to
  `evas-sim==0.8.7` and the locked native wheel selected.
- Static `scripts/verify_evaluator_environment.py` checks pass. The formal live
  verifier requires Python exactly `3.11.13`; host Python `3.11.15` is retained
  only as non-formal compatibility evidence.
- A fresh `linux/amd64` Docker build from `environment/Dockerfile` passes with
  the digest-pinned Python `3.11.13` base. Runtime assertions observe
  `evas-sim 0.8.7`, `evas-rust`, a present/loadable Rust core, ABI `20260718`,
  and core version `0.2.4`.
- The real task-014 clean-room smoke passes: `dut_compile=1.0`,
  `tb_compile=1.0`, `sim_correct=1.0`, `weighted_total=1.0`. No forbidden
  private path enters the clean room, and managed cleanup changes the room from
  present before cleanup to absent after cleanup.
- The smoke claim gate allows only
  `single_task_clean_room_pipeline`; `model_score_claim_allowed=false` and
  `spectre_required=false`.
- The current v3 score roster contains zero `counted_in_score=true` rows.
  Formal list output therefore reports zero selected rows and a blocked claim.

## 2026-08-29 - Automated checks

- Focused evaluator closure tests:
  `20 passed` across environment contract, clean-room smoke, runtime failure
  attribution, complete-denominator gating, dirty-source gating, command
  binding, and persistent-worker blocking.
- Public runtime and mini-SWE tests after installing the lockfile's declared
  `agentic` extra: `38 passed, 3 skipped`.
- Final combined affected-surface invocation: `58 passed, 3 skipped`.
- A broader invocation produced `59 passed, 3 skipped` plus eight pre-existing,
  out-of-scope failures: four from the initially absent optional `agentic`
  extra, one v4 `pending_recertification` fixture, and three v1 tests whose
  `benchmark-vabench-release-v1/reports/model_eval_roster.json` is absent. The
  optional-extra failures disappear in the declared agentic environment; no
  closure code was changed to mask the remaining baseline failures.
- Ruff `0.12.12`, Python bytecode compilation, `git diff --check`, and Ruby YAML
  parsing of both affected workflows pass.
- The previously suggested `scripts/check_repo_layout.py` command cannot run
  because that file does not exist in this repository; repository-layout
  behavior is instead covered by the existing runtime-contract tests.

## 2026-08-29 - Repository boundary recheck

- Behavioral fork `origin/main` and `upstream/main` remain equal at
  `7b5616dc52195ec275ec6d21c71d7763613702cd`.
- EVAS fork `origin/main`, `upstream/main`, and audit branch remain equal at
  `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`; the EVAS audit worktree is clean.
- The original EVAS worktree remains on `fix/dynamic-zero-period-timer` with
  only its pre-existing modifications to `evas/compiler/linter.py`,
  `evas/compiler/parser.py`, and `tests/test_linter.py`.

## 2026-08-29 - Exact-runtime and empty-denominator evidence

- A fresh digest-pinned `linux/amd64` container executes both the live verifier
  and task-014 smoke under Python exactly `3.11.13`; the pipeline claim gate is
  allowed and all hidden-score components are `1.0`.
- A formal counted run in the same exact runtime writes
  `status=blocked_empty_denominator`, records zero selected/frozen-counted
  rows, sets `claim_allowed=false`, and exits with status `2`.
- The formal gate rejects non-canonical score-roster paths, filtered or partial
  denominators, stale/dirty source identity, invalid score metrics, mismatched
  Python/EVAS identities, command drift, persistent-worker mode, incomplete
  result artifacts, and infrastructure failures.
- Independent code review reproduced the gate's corrupt-metrics rejection and
  returned `ACCEPT` with no remaining blocker.

## 2026-08-29 - r53 three-arm clean-room smoke

- Branch/baseline recheck:
  `behavioral-veriloga-eval` is on `audit/vaevas-eval-closure` at
  `23c3d7bf0f852af19cb62e63f0d45aaf41f38203`; `origin/main` and
  `upstream/main` both remain at
  `7b5616dc52195ec275ec6d21c71d7763613702cd`.
- EVAS recheck:
  `/Users/bucketsran/Documents/TsingProject/vaEVAS-next/EVAS` is on
  `audit/evas-evaluator-compat`; `HEAD`, `origin/main`, `upstream/main`, and
  `origin/audit/evas-evaluator-compat` all remain at
  `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
- An inherited first draft passed one test but was rejected during review
  because it copied the hidden evaluator solution into the submission and did
  not execute the generation harness. No claim is based on that draft.
- Revised RED: `tests/test_v4_r53_clean_room_smoke.py` failed four checks because
  the draft did not expose a test-only sandbox control, accepted EVAS 0.8.3,
  allowed freeze replacement, and treated a zero-exit adapter without a
  structured result as passed.
- Revised GREEN: the same file now reports `4 passed`. The result-protocol plus
  smoke invocation reports `55 passed`.
- Affected v4 regression surface:
  `benchmark-vabench-release-v4/scripts/tests/test_v4_experiment_result_protocol.py`,
  `tests/test_benchmarkv4_calibration_pilot.py`, `tests/test_mini_swe_vabench.py`,
  `tests/test_v4_r53_active_entrypoints.py`, and
  `tests/test_v4_r53_clean_room_smoke.py` report `201 passed, 3 skipped`.
- Ruff `0.12.12`, Python bytecode compilation, Ruby YAML parsing of
  `.github/workflows/evaluator-closure.yml`, and `git diff --check` pass.
- Environment negative checks behaved as intended. The host PATH resolves
  `evas` to version `0.8.3`, which the new smoke rejects. The clean EVAS fork
  reports package `0.8.7` but initially produced structured
  `infrastructure_failure` sidecars because no Rust core existed in that
  worktree.
- A read-only-source Rust build used a temporary `CARGO_TARGET_DIR` outside the
  EVAS repository. With `EVAS_RUST_CORE_LIB` bound to that artifact, identity
  became `evas-sim 0.8.7 (rust-core 0.2.4, ABI 20260718, revision unknown,
  loadable)`. The existing public and no-EVAS Docker images also built and
  verified their pinned 0.8.7 capability boundary.
- The final real Docker smoke artifact is
  `generated-smoke-r53-closure-v2/smoke.json` (ignored generated evidence),
  SHA256
  `629f1f3352bd6a057078b0bbbe5c6243d624007b6e0e2646f3c1f899e48a37ae`.
  It records `status=PASS`, no blockers, release r53, and three fresh matched
  runtimes.
- `Agent-No-EVAS` records zero in-loop EVAS calls and `Agentic` records one.
  All three trajectory hash chains verify, all final submissions are immutable,
  and every sidecar joins to submission tree SHA256
  `ed247e3e8f80ac258bb3e1c07330af63399241af519a679121b31c3e82ab8a67`.
- The intentionally incomplete public-contract candidate receives structured
  `behavior_failure` in all three arms. That verdict is expected and is not a
  failed smoke: the gate validates evaluator connectivity and evidence
  integrity, not candidate quality. The aggregate EVAS 0.8.7 sidecar SHA256 is
  `00c58581601acb361c588407052824c8c36b83575c163dcc9b4629b5054985ee`.
- The claim gate permits only
  `single_task_three_arm_clean_room_pipeline`; both model-score and paper-result
  claims remain false, and paper-facing result authority still requires the
  separately declared Spectre protocol.

## 2026-08-29 - r53 smoke verifier refresh

- Fresh local syntax check passes:
  `./.venv/bin/python -m py_compile scripts/run_v4_r53_clean_room_smoke.py benchmark-vabench-release-v4/operations/calibration_pilot/run_campaign.py benchmark-vabench-release-v4/operations/calibration_pilot/result_protocol.py benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py`.
- Fresh focused tests pass:
  `./.venv/bin/python -m pytest -q tests/test_v4_r53_clean_room_smoke.py tests/test_v4_r53_active_entrypoints.py`
  reports `13 passed`.
- Fresh evaluator-closure subset passes:
  `./.venv/bin/python -m pytest -q benchmark-vabench-release-v4/scripts/tests/test_v4_experiment_result_protocol.py tests/test_v4_r53_clean_room_smoke.py`
  reports `57 passed`.
- Fresh affected v4 surface passes:
  `./.venv/bin/python -m pytest -q benchmark-vabench-release-v4/scripts/tests/test_v4_experiment_result_protocol.py tests/test_benchmarkv4_calibration_pilot.py tests/test_mini_swe_vabench.py tests/test_v4_r53_active_entrypoints.py tests/test_v4_r53_clean_room_smoke.py`
  reports `203 passed, 3 skipped`.
- `.github/workflows/evaluator-closure.yml` parses with Ruby YAML, and
  `git diff --check` passes.
- `generated-smoke-r53-closure-v2/smoke.json` remains the accepted artifact:
  SHA256 `629f1f3352bd6a057078b0bbbe5c6243d624007b6e0e2646f3c1f899e48a37ae`.
  Its aggregate EVAS sidecar
  `generated-smoke-r53-closure-v2/output/SCORE_EVAS_0_8_7.json` has SHA256
  `00c58581601acb361c588407052824c8c36b83575c163dcc9b4629b5054985ee`.
- Artifact inspection confirms `status=PASS`, release `r53`, EVAS
  `0.8.7`, `Agent-No-EVAS` has zero EVAS calls, `Agentic` has one EVAS call,
  all three trajectory chains verify, all final submissions are immutable, and
  every score sidecar joins to frozen submission tree
  `ed247e3e8f80ac258bb3e1c07330af63399241af519a679121b31c3e82ab8a67`.
- Boundary recheck: `benchmarkv4-r53` has no diff; the clean EVAS fork has no
  diff; the old `/Users/bucketsran/Documents/TsingProject/vaEvas/EVAS`
  worktree still shows only the pre-existing dirty files
  `evas/compiler/linter.py`, `evas/compiler/parser.py`, and
  `tests/test_linter.py`.

## 2026-08-29 - Independent review closure

- Independent code review accepted the generated single-task smoke evidence
  but found three merge-readiness gaps: order-sensitive multi-file freeze
  verification, missing protocol regressions in evaluator-closure CI, and a
  schema that did not require `immutable=true` for available submissions.
- The freeze now canonicalizes artifact order. A new regression proves that a
  non-lexicographically declared two-file submission can be frozen twice
  without drift while preserving deterministic tree identity.
- Evaluator-closure CI now runs the protocol, calibration-pilot, mini-SWE,
  active-entrypoint, and r53 smoke regressions; its path filter includes the
  protocol regression file.
- The experiment-result schema now conditionally requires `immutable=true`
  whenever `final_submission.status=available`, with an explicit negative
  schema regression.
- Post-fix focused tests report `57 passed`; the fresh affected v4 surface
  reports `203 passed, 3 skipped`.
- Ruff `0.12.12`, Python bytecode compilation, workflow YAML parsing, schema
  JSON parsing, and `git diff --check` all pass after the review fixes.
- A separate verifier returned `PASS` for this first milestone. Its accepted
  claim remains only the r53 three-arm clean-room pipeline; it explicitly does
  not treat the smoke as baseline reproduction or paper-result evidence.

## 2026-08-29 - AI-native harness evolution plan verification

- Replaced the completed first-milestone current plan with the next-phase
  AI-native harness evolution plan; no business/runtime implementation was
  performed in this planning step.
- The plan records exactly one `in_progress` phase (reconcile the paused
  prototype) and ten `pending` phases covering protocols, controller/state,
  mini-swe compatibility, domain tools, validation/test separation,
  AlphaApollo reasoning/evolution, evidence, ablations, and CI/merge gates.
- `git diff --check` passes for the planning and decision-log changes.
- The behavioral repository remains on fork `main`; the only pre-existing code
  work remains the untracked paused `runners/agent_harness/` prototype and its
  test. It was inspected but not integrated, committed, or expanded.
- The clean EVAS fork remains on `audit/evas-evaluator-compat` with no changes.
- The older `/Users/bucketsran/Documents/TsingProject/vaEvas/EVAS` worktree
  remains on `fix/dynamic-zero-period-timer` with only its pre-existing
  modifications to `evas/compiler/linter.py`, `evas/compiler/parser.py`, and
  `tests/test_linter.py`.
- No code tests were run because this step changed only tracked planning and
  decision/verification documentation. Runtime verification remains required
  per implementation slice.

## 2026-08-29 - Harness plan and publication-contract refinement

- The current plan now treats vaEVAS domain tools as non-callable extension
  points pending a separate tool-design decision and per-tool ablation review.
- The plan maps SWE-agent/mini-swe, OpenHands, Aider, and Codex CLI patterns to
  named vaEVAS landing files, required regressions, and explicit rejection
  boundaries; none is introduced as a runtime dependency.
- `AGENTS.md` now requires multiple focused, CI-safe, independently revertible
  commits, exact-scope staging, per-slice verification, and fork-only pushes.
- Baseline audit before the documentation commit reports `main...origin/main`
  as `0/0` and `upstream/main...main` as `0/4`: fork `main` contains four
  reviewed vaEVAS commits on top of the current Arcadia-1 upstream baseline.
- No runtime code or frozen r53/EVAS asset is part of this documentation slice.

## 2026-08-29 - Phase 0 generic harness boundary prototype

- Baseline audit before staging reports branch `main` at `fb49d53df2`,
  `main...origin/main` as `0/0`, and `upstream/main...main` as `0/5`.
  The writable remote remains BucketSran `origin`; Arcadia-1 `upstream` remains
  read-only.
- Phase 0 now has an explicit keep/rework disposition in
  `docs/alphaapollo-migration/features/AA-VAE-015-generic-harness-boundaries.md`
  and `plans/current-plan.md` marks Phase 0 completed with Phase 1 in progress.
- Focused harness contract tests pass:
  `./.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_agent_harness_controller.py` reports `18 passed`.
- Existing mini-swe regressions remain green:
  `./.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_mini_swe_vabench.py` reports `30 passed, 3 skipped`.
- One earlier combined run observed the existing timeout-sensitive
  `test_direct_evas_timeout_is_recorded_without_leaking_control_markers` fail
  to record its invocation. Its exact rerun passed (`1 passed`) and the fresh
  standalone mini-swe suite then passed. The prototype is not imported by that
  path; no mini-swe production change was made in this slice.
- Active r53 entrypoint regressions remain green:
  `./.venv/bin/python -m pytest -q -p no:cacheprovider
  tests/test_v4_r53_active_entrypoints.py` reports `9 passed`.
- Python bytecode compilation passes for `runners/agent_harness/*.py` and
  `tests/test_agent_harness_controller.py`.
- Ruff 0.12.12 reports `All checks passed!` for the new package and test.
- The repository has no `scripts/check_repo_layout.py`; the applicable
  mini-swe and active-entrypoint runtime-contract regressions were run instead.
- A targeted production-import scan finds `runners.agent_harness` only in
  `tests/test_agent_harness_controller.py`; current v4 runners and
  calibration-pilot entrypoints do not import the prototype package.
- Independent code review initially found mutable freeze artifacts, missing
  event visibility, and empty episode identities. RED regressions were added,
  all three were fixed, and re-review returned APPROVE with no blocking issue.
- The re-review's remaining LOW note (unconstrained visibility strings) was
  also closed by an `EventVisibility` literal, runtime allowlist, and a
  rejection regression before commit.
- `git diff --check` passes.
- Boundary: this prototype changes no r53 task bytes, no EVAS code, no existing
  mini-swe execution path, and no formal score authority. It does not trigger
  Spectre parity.
