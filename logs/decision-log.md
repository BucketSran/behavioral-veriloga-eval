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
