# AA-VAE-071 — Legacy/native comparison engineering gates

## Intent and reuse

Continue AA-VAE-069 with a thin, opt-in comparison layer. Reuse the existing
mini-swe/native runners, DeepSeek reservation guard, immutable local evidence publication,
frozen-submission verifier and final-receipt reader. The architecture keeps
controller, environment and final authority separate; it does not import a
second agent framework or translate legacy evidence into fabricated native logs.

## Initial slice: explicit operational limits

`deepseek_budget.py::DeepSeekPilotBudget` accepts explicit `model_call_limit=None`:
the comparison follows r53 wall time without the old pilot's extra eight-call
ceiling. All calls still enter the shared monetary guard. The default stays 8.
`BudgetedDeepSeekClient(..., timeout_s=1800)` permits the same request watchdog
as the runners; the old default stays 120. Invalid watchdogs fail before calls.
Rates/model remain the dated DeepSeek-specific profile, not a general provider
budget system, invoice measurement or newly approved live fee contract.

Tests: `tests/test_agent_harness_deepseek_budget.py` uses the real HTTP payload
boundary with free responses. Nine admitted calls, cross-cell unknown-cost stop,
actual curl watchdog, default preservation and invalid inputs are covered.

## Implemented comparison seams

All runtime paths below are under
`benchmark-vabench-release-v4/operations/calibration_pilot/`.

| File / entry | Responsibility and reused implementation |
| --- | --- |
| `run_legacy_native_comparison.py::freeze_comparison` | Derive two three-task campaigns from AA-VAE-069 without editing its dated blueprint; freeze six ordered cells, image, source bytes, EVAS and shared cost controls. |
| `execute_comparison` | Serial, fresh, one-attempt execution through existing `run_campaign` legacy/native runners and one `DeepSeekPilotBudget`; no reentry/resume. |
| `comparison_surface.py` | Hash complete exported public files and initial submissions; observe actual Docker mounts/image/security; hash effective requests and distinguish common controls from named prompt/tool differences. |
| `comparison_results.py` | Read existing native evidence or legacy generation/freeze/final receipts; join six audit rows and three task pairs without invoking or repairing a judge. |
| `read_comparison` | Bind campaign/source files, terminal/request journal, budget accounting and backend receipts; invalidate matched deltas when surface evidence is absent/mismatched. |

Three optional hooks in `run_campaign.py`, `mini_swe_vabench.py` and
`run_native_mini_swe.py` observe the exported runtime and the live environment
immediately after preflight. They default to `None`; the legacy default path
and native controller behavior are unchanged. Inspection occurs before the
first model request and before container cleanup, not from declarations alone.

```text
freeze six-cell schedule + two campaigns + one shared cost guard
for cell in frozen order:
    export -> observe public bytes -> preflight -> inspect live container
    scripted response -> existing agent/tool loop (every call enters guard)
    existing submission freeze -> existing bound EVAS final judge once
    validate immutable backend receipt -> append terminal journal row
    if guard stopped: retain every later cell as not_started
read-only join -> verify journals/receipts/surfaces -> three matched pairs
```

The legacy envelope binds untouched generation files, the pre-generation final
profile, final request and sidecar. Native evidence keeps its original schema;
legacy data is not converted into fictitious native trajectories. Costs are
guard upper bounds (including unknown reservations), not invoices. Elapsed time
is end-to-end cell time, including setup and final scoring, not inference-only
latency. Null and budget-censored outcomes never become fabricated zero scores.

## Test-first repairs and reference principles

This slice reuses already adopted AlphaApollo interaction/evidence separation
and coding-agent environment adapters; it copies no new external framework.
The external reference rationale remains in AA-VAE-069 and the migration
mainline. New code composes existing tools, budget and final-authority readers.

New regression files are `tests/test_agent_harness_comparison_results.py`,
`tests/test_agent_harness_comparison_surface.py`, and
`tests/test_agent_harness_workflow_comparison.py`; CI wiring is in
`.github/workflows/evaluator-closure.yml` and its existing gate test.
RED/GREEN fixes cover completed-but-missing evidence, incorrect cell/model
bindings, modified projections, cost/request journal drift, symlinks,
non-finite controls, missing/contradictory environment facts, provider-option
differences, tool-result parent IDs, and absent versus present-empty submission.
The empty DUT/Testbench submission directory has a valid empty-tree hash;
absence is missing evidence. Budget stops have their own disposition/reason.

## Scope and remaining live gate

The entry point is deliberately a **free scripted-response Python API**, not a
paid CLI. `_ScriptedComparisonClient` exercises the existing provider payload,
parser and reservation boundary but substitutes the network execution closure.
It loads no credentials and sends no HTTP. Fixture cost figures only test the
guard's arithmetic. Only local sanitized indexes/notes belong in Git, not raw
run roots or unrestricted observations.

Before a real study: add/review the explicit live transport adapter, freeze a
current named service/model/rates/decoding profile, obtain a new fee budget,
then execute a fresh six-cell comparison. Do not reuse either historical pilot
budget. Free scripted submissions test connectivity and accounting, not model
quality or reconstruction of the paper baseline. This is a workflow comparison,
not a pure-controller causal ablation. EVAS 0.8.7 development-only authority and
r53 bytes remain unchanged; DUT/bugfix final authority is held out from feedback
but is not an independently hidden stimulus set. SFT/RL and Spectre are out of scope.

See [the engineering plan](../../../plans/legacy-native-comparison-engineering.md)
and dated verification log for exact commands, source and publication evidence.

Verification checkpoint: local active gate **1,380 passed / 46 optional skips**;
committed-source real Docker/EVAS fixture **41 passed**. Published source
`8609747ccb` passes all three hosted workflows; full-checkout regression is
**1,482 passed / 49 optional skips**, with the new six-cell/censoring stage and
all prior Docker/final checks GREEN. These are engineering results, not model
performance. Local historical fixture failures remain explicitly recorded as
sparse-checkout limitations; excluded history was not restored.
