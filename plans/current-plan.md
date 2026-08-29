# vaEVAS Evaluation Closure Plan

Updated: 2026-08-29

## Objective

Close the reproducible evaluation path across the `behavioral-veriloga-eval`
fork and the `EVAS` fork while preserving their upstream ownership and keeping
Spectre optional.

## Repository boundaries

- Benchmark, runner, environment, evidence, and claim policy:
  `BucketSran/behavioral-veriloga-eval`.
- Simulator/compiler/runtime implementation: `BucketSran/EVAS`.
- Both fork `main` branches track `Arcadia-1` upstream and were synchronized
  before this audit branch was created.

## Steps

- [x] Synchronize both fork `main` branches with their upstream repositories.
- [x] Create clean audit worktrees from the synchronized fork branches.
- [>] Define one evaluator environment contract: Python version, locked runtime
  and test dependencies, EVAS package/native-core identity, mounts, and inputs.
- [ ] Add a single-task generation-to-hidden-scoring clean-room smoke test.
- [ ] Add the smoke test to CI and document the full scoring command.
- [ ] Bind summary claim state to executed evidence and explicit claim scope.
- [ ] Audit EVAS changes only where the integration test proves a simulator or
  packaging defect; keep benchmark-policy repairs in this repository.

## Stop condition

A clean environment can execute the documented single-task smoke and full
evaluation entrypoint; result provenance, failure states, denominators, and
claim boundaries are machine-checkable, with no Spectre requirement for EVAS
certification or model-score claims.
