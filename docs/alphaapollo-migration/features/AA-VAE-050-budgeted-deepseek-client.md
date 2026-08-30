# AA-VAE-050 — Budgeted DeepSeek pilot client

Status: opt-in client and free integration verified; no paid pilot executed.
The ordinary campaign CLI and r53 stopping policy remain unchanged.

## Idea and source

Resource authority belongs to host code, outside model proposals and prompts.
This extends the project's environment-owned budgeting principle to a named
low-cost development pilot; it is not copied AlphaApollo implementation.
The model, CNY/USD pricing snapshot and provider-mode semantics come from
[official DeepSeek documentation](https://api-docs.deepseek.com/quick_start/pricing/)
and [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/).
The frozen design/source links are in `plans/deepseek-budget-pilot.md`.

## Code map and contract

- `benchmark-vabench-release-v4/operations/calibration_pilot/deepseek_budget.py`:
  `DeepSeekPilotBudget` owns the six-cell shared Decimal cap, eight model calls
  per cell and an exclusive private durable journal. `BudgetedDeepSeekClient`
  fixes the official Flash endpoint/model, native tool protocol, temperature 0,
  non-thinking mode, SSE usage and maximum 4096 output tokens. It reuses the
  existing `OpenAICompatible` SSE/transport-capture methods.
- `tests/test_agent_harness_deepseek_budget.py`: free boundary regressions.
- `tests/test_agent_harness_deepseek_budget_smoke.py`: both native backends
  through real Docker, freeze, strict EVAS replay and read-only score checking;
  only the HTTP response is a deterministic free fixture.
- `tests/test_agent_harness_ci_gate.py` and evaluator-closure workflow:
  runtime path triggers and free integration coverage.

Before HTTP, reserve the entire conservative context bound plus output limit at
peak/cache-miss prices, then fsync. Only a complete final SSE usage record with
the expected model, terminal marker, valid integer totals and compatible cache/
reasoning counters can release the unused reservation. Reconciled values are
upper bounds using observed tokens, not provider invoices or estimated tokens.
Unknown/failed requests keep their full reservation and latch a global stop;
the inherited transport cannot silently retry. Call ceilings are cell-local,
so other planned cells may still run if shared accounting remains valid.

The budget is shared across fresh clients, not recreated for each cell. Its
journal cannot be overwritten/resumed; disk errors prevent subsequent HTTP.
Journal entries contain no key, messages, tool arguments or final score. This
is trusted host-side safety code, not protection against arbitrary Python code
deliberately bypassing the client or unrelated processes spending on the account.

## Verification and remaining gate

RED/GREEN covered missing implementation, lack of reconciliation, malformed
usage accepted, absent eight-call ceiling and missing CI selection. Targeted
budget/capture/CI tests passed (35); real native-backend smoke passed (2).
Full regression/static/hosted evidence is recorded in `logs/verification-log.md`.
Neither r53 task bytes nor EVAS 0.8.7 was changed; no dependency was added.

The current general CLI does not instantiate this client. A live driver must
first bind one shared budget to all six backend-qualified IDs, freeze model/
mode/rates/images/code, remove inherited credentials and preserve every
scheduled/censored row. `PilotBudgetStop` is an operational stop, not an
ordinary benchmark failure or a zero score. Those launch/index steps and
actual model/service evidence remain pending credentials; do not run the free
dry-run manifests by simply removing `--dry-run`.
