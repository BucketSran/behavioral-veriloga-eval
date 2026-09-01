# Real-model Differential And Incremental Study

Status: implementation and free clean-room validation complete; paid execution
blocked until an exact aggregate fee cap and credential-file path are supplied.
Updated: 2026-09-01. Integration owner: main.

## Fixed baseline and purpose

This is a bounded diagnostic over the sealed VABench r53 release and EVAS 0.8.7.
It does not modify the benchmark, evaluator, legacy default, corpus bytes or final
score authority. The live provider contract reviewed on 2026-09-01 names
`deepseek-v4-flash` (`DeepSeek-V4-Flash-0731`), temperature 0, provider thinking
disabled and a 4,096-token output cap. The alias is not an immutable snapshot.

The two studies answer different questions and must not be pooled:

1. Does the opt-in native mini-swe harness change the observable workflow or
   result relative to legacy mini-swe under one model, task and shared budget?
2. Within the native harness, what is the observed single-task increment from
   the reviewed RAG plus public-waveform surface, and how does that observation
   differ between single-trajectory Reasoning and multi-branch Evolution?

These are engineering diagnostics, not a reproduction of the paper baseline,
a population estimate, a formal benchmark result or an individual-tool causal
ablation. One family is deliberately used to bound cost and debug evidence.

## Study 1 — six-cell legacy/native differential

Entrypoint: `comparison_live.py`. One frozen root owns one shared spending guard
and the following ordered roster:

| Order | Family | Form | Backend |
| ---: | --- | --- | --- |
| 1 | 001 | DUT | legacy-mini-swe |
| 2 | 001 | DUT | native-mini-swe |
| 3 | 001 | bugfix | legacy-mini-swe |
| 4 | 001 | bugfix | native-mini-swe |
| 5 | 001 | Testbench | legacy-mini-swe |
| 6 | 001 | Testbench | native-mini-swe |

Freeze the same public source, model contract, Docker image identity, EVAS
identity, decoding, per-turn limit and total approved cap. The reader preserves
all six scheduled rows, including unstarted/budget-stopped rows. Primary output
is the three paired records: disposition, development EVAS score, request/public
surface equality, model calls, conservative guard upper bound and elapsed time.
Do not retry a wrong answer or choose another task after seeing a score.

Interpretation:

- equal surface and equal scores support workflow compatibility on this slice;
- a surface mismatch blocks attribution to controller behavior;
- a score delta is a case finding to inspect through frozen evidence, not a
  benchmark-level quality claim;
- an infrastructure stop remains in the denominator and is not converted to 0.

## Study 2 — 2×2 backend/tool increment

Entrypoint: `run_combined_tools.py`. Use four fresh roots with the same family001
DUT source, model/provider profile, EVAS/Docker identities and per-backend limits.
Freeze the intervention explicitly; absence of tools is an audited condition,
not an omitted field in analysis.

| Cell | Backend | Intervention | Public information surface |
| --- | --- | --- | --- |
| A | native-reasoning | baseline | Bash only; no reviewed docs or public waveform |
| B | native-reasoning | rag-waveform | reviewed docs plus candidate-bound public waveform |
| C | evolution | baseline | isolated branches; no reviewed docs or public waveform |
| D | evolution | rag-waveform | isolated branches plus reviewed docs and round-barrier waveform feedback |

Each condition must pass `condition_acceptance_passed`: enabled tools must have
complete successful evidence; disabled tools must have zero attempt, success,
feedback exposure and incomplete evidence. `combined_acceptance_passed` is true
only for the two `rag-waveform` conditions. Read-only reporting records the
intervention in both identity and group, so baseline and tool-enabled results
cannot be silently collapsed.

Report the four raw rows before any difference:

- B − A: single-trajectory observed tool-surface increment;
- D − C: Evolution observed tool-surface increment;
- C − A: configured Evolution-system difference without public tools;
- D − B: configured Evolution-system difference with public tools;
- `(D − C) − (B − A)`: descriptive interaction only.

Scores are binary development EVAS outcomes on one task. Evolution uses two
branches for two rounds and is not compute-matched to native Reasoning. Therefore
C − A and D − B are configured-system effects, not pure backend effects. Always
report actual branch/model calls, cost bounds and complete branch denominators.

## Spending, launch and stop contract

No amount is implied by this plan. A paid launch requires a new exact aggregate
fee authorization and an external owner-only literal credential-file path.
Study 1 uses one shared cap. Study 2 currently uses one guard per condition, so
the frozen four condition caps must sum to no more than the separately approved
Study 2 aggregate ceiling; do not quote only a per-root cap as the total risk.

The 2026-09-01 official CNY schedule is frozen in the provider profile: input
cache hit 0.05/0.10, cache miss 1.50/3.00 and output 4.50/9.00 per million tokens
for off-peak/peak respectively. USD schedules are also recorded. The runtime
reserves conservatively at peak rates; guard upper bounds are not invoices.

Stop without replacement on manifest/profile drift, stale review date, unknown
cost, preflight failure after launch reservation, exhausted guard, incomplete
terminal evidence, candidate/final binding failure or any attempted reentry.
Preparation and inspection are free but must freeze the approved numeric caps;
therefore placeholder-cap preparations are not valid launch artifacts.

## Required evidence and claim boundary

Before a paid call, record exact manifest hashes, source commit, r53 manifest,
resolved Docker IDs, EVAS 0.8.7 identity, corpus profile, credential metadata
only, fee caps and ordered roster. After execution, use only the existing
read-only report paths. Never refreeze, repair, rejudge or feed final scores into
Evolution memory while producing the report.

Minimum deliverables are the six-cell comparison report, four condition reports,
safe read-only ledgers, full denominators, actual call/cost counters, frozen
submission and EVAS sidecar joins, plus a short case analysis for every mismatch.
The maximum justified claim is a bounded single-family engineering observation.

Official provider references reviewed for this protocol:

- <https://api-docs.deepseek.com/>
- <https://api-docs.deepseek.com/zh-cn/quick_start/pricing/>
