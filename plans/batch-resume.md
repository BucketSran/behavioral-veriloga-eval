# Batch-level recovery (AA-VAE-070)

## Brief and scope

User request (2026-08-31): implement cross-process native/Evolution batch
recovery, learning from upstream evaluation frameworks rather than replacing
the existing harness. Base: `e46a9d6719893d500071f6cf5ce744d4dc7f439a`.
The owning layer is campaign orchestration, not model policy or final judging.

Completed means a verified terminal record, including a valid zero score or
unscored model failure. It does not mean passing. Recovery never retries based
on candidate quality, resumes a conversation, or refunds an attempt/call budget.
Unknown in-flight execution, incomplete terminal evidence and ambiguous final replay
remain fail-closed. Historical runs without the new frozen batch contract are
not silently adopted. No paid run, credential access, benchmark/EVAS edit,
external service change or new dependency is part of this implementation.

## Acceptance / KPIs

1. Reopening a frozen batch validates source/config/cell roster before clients;
   drift, corrupt receipts and concurrent writers admit zero model calls.
2. Completed cells are verified and reused without model or judge calls;
   missing cells execute with fresh runtimes and remain in the full denominator.
3. Infrastructure recovery uses existing retry policy and immutable attempt
   lineage. Only a sealed, verified safe boundary can authorize a new attempt;
   exhausted caps, unknown required call accounting, cleanup/final/protocol failures cannot.
4. Native and Evolution expose explicit batch recovery without changing legacy
   resume semantics or restoring partial Evolution rounds/shared memory.
5. Free regression and clean-room tests, independent read-only review, exact
   code/source references and focused local commits provide closure evidence.

## Controlled plan

1. Read local contracts; inspect official Inspect AI/Harbor recovery designs.
2. Implement a thin shared frozen batch journal/OS lock using standard library
   and existing atomic publication/evidence readers; test each behavior RED/GREEN.
3. Extend existing native attempt receipts for safe between-attempt recovery;
   wire native campaign scheduling without weakening per-episode no-reentry.
4. Add an outer Evolution batch path, preserving the existing single-cell engine.
5. Run focused, integration, static and navigation gates; independent review;
   record migration rationale/limits and commit independently reviewable slices.

## Risks / stop conditions

Stop affected writes on ownership/source drift. Never infer zero spend from a
missing response or invoke a judge to repair a missing terminal record. Whole
batch recovery is distinct from arbitrary crash recovery inside a cell. Keep
the stopped paid pilot and its historical fee authorization unchanged.

## Evidence

Implemented and independently reviewed. Native/attempt focused gate: 82 passed;
Evolution/native-episode focused gate: 64 passed / 2 optional skips. Three
actual Docker/EVAS cross-process tests reopen completed cells without provider,
credential loading or judge reentry; nine task-form/three-condition/Evolution
regressions pass. Exact full-suite counts and commands are in the verification
log. Upstream citations are design provenance, not evidence that vaEVAS has
implemented every upstream guarantee.

Evolution setup retries are stricter than a generic infrastructure retry: only
bound setup/terminal files and verified zero-start/cost evidence may remain.
Any public-validation/final runtime or unknown lifecycle artifact blocks retry.
Canonical config reconstruction reuses the existing engine builder; completed
score receipt reads reuse the existing production final-judge verifier.

No release/evaluator change, paid experiment, credential read or Git push was
performed. This closes local batch recovery, not arbitrary crash restoration,
historical-output adoption, fee-budget replay or distributed checkpointing.
