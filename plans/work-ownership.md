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
| Production public-validation adapter and complete campaign wiring | main coordinator | none; opt-in public-simulation slice verified, complete campaign wiring still pending |
| Trajectory/result joins, backend adapters, evolution/memory/lineage, and their tests | main coordinator | none; assign exact leaf files before parallel implementation |
| All other tracked files not explicitly assigned below | main coordinator | none |

There are currently **no active delegated write assignments**. Independent
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

The public-validation adapter slice is verified. The coordinator now owns the
opt-in native episode / production final result join described in the current
plan, including `native_episode.py`, minimal result-store/reentry changes and
their tests. Parallel mapping/review remains read-only; no delegated writing
lane is opened by this document.
