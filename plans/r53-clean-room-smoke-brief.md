# Task Brief: r53 Three-Condition Clean-Room Smoke

## Task

Implement a deterministic VABench r53 integration smoke that executes the
three declared evaluation conditions, records an auditable trajectory, freezes
the final submission, and scores it with pinned EVAS 0.8.7.

## Layer

`behavioral-veriloga-eval`

## Scope

1. One frozen r53 task and one deterministic scripted provider/agent behavior.
2. Fresh isolation for `One-shot`, `Agent-No-EVAS`, and `Agentic+EVAS`.
3. Append-only event evidence with condition, attempt, candidate, submission,
   evaluator, and verdict bindings.
4. Strict EVAS trusted replay and an immutable structured score sidecar.
5. Targeted tests, one reproducible smoke command, and CI coverage.

## Non-goals

1. Reproduce paper baseline Pass@1 or rerun the common-300/full-1,200 campaign.
2. Modify r53 task bytes, EVAS code, EVAS packaging, or scoring semantics.
3. Add Spectre to the routine development or CI path.
4. Claim model quality, feedback causality, or simulator equivalence.

## Constraints

1. Benchmark identity is r53 at
   `7b5616dc52195ec275ec6d21c71d7763613702cd`.
2. Evaluator identity is `evas-sim==0.8.7` at
   `6cb6fa7a7dac70fc0d4120126d8cf74258e6637b`.
3. Hidden evaluator inputs are unavailable until the generation episode ends.
4. Each condition uses a new sandbox, candidate tree, and attempt identifier.
5. Formal evidence fails closed on missing structure or identity mismatch.

## Acceptance

1. A public command produces three terminal condition records for one r53 task.
2. Only `Agentic+EVAS` records an allowed public EVAS invocation.
3. Every event and sidecar verifies against the frozen submission hash.
4. The EVAS sidecar records version 0.8.7 and a structured verdict.
5. The output explicitly limits the claim to pipeline connectivity.

## KPIs

1. `three_condition_clean_room_smoke = pass`.
2. `trajectory_submission_score_join = pass`.
3. `identity_and_leakage_fail_closed = pass`.

## Required Logs

1. Exact commands and runtime identity.
2. Output paths and content hashes.
3. Per-condition terminal and capability state.
4. `dut_compile`, `tb_compile`, `sim_correct`, and weighted verdict.
5. Any infrastructure or candidate failure attribution.
