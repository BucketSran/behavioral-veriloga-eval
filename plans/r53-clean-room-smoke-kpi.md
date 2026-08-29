# Task KPI: r53 Three-Condition Clean-Room Smoke

## Goal

Prove that the current r53 harness can produce trustworthy, joinable
generation-to-score evidence under the pinned EVAS 0.8.7 evaluator.

## Primary KPI

1. `three_condition_terminal_records = 3/3`.
2. `hidden_evaluator_visible_during_generation = 0/3`.
3. `unauthorized_evas_capability = 0/2` for One-shot and Agent-No-EVAS.
4. `authorized_agentic_evas_invocation >= 1`.
5. `structured_evas_0_8_7_sidecars = 3/3`.
6. `submission_hash_mismatches = 0`.

## Secondary KPI

1. Targeted test suite passes deterministically without a live model API.
2. One documented command reproduces the evidence in a fresh runtime.
3. Every failure is classified as candidate, invalid submission, or
   infrastructure; cleanup incidents remain separate.

## Guardrails

1. Do not modify the r53 release or EVAS repository.
2. Do not use the smoke as model-performance evidence.
3. Do not silently enable network, retrieval, persistent workers, or private
   evaluator mounts.
4. Do not accept an unstructured zero-exit judge result as a pass.

## Required Evidence

1. Exact targeted-test and smoke commands.
2. Runtime and source identity records.
3. Per-condition trajectory, frozen submission, and score-sidecar paths.
4. Verification summary and any residual validation gap.
