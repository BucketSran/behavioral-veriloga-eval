# Synthetic extension implementation

> Historical implementation plan. Docs and waveform have since been integrated;
> the synthetic-only training module/tests were retired on 2026-09-01. See
> [current-plan](current-plan.md) for active scope and the
> [AA-VAE-059 retirement note](../docs/alphaapollo-migration/features/AA-VAE-059-synthetic-training-export.md)
> for Git recovery. No historical ownership grant below is active.

Updated: 2026-08-31. Base: `7004ee095fb1e5c21dd4751a2a1ff613c343f32a`.

## Brief and boundaries

Implement the approved AA-VAE-056 first slice: deterministic offline retrieval,
bounded public waveform summaries, and an independent synthetic training-export
contract. Reuse existing controller authorization, budgets and trajectories.
No real corpus, provider call, training, new dependency, final-feedback reuse,
r53/EVAS modification or legacy-default change. Corpus/source declarations are
trusted operator inputs, not automatic proof of license or decontamination.

## Acceptance and frozen first-version limits

- Retrieval: immutable in-memory corpus loaded from a strict synthetic manifest;
  source bytes/hash/license/exclusions checked before use; lexical matching with
  canonical tie-break. At most 64 documents, 64 KiB per document, query 512 chars,
  top_k 1–5 and snippets 600 chars. Network disabled. Corpus/index/profile hashes
  bind responses and the explicit tool capability. Unknown provenance rejects.
- Waveform: parse only a fixed `tran.csv` below a caller-owned output directory;
  reject links, nonregular files, traversal, malformed/duplicate headers and
  nonnumeric cells. Read at most 1 MiB, 10,000 data rows and 32 columns; emit at
  most 8 signals. Empty/nonfinite values are counted, never JSON NaN/Infinity.
  Missing/invalid/too_large/truncated are diagnostics, never task verdicts.
  A parser alone proves no invocation provenance. Only an exclusive fresh public
  invocation may attach its summary to candidate-bound public feedback; arbitrary
  Bash markers or old shared output files cannot authorize that attachment.
- Training: explicit synthetic source, split/license/provider-use declarations,
  canonical provenance and normalizer hashes; separate SFT/RL projections.
  Reject final/trusted/private/unknown sources and all r53 benchmark tasks;
  environment observations are not assistant targets, budget exhaustion is not
  positive SFT, RL reward must be separately declared public validation. No file
  export/CLI or training execution is enabled for real data.
- Integration: optional explicit tool-set composition only, shared authorization
  and budget admission before execution, bounded next-request delivery and
  trajectory/result identity joins. No wildcard activation of reserved tools.
  Preserve default mini-swe/Bash and sealed final authority.

## Sequence and ownership

1. Freeze this brief/KPI/interface plan and assignments before code.
2. Three independent leaves use vertical RED → GREEN (one behavior at a time).
3. Main reviews leaves and implements shared opt-in composition with separate
   regression tests. Do not claim a pure parser/exporter is full runtime support.
4. Independent boundary review, focused tests, full harness suite, static checks
   and free clean-room integration as appropriate. Record unavailable gates.
5. Publish small GREEN commits to BucketSran fork only; preserve prior evidence.

Main owns all shared contracts/launchers/docs/Git and new `tools/__init__.py`.
Leaf ownership is restricted to the module and test pairs in work-ownership.md.
Interface changes are returned to main, not silently spread across modules.

## Stop condition / activation follow-ups

The slice ends with verified synthetic modules and honestly scoped integration,
exact tests and code mappings in migration notes. Actual corpus licensing and
decontamination, real training use authority, paid experiments and matched
tool-effect ablations remain separate decisions. A failed provenance check must
disable the affected extension, never fall back to unbound output.

## Bounded implementation outcome

Three isolated leaves handed back; main owns all shared integration and publication.
AA-VAE-057 adds a synthetic docs Python API for native mini-swe/Reasoning, common
budget admission, next-request delivery and score joins. It deliberately rejects
ordinary aggregate/ledger use until a comparison protocol is frozen. There is
no campaign CLI or Evolution docs path. AA-VAE-058 is a standalone parser only:
the exclusive execution/output receipt prerequisite is not implemented. AA-VAE-059
is a synthetic source projection only, not a native trajectory adapter or trainer.
Feature notes map exact code and verification; logs separate local and hosted gates.
