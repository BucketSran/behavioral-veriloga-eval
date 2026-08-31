# Authorized Verilog-A reference activation

Date: 2026-09-01. Base: `30d1efa9563d7c9600adf28317ba8021edec3448`.

## Brief and acceptance

Activate the user's expressly authorized `Arcadia-1/veriloga-skills` references
in the existing reviewed-v2 offline corpus, for local or declared API-model
context. The user states they contributed to that project and permits this use.
This records the user's authorization, not a newly discovered public license.

Primary KPIs: four pinned source files pass byte-hash verification and load via
`OfflineDocsCorpus`; deterministic representative queries return their sources;
the existing external-context check accepts the declared authorization.
Secondary KPI: reproducible source acquisition and public manifest/evidence
metadata without vendoring reference text. Runtime retrieval remains offline.

Non-goals: new retriever/dependency, entire-skill execution, task solutions,
paid inference, training, scoring-policy changes, EVAS or r53 edits. Cadence is
optional: inspect filenames in existing vaEVAS folders read-only; omit if absent.
Do not restore archives or access AlphaApollo private projects.

## Execution plan

1. Review the four general references at commit
   `7c5d3f03a162ee8131103e9551eee842424360bb` and record authorization evidence.
2. Add a failing manifest/rights regression, then the minimal v2 manifest.
   Fetch exact source bytes only into a fresh ignored reports directory.
3. Verify real local retrieval and opt-in source-byte tests; run adjacent
   corpus/tool and repository navigation regressions. No model calls needed.
4. Independently review the allowlist, provenance, scope and tests. Record
   commands, hashes and validation gaps; publish focused GREEN commits to fork.

Main owns all edits and Git. The native `corpus_source_review` task is read-only
and reviews public references only; no delegated writer or paid lane is open.
Stop on hash drift, source leakage concerns or ownership drift. Do not silently
update the pin, broaden the allowlist or represent ingestion as quality evidence.

## Evidence and remaining risks

Record local corpus location/profile identity and test counts in the verification
log. Manual review is not a mathematical proof of zero benchmark overlap.
The existing single-document/prefix retrieval limits remain; no relevance or
model-performance improvement is claimed by this activation.
