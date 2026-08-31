# R53 public execution contract compatibility

2026-08-31. Base: `1c73e519bdaf2a3a3a62953fbc0472ff33a39f6c`.

## Brief and KPI

Repair the harness adapter that rejects the sealed portable public contracts
for families 102 and 112 (DUT, bugfix and Testbench: six tasks). The preceding
analysis and user acceptance settle this bounded scope; no interface or scoring
design decision is missing. Layer: behavioral-veriloga-eval, not EVAS.

Primary KPI: all 1,200 released public runtime contracts are recognized by the
production selector, preserving their exact command and feedback scope.
Secondary KPIs: rejected mixed/unknown/injected contracts; portable command
propagation through public observation and isolated waveform paths; fresh
clean-room trajectory -> freeze -> EVAS score-sidecar connectivity.

Guardrails: sealed r53 bytes, EVAS 0.8.7, strict commands, legacy default,
reference-only Testbench feedback, final non-reentry, candidate binding and
selection/score semantics remain unchanged. No provider call, hidden-content
inspection, new public behavioral checker, waveform metric, RAG or training.
Source changes alter future profile hashes; historical evidence is not rewritten.

## Plan and ownership

1. Record baseline and scope separately from runtime changes.
2. RED -> GREEN for released portable DUT/bugfix contracts, then Testbench.
   Select only fixed command variants; never execute arbitrary metadata.
3. Add all-release coverage and malformed/mismatched contract regressions.
   Verify command propagation, authority drift and existing strict behavior.
4. Run focused tests, harness/campaign gates, static checks and fresh Docker
   clean-room smoke with scripted public candidates, not a model baseline.
5. Independent read-only review; record limitations and exact verification.
   Publish focused GREEN commits only to BucketSran origin/main.

Main exclusively owns `operations/calibration_pilot/public_validation.py`
(under `benchmark-vabench-release-v4/`), related existing production-public-
validation/public-waveform tests, any new public-contract coverage test,
`tests/test_agent_harness_waveform_integration.py` and
`tests/test_agent_harness_evolution_campaign.py` for portable clean-room cases,
applicable CI gate, calibration README, this plan/current-plan/work-ownership,
decision/verification logs and AA-VAE-067 migration note/index. No other runtime
surface is preauthorized; expand the recorded scope if consumer evidence
requires it. `portable_contract_review` is read-only test/consumer advice;
a separate final reviewer has no source or Git write authority.

Consumer audit: `run_campaign.run_public_evas` also has old schema allowlists,
but it belongs to the separate legacy `--agent-scaffold native` sensitivity
tool, not default mini-swe or the active native/Evolution fixed validator.
Leave that legacy compatibility issue explicit and unchanged in this slice.

Integration finding: the portable v4-102 DUT public support uses dynamic array
access rejected by pinned EVAS 0.8.7. Keep an explicit negative execution test
(failed observation, nonzero exit, named unsupported-feature diagnostic); do
not modify support/release/evaluator bytes or relabel this as simulation success.
Scripted Evolution DUT/Testbench family 102 candidates produce terminal
`compile_failure`, unlike the original family 001 `behavior_failure` stubs.
Assert each known verdict explicitly and retain freeze, hash, one-final and
memory-isolation checks; record actual final status in the local smoke index.

## Evidence and stop conditions

Keep commands, RED/GREEN counts, static/independent review outcomes and source-
bound smoke evidence in `logs/verification-log.md`. Use fresh ignored reports
directories for local output; publish only compact hashes/counts, never raw
trajectory or checker diagnostics. A failed simulation is not automatically an
adapter failure or a task verdict.

Stop this slice if it requires release/evaluator changes, score/selection policy
changes, credentials, or materially broader public feedback. Report unavailable
Docker/static gates explicitly rather than claiming full closure.

## Review

Implementation and independent read-only review are complete with no blocking
finding. Final focused gate: 192 passes / 20 opt-in skips. Three real Docker
groups cover 17 passing cases (including explicit failed-execution/verdict
expectations); exact invocations and the initial failed run remain in the log.
Fork publication and source-bound hosted verification are still in progress.
LSP/typecheck is unavailable, so record Ruff/compilation/AST as narrower evidence.
This work repairs contract coverage; it does not establish full-1,200 simulation
success or model-quality gains. The legacy sensitivity consumer and pinned
EVAS dynamic-array limitation remain separately named residual issues.
