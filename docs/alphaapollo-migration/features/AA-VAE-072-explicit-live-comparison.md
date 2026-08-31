# AA-VAE-072 — Explicit live comparison transport and launch gate

## Intent and reuse

AA-VAE-071 supplied the free six-cell engineering chain. This slice adds a
separate `comparison_live.py` entrypoint, not another agent loop, budget system
or scoring implementation. Preparation does not authorize spending. No real
provider call or credential is used in this implementation's verification.

The architecture follows the existing controller/environment/provider split:
the provider adapter owns HTTP and response normalization; the coordinator owns
the schedule, public-surface checks, budget and terminal evidence. We reuse
`BudgetedDeepSeekClient`, `DeepSeekPilotBudget`, `pilot_credentials.load_pilot_key`,
the pilot's sanitized metadata preflight, and AA-VAE-071's existing runner and
read-only result joins. No third-party implementation or new dependency is copied.

## Provider contract and primary sources

Official documentation checked 2026-08-31:

- [Models/pricing](https://api-docs.deepseek.com/quick_start/pricing/) and
  [CNY pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/):
  `deepseek-v4-flash`, current documented version `DeepSeek-V4-Flash-0731`,
  peak cache-miss input/output per million CNY 3/9 or USD 0.44/1.32.
- [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
  and [thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/):
  explicitly disable thinking, temperature 0, streaming with usage enabled.
- [First API call](https://api-docs.deepseek.com/) describes the compatible
  endpoint and alias. The request uses the alias, not an undocumented snapshot
  request ID. Recorded version metadata does not make an alias immutable.

The local 4096 output cap is an experiment control, not the provider maximum.
The existing guard reserves a conservative 1,048,576-token input at peak/miss
prices, then releases only a validated usage difference. Its journal's
`pricing_date=2026-08-30` is the guard's historical review label, not the official
price-effective date; the new profile records the separate Aug31 review.
The unchanged guard only supports CNY caps up to 5.00 or USD up to 0.70.
These supported maxima are not new user spending authorization.

The v1 profile is launch-valid only on its reviewed UTC day (2026-08-31).
Expired profiles remain inspectable/readable but cannot launch. A later launch
requires another official rate/contract review and fresh preparation; do not
edit a frozen file, automatically renew dates, or reuse an old approval/budget.

## Code map and sequence

| Responsibility | Code |
| --- | --- |
| Dated provider profile, exact cap/currency/hash assertion, CLI | `operations/calibration_pilot/comparison_live.py` |
| Observed live HTTP with existing reservation/SSE capture | `comparison_live.py::LiveComparisonClient` → `deepseek_budget.py::BudgetedDeepSeekClient` |
| Shared six-cell engine; distinct free/live preparation | `run_legacy_native_comparison.py::freeze_comparison`, `_execute_comparison` |
| Authorization/preflight hash joins, read-only transport accounting | `comparison_live.py::validate_live_authorization`, `validate_provider_preflight`; `read_comparison` |
| Free boundary and real Docker/EVAS regressions | `tests/test_agent_harness_comparison_live.py`; `.github/workflows/evaluator-closure.yml` |

Runtime paths above are under `benchmark-vabench-release-v4/`.

```python
prepare(named_profile, exact_cap, image_id, source_bytes, r53, evas_identity)
inspect()  # no key, HTTP, generation, freeze or judge
run(expected_manifest_hash, approved_cap, currency):
    validate_frozen_inputs_and_current_profile()
    validate_local_evas_and_image()
    reserve_operator_assertion_once()  # not authenticated human identity
    load_external_owner_only_literal_key()
    read_sanitized_provider_metadata_and_check_currency()
    for cell in frozen_six_cell_schedule:
        existing_runner(observed_budgeted_live_client)
        preserve_original_freeze_and_final_receipt()
    read_existing_evidence_without_rejudging()
```

`live_authorized=false` remains on the immutable preparation. Only the separate
one-use `live-authorization.json` records the operator's exact launch assertion.
`provider-preflight.json` stores availability/currency and response hashes, not
account balance. Both receipts are bound to the execution projection/report.
Failure after reservation cannot automatically retry, even if it occurred before
generation. Historical free v1 manifests stay free and reject live execution.

Live reports use `paid_requests=null` because invoices are not observed.
`potentially_billable_attempts` counts durable transport reservations, including
ambiguous attempts; it is not a charge count. Scripted free API reports keep
`paid_requests=0`. Explicit `run` returns nonzero on incomplete/censored rows.
The existing `request_observed` event fingerprints a prepared logical payload
before monetary admission; it does not prove HTTP was sent. Count reservations
and transport captures separately, never infer paid calls from that event.

## Tests and boundaries

Vertical RED/GREEN checks cover missing entrypoint; drift before credential
loading; expired launch/current read; shared live transport admission; output
cap drift before HTTP; authorization/preflight tampering; no implicit CLI launch;
real six-cell scoring with synthetic external HTTP; both fee-stop modes; no
metadata/model/judge reentry; and CI wiring.

The real integration fixture substitutes only external metadata/HTTP responses;
it executes the actual curl payload/capture boundary, Docker tools, submission
freeze and EVAS sidecars. Synthetic public stubs may score zero. This proves
engineering connectivity, not real-model performance or a paper baseline.

Local evidence: **62 real Docker/EVAS checks passed**, external responses
synthetic; active harness/r53 regression **1,398 passed / 50 optional skips**;
workflow contracts **20 passed**. Independent read-only source review found no
required correction. Test-first implementation also caught and repaired the
new CLI's incorrect tuple unpacking of the existing EVAS identity dictionary.
Runtime commit `00eb11e7c1` and CI commit `39123500cc` are separate review units;
exact-source hosted evidence is recorded in `logs/verification-log.md` after
publication. These local checks do not claim a full typecheck or paid run.

No r53 or EVAS 0.8.7 change; no default legacy switch, new controller,
cross-cell memory, training or Spectre path. Alias drift, a conservative guard
rather than invoice enforcement, and DUT/bugfix's shared visible replay stimuli
remain explicit limitations. Fresh paid execution still requires user agreement
on currency/cap and inspection of the exact prepared profile/hash.
