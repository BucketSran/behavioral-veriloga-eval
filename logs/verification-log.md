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

## 2026-08-29 - Existing evaluation baseline

- v3 runner CLI help and module import succeed in the current host environment.
- Existing targeted pytest invocation cannot start on the current host because
  `pytest` is absent.
- Existing environment inputs disagree: Docker uses Python 3.10 and installs
  only `evas-sim==0.8.4`, while the project requires Python 3.11+ and additional
  runtime/test dependencies.
