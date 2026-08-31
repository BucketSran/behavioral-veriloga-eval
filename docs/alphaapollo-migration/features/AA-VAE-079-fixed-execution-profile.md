# AA-VAE-079 — Fixed native execution profiling

Status: implemented; scripted-provider Docker/EVAS evidence, not model quality.

## Idea and reuse

Separate execution throughput from model success and report-import latency.
Reuse the existing r53 clean-room smoke provider, production native launcher,
verified score reader and AA-VAE-078 observation hooks. No external scheduler,
new dependency, paid provider, benchmark change or EVAS modification.

## Code and contract

- `scripts/profile_native_execution.py`: run the same public-stub Agentic cells
  at workers 1/2/4, fresh runtime per run, one attempt, exact cell/attempt binding.
- `tests/test_agent_harness_execution_profile.py`: timing, immutable outputs,
  roster/content/verdict drift, missing evidence and private-exception regression.
- `.github/workflows/evaluator-closure.yml`: real Docker profiling gate.

```sh
.venv/bin/python scripts/profile_native_execution.py \
  --output-root benchmark-vabench-release-v4/reports/my-fresh-profile \
  --native-docker --workers 1,2,4
```

Use `--fixture` for the cheap in-process contract test. Output must be fresh
and have no symlink ancestors; on macOS use canonical `/private/tmp/...`, not
`/tmp/...`, or the repository reports directory. No overwrite/resume is offered.

Queue time is enqueue-to-worker-start. Worker occupancy includes setup/export,
generation, scoring and readback; phase sums are not total wall time. Model
phase includes client recording and internal transport retries, not pure HTTP
latency. `peak_active_cells` is not peak containers. CPU/RAM/container counters
are explicitly unknown. Content digest hashes frozen files independently of
runtime IDs; verdict export contains only status and score.

## Evidence and limits

Three family-001 Agentic tasks exercise DUT, bugfix and Testbench. A 4-worker
configuration can only occupy three cells here. The public stub scores zero;
stable zero verifies the execution/score join, not successful problem solving.
Ten fixture tests cover fail-closed accounting and output protection. Raw runs
and exact timings are recorded in the verification log, never in model memory.

This is a small, fixed-order diagnostic, not a warmed/randomized performance
study or a recommendation for production concurrency. Real service throttling,
larger workloads, resource telemetry and repeated timing trials remain separate.
No resource-control or Inspect execution migration is justified by this smoke.
