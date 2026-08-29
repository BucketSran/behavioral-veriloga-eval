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
