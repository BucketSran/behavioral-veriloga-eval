# behavioral-veriloga-eval

vaEVAS combines VABench, an AI-native agent harness, public EVAS feedback,
trusted replay, and reproducible evaluation evidence.

## Current Benchmark Entrypoint

The active, immutable release is:

```text
benchmark-vabench-release-v4/release/benchmarkv4-r53/
```

Its [canonical manifest](benchmark-vabench-release-v4/release/benchmarkv4-r53/MANIFEST.json)
defines the denominator: 400 matched families, 1,200 tasks, and 2,000 certified
faults. The pinned evaluator is **EVAS 0.8.7** (`evas-sim==0.8.7`).
See the [r53 release certification](benchmark-vabench-release-v4/R53_RELEASE_CERTIFICATION.md).

Do not repair sealed task bytes in place or use a previous release as the
default for new experiments. A release change requires an explicitly approved
successor revision and provenance.

## Start Here

- [Agent contract](AGENTS.md): authority, isolation, evaluator and claim boundaries.
- [Documentation index](docs/README.md): current guides versus historical records.
- [Current plan](plans/current-plan.md): implemented scope and remaining work.
- [Campaign runners](benchmark-vabench-release-v4/runners/README.md) and
  [calibration / mini-swe operations](benchmark-vabench-release-v4/operations/calibration_pilot/README.md):
  executable operator entrypoints.
- [AlphaApollo migration notes](docs/alphaapollo-migration/README.md):
  ideas, exact code changes, tests, and known differences.
- [Verification log](logs/verification-log.md): dated local and hosted evidence.

The legacy mini-swe backend remains the default. The native single-cell launcher
is opt-in; AlphaApollo Reasoning/Evolution and complete native campaign coverage
remain unfinished. Connectivity smokes do not establish model performance.

## Evaluation And Visibility

Public EVAS feedback may guide generation. A model-invisible final checker
runs only after submission freeze and writes a hash-bound score sidecar.
Current trusted replay uses EVAS 0.8.7; its terminal position does not by itself
grant formal or Spectre-backed score authority.

Spectre is not a routine development requirement. It is a conditional audit
when EVAS changes or an explicitly named external/final protocol requires it.
Report the actual judge and evidence scope; never infer simulator equivalence.

The source repository can contain evaluator-side assets, but an agent sandbox
receives only the declared public package and writable submission surface.
Never mount private checkers, certified faults or final scores into generation.
Credentials, raw provider payloads, waveforms, and unrestricted trajectories
stay out of Git. See the [layout policy](docs/REPO_LAYOUT_POLICY.md).

## Repository Map

- `benchmark-vabench-release-v4/`: sealed releases, provenance, operations and runners.
- `runners/agent_harness/`: common controller, contracts and evidence components.
- `runners/`, `schemas/`, `environment/`: shared execution and contract surfaces.
- `docs/`, `plans/`, `logs/`: guides, current work and dated evidence.
- `tests/`, `scripts/`, `examples/`: regressions, maintenance and non-scored examples.
- `benchmark-vabench-release-v3/` and `benchmark-vabench-release-v1/`:
  historical source/evidence, not current defaults. V2 is retired.
- Earlier v4 revisions: retained for explicit historical reproduction, not new runs.

## Quick Repository Check

```bash
uv run --locked --extra agentic python -m pytest -q \
  tests/test_v4_r53_active_entrypoints.py \
  tests/test_evas_output_cleanup.py tests/test_task_count_filters.py
```

This is an entrypoint/layout check, not a complete evaluation gate. Follow the
operator guides and verification log for focused harness tests and real
clean-room scoring checks. Do not create top-level scratch/results directories.
