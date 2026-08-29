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
