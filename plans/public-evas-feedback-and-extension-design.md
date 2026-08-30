# Public EVAS feedback repair and parallel extension design

Date: 2026-08-31. Base: `8467af3d38d2ffc43361790e27367e57db091755`.

## Brief / approved scope

The user approved advancing the public EVAS feedback repair and suggested
parallel RAG, waveform and SFT/RL work. Main implements the bounded native
feedback/measurement repair; three read-only advisers design future extensions.
They do not activate tools, assemble corpora, export training data or train.
This preserves the prior domain-tool design gate and separate training track.

Layer: behavioral-eval harness. Public process diagnostics must distinguish
the surrounding Bash exit from each sandbox-reported EVAS invocation. Querying
help/version is not a successful simulation; process success is not task success.

## Acceptance / KPIs

1. A failed EVAS process piped to a successful command retains Bash returncode=0
   but exposes EVAS failure to both native interactive policies.
2. The wrapper reports its argv operation, not guesses about the model's Bash
   string. Help/version/other/unknown remain separate from simulate. The public
   marker channel is forgeable: all new data is unauthenticated diagnostic-only,
   never verified process authority, hard-budget input or correctness evidence.
3. Only current-action observations are shown; candidate hashes and invocation
   IDs bind public feedback. Bounded/truncated evidence is explicitly incomplete.
4. Safe feedback contains no private telemetry nonce, raw wrapper command,
   final-test/checker data or behavioral verdict. No-EVAS remains disabled.
5. Legacy defaults and historical no-operation records remain compatible.
   New native behavior is recorded in the frozen runtime configuration.
6. Tests verify actual outgoing model requests, typed observations and readonly
   evidence; free Docker/EVAS smoke checks real wrapper-to-score connectivity.

Primary KPI: all six contracts pass. Secondary: independent review, complete
failure denominator and counter interpretation. No model-quality KPI.

## Ownership and sequence

- Main owns `mini_swe_vabench.py`, native launcher, shared mini-swe bridge,
  invocation summary/report integration, tests, plans/logs/docs and all Git.
- `rag_design`: read-only frozen public corpus/retrieval contract and tests.
- `waveform_design`: read-only public waveform provenance/summary contract.
- `training_design`: read-only separate SFT/RL export/split/reward design.

Use vertical RED/GREEN slices: pipeline failure -> argv operation -> native
request delivery -> reporting/truncation -> Docker and regression. Preserve
exact evidence in the verification log. Publish the tested repair separately
from the main-written extension design synthesis. No red intermediate main.

## Non-goals, risks and stop conditions

No r53/EVAS modification, global Bash pipefail, automatic submission, final
score feedback, installed-example/image policy change, new dependencies, paid
calls, credential reads, old-evidence edits or private AlphaApollo access.
The wrapper's captured stream is bounded, unauthenticated sandbox-report data.
Arbitrary model Bash can forge it without running EVAS. New counters are named
reported_* and quarantined under untrusted_operation_summary; they cannot prove
actual execution and may under/overreport. Host-authenticated per-process
metering requires a separate isolated executor, outside this repair.
Avoid claiming simulation correctness from exit zero. Stop the affected change
if it needs hidden feedback, release changes or additional execution authority.
Extension activation requires its own reviewed corpus/tool/training decisions.
