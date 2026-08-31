# AA-VAE-071 — Legacy/native comparison engineering gates

## Intent and reuse

Continue AA-VAE-069 with a thin, opt-in comparison layer. Reuse the existing
mini-swe/native runners, DeepSeek reservation guard, immutable publication,
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

## Remaining integration

The shared six-cell launcher, actual export/environment/request audit and
read-only legacy/native join are being implemented under
[the engineering plan](../../../plans/legacy-native-comparison-engineering.md).
Do not treat these initial parameters alone as completed launch gates.
No paid experiment, benchmark/EVAS change or model-quality result is included.
