# Execution profiling and multi-path reporting

Date: 2026-09-01. Base: `3aa5129a112c220c546dd1e2004d22903860ba30`.

## Brief and approved scope

Implement the user's approved next iteration in behavioral-veriloga-eval:
observational phase timing, a repeatable scripted-provider workers=1/2/4
Docker/EVAS workload, and read-only reporting for legacy comparison,
Evolution and combined tools. Reuse native execution, retry, verified readers
and the optional Inspect log API. No new scheduler or third-party dependency.

Frozen non-goals: r53/EVAS 0.8.7, default legacy behavior, score/selection/budget
semantics, paid provider calls, Spectre, private project imports and old trees.
Inspect execution delegation is not approved for this slice. Resource-control
changes require measured evidence; no speedup target is assumed.

## KPIs and acceptance

- Timings identify cell/attempt and actual measured stages; unobserved phases
  remain null/absent. Nested/parallel spans are not summed into total wall time.
- Observability does not expose private payloads to models or change stop,
  retry, freeze or final-score authority. Failures retain original exceptions.
- The fixed public-stub workload executes fresh cells through production
  native code at 1/2/4 workers, records throughput/latency/accounting and rejects
  missing/duplicate cells or mismatched submitted content/verdicts.
- Export reuses each path's verified reader, preserves separate estimands,
  all-branch/attempt costs, zero/null scores and provenance. No model, tool,
  freeze or judge invocation; outputs never overwrite inputs.
- Targeted tests, optional official Inspect tests, real Docker/EVAS evidence,
  applicable static/regression checks and independent review precede delivery.
- No real-model quality, causal tool benefit, complete resource observation or
  performance improvement claim beyond the measurements actually collected.

## Sequence and ownership

1. Commit this scope and ownership record.
2. Main implements phase observation and profiling through vertical RED/GREEN.
3. A bounded exporter delegate implements only its assigned leaf files/tests;
   main owns integration, shared docs/CI and all Git operations.
4. Measure fixed runs; retain existing scheduling unless evidence justifies a
   specific small correction. Report unavailable resource counters explicitly.
5. Independent read-only review; focused commits for runtime/profiler, exporter
   and integration records; push only BucketSran origin/main.

Use existing ignored reports roots for raw smoke data. Commands, RED/GREEN,
measurements and review outcomes go in logs/verification-log.md; choices in
logs/decision-log.md; code/idea mapping in the migration feature notes.

## Risks and stop conditions

Source/ownership drift, hidden-output leakage, changed final/retry semantics or
required fees stop the affected branch. Missing historical sparse fixtures are
reported separately; do not restore bulk assets or label optional skips passes.
Instrumentation coverage and actual service rate-limit tests remain explicit.

## Implementation outcome

AA-VAE-078 timing, AA-VAE-079 fixed workload and AA-VAE-080 multi-path reporting
are implemented. Independent reviews completed after fail-closed profiler
repairs; actual Docker and official Inspect tests pass. See verification log
for fresh measurements and final regression/publication evidence.

Scope clarification: Evolution export covers one terminal attempt and its
available all-branch costs, not every attempt of a retry batch. The adapter
does not manufacture unavailable costs or an expanded candidate DAG. Whole-batch
aggregation, paired-delta visualization, resource sampling and statistically
controlled performance trials remain follow-ups. No scheduler rewrite occurred.
