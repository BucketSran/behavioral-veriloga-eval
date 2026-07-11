# Phase 1 Evidence v2 Closeout

Status: implemented, regression-tested, and exercised on canonical DUT 001-080
on 2026-07-11.

This phase changes evidence validity from whole-release-lock equality to exact
component identity. `TOOLCHAIN_LOCK.json` remains the release snapshot and
preflight allowlist; its SHA is provenance, not a universal cache key.

## Implemented surfaces

- `scripts/evidence_fingerprints.py` computes task, checker, AHDL-like, EVAS,
  and Spectre component identities and returns an explicit reuse decision.
- `scripts/run_v4_first_n_spectre.py` emits Spectre evidence v2. Its simulation
  cache excludes checker code and release-snapshot SHA; cached raw traces are
  re-evaluated by the current checker.
- `scripts/certify_v4_mutations.py` emits mutation evidence v2, uses separate
  backend cache keys, and marks cache-derived records `carried_forward`.
- `scripts/promote_v4_mutation_certifications.py` emits negative certification
  v2 when component fingerprints exist. Legacy v1 input remains snapshot-bound
  and cannot be silently upgraded.
- `scripts/seal_v4_gate2_certifications.py` validates exact backend components
  and emits composed task certification v2.
- `scripts/audit_v4_strict_readiness.py` reports the precise stale Spectre
  component instead of requesting a whole-suite rerun.
- `scripts/index_v4_evidence.py` indexes immutable v1/v2 records and explains
  whether each represented backend can be reused, needs component recovery, or
  must be rerun.
- The first-N, negative-certification, and task-certification schemas accept
  both v1 and v2 records. v2 records require component and release provenance.

## Decision contract

For one task/profile/backend record:

- release-snapshot changes do not invalidate evidence;
- a change in another backend does not invalidate this backend;
- task input, deck, harness, profile, trace-contract, or selected backend
  changes rerun only this backend;
- checker-only changes reuse a complete stored trace and re-run the checker;
- checker changes with a missing raw trace or required signal rerun only the
  affected backend;
- v1 whole-lock equality alone is not proof of current EVAS/AHDL identity.

## Verification

The focused evidence-v2 and first-N Spectre runner suites pass:

```text
32 passed
```

The suite covers independent EVAS/Spectre invalidation, unrelated checker
changes, checker-only trace reuse, missing-trace-signal fallback, task-local
harness invalidation, v1 compatibility, v2 promotion, precise readiness
diagnostics, and seal-time backend rejection.

A read-only migration probe of the historical first-120 Spectre evidence is:

```bash
python3 scripts/index_v4_evidence.py \
  reports/first_n_spectre/first120.json \
  --toolchain-lock TOOLCHAIN_LOCK.json \
  --output /tmp/v4-phase1-first120-migration-index.json
```

Observed result:

```json
{"record_count": 120, "action_counts": {"reuse": 120}}
```

This result proves reuse of the represented Spectre backend identity only. It
does not certify current EVAS, checker strength, property coverage, or Gate 2.
Those remain Phase 2 work for DUT 001-080.

A strict 001-080 audit after removing whole-numbering-snapshot coupling found:

- all 80 historical v1 rows retain a matching Spectre backend identity but
  need current checker re-evaluation before Gate 2 sealing;
- 031, 032, 048, 061, and 070 have changed task/harness/profile inputs that
  require task-local evidence review;
- 048 has an untriaged Spectre warning;
- 061 also has a changed gold bundle;
- the known Gate 3 property-coverage gaps remain 061, 067, 069, 073, 075, 076,
  and 078.

## Canonical DUT 001-080 exercise

The final component-scoped exercise used lock SHA256
`6b5e46397612f6ac536118be91bfd1294d3d5976b92a697e16d3fd441e59ac9f`
and EVAS runtime commit `55729488140cdc5f8f47dc476c54d0dad665dde6`.

- EVAS evidence:
  `/tmp/v4-phase1-local-evas-001-080-v2.final.json`
  (`f7c3a9600e21f1bffd1c3695a933ebbca6dfaa5cd96b7ffda5fc7fb9ca9761c8`),
  160/160 feedback and score runs passed.
- Spectre evidence:
  `/tmp/v4-phase1-spectre-001-080-v2.final.json`
  (`a925d50fa9917c0e661384a5ad989cc93a0a779ecc98d35216e7e76cb0717627`),
  80/80 score rows passed with zero untriaged warnings.
- Strict audit:
  `/tmp/v4-phase1-strict-readiness-001-080.final-v2.json`
  (`ec9a0a2ce0f8bfff7e8f5bcb576ddfd977e4ea96da5148757e24764dfcdf35f3`),
  Gate 2 ready count 80/80.

The first Spectre pass reused 74 exact simulation caches and reran only 031,
032, 048, 049, 061, and 070. Subsequent checker and EVAS changes replayed all
80 Spectre checkers from stored traces with zero remote executions. This is the
intended evidence-v2 behavior: EVAS changes invalidate EVAS evidence but not an
unchanged Spectre backend; checker changes invalidate derived decisions but not
complete compatible traces.

Gate 3 remains 73/80. Property and mutation-activation coverage is still
incomplete for 061, 067, 069, 073, 075, 076, and 078. Gate 2 completion must
not be reported as final mutation-strength completion for those seven rows.

## Parallel-work boundary

Lanes working on DUT 081-400 should retain raw traces/logs and supply component
hashes in their handoff, but should not refresh `TOOLCHAIN_LOCK.json` or seal
tasks. Codex imports accepted records, re-evaluates current checkers, and owns
the final component-scoped seal.
