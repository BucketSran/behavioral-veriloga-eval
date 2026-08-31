# Bounded adversarial acceptance and read-only framework integration

Date: 2026-09-01. Base: `c4f2f93e89dddf3cf91ec7716872c5554524921a`.

## Brief

Implement the user's two approved slices independently: adversarial end-to-end
regressions and a read-only Inspect AI results adapter. Framework integration
serves interoperability, analysis and eventually execution throughput, not an
anti-hacking claim. Native/legacy runners already support bounded workers;
result import concurrency is not model-evaluation speedup.

Scope: existing r53 scripted-provider Docker/EVAS fixtures; existing verified
native score readers and reviewer-safe ledger; optional Inspect log export.
Non-goals: changing r53, EVAS 0.8.7, legacy defaults, scoring semantics, retry
ownership, paid models, Spectre, distributed scheduling or new training work.

## KPI and acceptance

- Real Docker/EVAS adversarial cases exercise generation through final scoring,
  or an expected fail-closed boundary, with no paid/model-network calls.
- Successful controls accompany rejection tests; fake diagnostics cannot become
  final passes, and frozen evidence corruption cannot silently trigger replay.
- Export preserves every scheduled row, original zero/null scores, eligibility,
  costs with unknown values, identities, source hashes and paired denominators.
- Export performs zero generation/tool/freeze/judge calls, never overwrites input
  evidence, rejects corruption, and imports into the official Inspect log API.
- Serial and bounded parallel readback are semantically identical. Record import
  timing separately from evaluation timing; no claimed speedup without evidence.
- Focused tests, applicable regression/static/CI checks and independent review
  pass before separate fork-only commits. Raw evidence stays ignored/local.

## Plan and ownership

1. Map existing test fixtures and official Inspect APIs; freeze leaf ownership.
2. Add adversarial tests using production entrypoints and existing fixtures.
3. Add a thin verified-result reader/export adapter using vertical RED/GREEN.
4. Wire focused CI, document code mappings and execution-performance follow-up.
5. Review stable changes, run integration/regression gates and publish focused
   commits only to BucketSran origin/main.

Main owns code unless explicitly delegated in `work-ownership.md`, and owns
all shared records, CI and Git. Read-only advisers have no write authority.

## Risks and stop conditions

Historical sparse fixtures may be unavailable; use active r53 fixtures without
restoring old assets. Inspect remains optional and must not alter the agentic
environment's default dependency/runtime identity. Raw trusted judge material
must not enter an external log. Missing terminal evidence is an explicit import
error, never a fabricated zero or an invitation to execute. Any required change
to benchmark/evaluator semantics or paid-run scope needs a separate decision.

## Execution log and review

Commands, results, RED/GREEN observations and remaining coverage gaps are recorded
in `logs/verification-log.md`; design choices in `logs/decision-log.md`.
Feature notes map the implementation to the underlying ideas and official APIs.
