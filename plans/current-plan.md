# vaEVAS r53 Evaluation Closure Plan

Updated: 2026-08-29

## Objective

Close the current VABench r53 evaluation path around a pinned EVAS 0.8.7
judge without modifying either frozen dependency. The first executable
milestone is a deterministic one-task, three-condition clean-room smoke that
joins trajectory evidence to an immutable submission freeze and structured
score sidecar.

## Frozen dependencies

- Benchmark: `benchmark-vabench-release-v4/release/benchmarkv4-r53/`, commit
  `7b5616dc52195ec275ec6d21c71d7763613702cd`.
- Evaluator: `evas-sim==0.8.7`, tag `v0.8.7`, commit
  `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
- The r53 release and EVAS repository are read-only for this work.
- Spectre is outside the routine smoke path and is activated only by an EVAS
  change or an explicitly named external protocol.

## Historical foundation

- The completed v3 evaluator environment, Docker smoke, and claim-gate work is
  retained as reusable infrastructure evidence.
- V3's empty score roster is not a blocker for the r53 smoke and must not be
  used as the r53 denominator.
- The pre-r44 DeepSeek calibration pilot remains exploratory provenance, not a
  formal r53 baseline result.

## Steps

- [x] Freeze the benchmark and evaluator identities as r53 + EVAS 0.8.7.
- [x] Map the existing v4 runner, trajectory, submission, and
  trusted-replay interfaces; define the smoke brief and KPIs.
- [x] Add one failing public-interface regression for the deterministic r53
  smoke, then implement the smallest end-to-end path.
- [x] Extend the smoke across `One-shot`, `Agent-No-EVAS`, and
  `Agentic+EVAS`, enforcing capability isolation in code.
- [x] Bind append-only trajectory events to candidate hashes, the frozen
  submission tree, and an immutable EVAS 0.8.7 score sidecar.
- [x] Add targeted CI coverage and document the reproducible smoke command.
- [x] Run focused tests, the real clean-room smoke, static checks, and
  `git diff --check`; append exact evidence to the verification log.
- [x] Independently review leakage, retry, cleanup, judge identity, and claim
  boundaries before marking this milestone complete.

## Stop condition

One command executes a single frozen r53 task in three fresh condition-specific
clean rooms and emits machine-checkable evidence proving:

1. only `Agentic+EVAS` can invoke public EVAS;
2. no condition can access the hidden evaluator during generation;
3. trajectory events join to the exact frozen submission tree;
4. strict trusted replay observes EVAS 0.8.7 and emits a structured sidecar;
5. missing identity, missing structured verdict, hash drift, or capability
   leakage fails closed;
6. the smoke claim remains pipeline-only and cannot be promoted to a model
   performance or aggregate benchmark claim.

## Open risks

- Current smoke trajectory evidence is intentionally smoke-local; promotion
  into the general campaign schema should be a separate compatibility change.
- Retry lineage and cleanup incidents still need first-class campaign-wide
  records so infrastructure recovery cannot obscure the primary episode result.
- Docker availability remains a CI/runtime prerequisite for the agentic arms;
  non-container fallback evidence is compatibility-only and cannot satisfy the
  clean-room KPI.
