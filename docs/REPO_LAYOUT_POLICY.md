# Repository Layout Policy

This policy follows the [agent contract](../AGENTS.md). Use the
[documentation index](README.md) to distinguish active instructions from history.

## Active Public Surface

The active immutable benchmark release is:

```text
benchmark-vabench-release-v4/release/benchmarkv4-r53/
```

Its [manifest](../benchmark-vabench-release-v4/release/benchmarkv4-r53/MANIFEST.json)
and [certification](../benchmark-vabench-release-v4/R53_RELEASE_CERTIFICATION.md)
define release identity and evidence. EVAS 0.8.7 is pinned for current work.
The package is not an authoring workspace: task, fixture or manifest changes
require a separately approved successor revision. Harness/evaluation work
belongs in the v4 operations/runners or shared harness layers.

V3 and V1 remain historical source/evidence surfaces. V2 is retired and must not
be recreated. The unversioned `release/benchmarkv4/` is frozen r44; other
predecessors are retained only for explicit reproduction and provenance.
None is the current default.

## Stable Top-Level Directories

- `benchmark-vabench-release-v4/`: active release, provenance, operations and runners.
- `benchmark-vabench-release-v3/`, `benchmark-vabench-release-v1/`: historical assets.
- `docs/`: public documentation, migration notes and compact evidence indexes.
- `plans/`: active plan and clearly labeled historical snapshots.
- `logs/`: dated decisions and verification; not timeless operating instructions.
- `environment/`: shared agent-environment build source.
- `examples/`: runnable non-scored examples.
- `runners/`: reusable benchmark, harness and simulator adapters.
- `schemas/`: task, harness and result schemas.
- `scripts/`: repository maintenance scripts.
- `skills/`: optional reusable guidance, not implicit model-visible release content.
- `tests/`: regression and policy checks.

## Private And Transient State

Do not commit credentials, private endpoint/service identities, submission
records, raw provider payloads, unrestricted trajectories, waveform dumps,
simulator work roots or licensed judge artifacts. Public evidence must be
intentional, sanitized and reviewable.

Use an explicitly selected external output directory or the existing ignored
`benchmark-vabench-release-v4/reports/` subtree for local verification.
Use a fresh run directory; do not overwrite evidence or reuse a pytest basetemp
that contains an earlier run. Inspect any output before intentional publication.

## Forbidden Root Patterns

Do not create new top-level directories matching:

- `benchmark-vabench-release-v2/`
- `generated-*` or `generated/`
- `results-*` or `results_*/`
- `runlogs/`, `experiment-logs/`, `refine-logs/`
- `scratch/` or `tmp/`

Existing ignored data is not automatically disposable. Check evidence links
and obtain a bounded deletion scope before removing experiments or worktrees.

## Historical Documentation

Keep old protocol, taxonomy and audit records when they support provenance.
Label them as historical at the top and route readers to current documentation.
An old date alone is insufficient: legacy commands and counts must not look
like current instructions. Preserve referenced paths and bodies unless all
consumers have been audited. Do not mass-rewrite dated decision/verification logs.

## Checks

Run the current entrypoint/navigation and cleanup/count checks:

```bash
git diff --check
uv run --locked --extra agentic python -m pytest -q \
  tests/test_v4_r53_active_entrypoints.py \
  tests/test_evas_output_cleanup.py tests/test_task_count_filters.py
```

No dedicated `scripts/check_repo_layout.py` is currently present. For runtime
or scoring changes, also run the owning layer's regressions and the required
clean-room gate; this documentation check does not replace them.
