# Budget-controlled DeepSeek pilot

Date: 2026-08-30. Base: `38375909aee7103df154c72b2c3d7f3fbb3dee1c`.
Status: authorized pilot; preparation only until credentials and tested
pre-request spend protection are available. No paid request has been made.

## Brief and KPI

The user chose the cheapest currently available DeepSeek model and delegated
the remaining experiment choices, with budget control required. This work owns
the behavioral-eval pilot, not EVAS or released task content.

Primary acceptance: at most CNY 5.00 for requests launched by this pilot;
complete scheduled/started/stopped denominators; reproducible model/tool
trajectories joined to immutable submission/final EVAS evidence where eligible.
Secondary observations: backend protocol failures, compile/runtime/behavioral
outcomes, measured usage and wall time. No pass-rate or superiority threshold
is an acceptance criterion for this small engineering pilot.

Non-goals: full r53 evaluation, paper-baseline reproduction, model-quality
claims, Evolution, model training, domain/RAG tools, Spectre, new dependencies,
automatic recharge, external GPU rental or private-project access. Legacy
defaults, r53 bytes and EVAS 0.8.7 remain unchanged.

## Model and official rate snapshot

Use the official DeepSeek service and `deepseek-v4-flash`, documented as
`DeepSeek-V4-Flash-0731`. The same-price experimental vision model is unnecessary
for this text-only experiment. Recheck model availability before paid execution;
record both requested alias and observed response identity, without claiming an
immutable provider snapshot when the service exposes only an alias.

Official sources read on 2026-08-30:

- [CNY model/pricing table](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)
- [USD model/pricing table](https://api-docs.deepseek.com/quick_start/pricing/)
- [Thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/)
- [Model availability](https://api-docs.deepseek.com/api/list-models/)
- [Account balance](https://api-docs.deepseek.com/api/get-user-balance/)

Per million tokens, Flash rates are:

| Item | CNY off-peak | CNY peak | USD off-peak | USD peak |
| --- | ---: | ---: | ---: | ---: |
| Input, cache hit | 0.05 | 0.10 | 0.007 | 0.014 |
| Input, cache miss | 1.50 | 3.00 | 0.22 | 0.44 |
| Output | 4.50 | 9.00 | 0.66 | 1.32 |

Peak is Beijing Monday-Friday 09:00-12:00 and 14:00-18:00. Use peak,
cache-miss rates for protective accounting, independent of launch time/cache.
If the account is USD-denominated, use a separate USD 0.70 cap, not an assumed
exchange-rate conversion. This limit covers this pilot only, not concurrent
spending by unrelated processes on the account.

## Frozen experiment design

- Select one complete family by seed `20260830`, before inspecting outcomes.
- Three public forms: DUT, bugfix, Testbench; one repetition each.
- Two separate matched campaigns: `native-mini-swe` and `native-reasoning`.
- Both use the Agentic arm, the same model, public task, image, decoding,
  per-call output cap and evaluator. This is a backend comparison, not an
  EVAS/no-EVAS effect study or a comparison to the legacy controller.
- Native tool calls; temperature 0; planned explicit provider non-thinking
  mode; per-call output maximum 4096 tokens. The Reasoning backend is a policy,
  not a requirement to enable the provider's hidden-thinking mode.
- One active cell globally; one native attempt; maximum eight logical model
  calls per cell, with every underlying transport attempt separately charged.
  A request-count stop is a named development-pilot limit, not normal r53 policy.
- Interleave backend order by task form; use a fresh sandbox/client per cell.
  No cross-cell candidate, conversation or feedback reuse.
- Retain the r53 1800-second wall-time policy. Operational budget/request stops
  are explicitly censored pilot outcomes, never ordinary benchmark zeroes.
- Freeze all six scheduled cells before generation. Unstarted/stopped cells
  remain in the pilot index. Do not change settings or repeat a candidate in
  response to final scores. Final evidence cannot enter another model prompt.
- Treat these families as development/calibration exposure for later claims;
  record exclusion/secondary-analysis policy before any subsequent main result.

## Mandatory live-execution gates

The current CLI has no fiat-cost cap and no explicit DeepSeek thinking option.
Its transport may make up to three HTTP attempts per logical call. Existing
dry-run manifests therefore verify selection/runtime preparation only: **do not
turn them into live runs merely by removing `--dry-run`.**

Before paid execution:

1. Load a scoped `DEEPSEEK_API_KEY` or user-named external key file; never search
   private projects for credentials or publish key values/paths.
2. Verify official model availability, account currency and service usability
   with metadata endpoints; do not recharge or print account balances publicly.
3. Add/test a pilot-only pre-HTTP spend guard and explicit provider parameters
   through existing transport/client seams. Avoid another controller or proxy.
   Assert the actual outbound request contains `thinking: {type: "disabled"}`;
   a manifest label alone is insufficient. DeepSeek defaults to thinking mode,
   where sampling controls such as temperature do not have the same effect.
4. Reserve each request's worst-case charge before network execution, using a
   conservative provider context bound and capped output at peak/miss prices.
   Reconcile only validated provider usage; missing/failed/ambiguous requests
   retain their full reservation. Retries must pass the same gate individually.
   Do not rely on rough text/token estimates as a billing guarantee.
5. Bind provider mode, rates, currency, cap, request limits, code/image hashes,
   selection and execution order in a fresh immutable pilot manifest. No
   in-place resume after failure or process loss.
6. Prove zero network calls after a refused reservation, retry charging,
   missing-usage handling and unchanged default runner behavior using tests.
   Then execute the six-cell schedule within the shared cap, retaining stops.

The guard is a separate operational safety layer, not a silent change to the
sealed benchmark's stopping rule. Final score must not drive retry or expansion.

## Preparation, records and stop conditions

Use the existing wrapper for separate free dry-runs under the ignored
`benchmark-vabench-release-v4/reports/deepseek-flash-pilot-20260830/` subtree.
These outputs are never reused as live mutable runs. Store raw provider payloads,
private trajectories and final diagnostics locally only; publish sanitized
counts, source hashes and failure categories after review.

Stop before model execution if credentials are absent, rates/model availability
drift, spend protection is not verified, accounting is ambiguous, or the two
campaigns differ on a non-backend controlled factor. A budget-triggered stop
preserves all evidence and the full denominator; it does not authorize another
budget or episode. Real results and costs remain pending until live execution.

The run-experiment skill's GPU deployment ledger does not apply to this
API-hosted model. Its referenced compute-env file is absent locally; reuse the
repository's pinned Docker/EVAS environment contract and existing smoke evidence
instead of building or renting a GPU environment.

## Free preparation evidence

Both dry-runs prepared exactly three cells from seeded family `029`:
`v4-029` (DUT), `v4-1029` (bugfix), `v4-529` (Testbench). Their canonical
`.cells` arrays are identical. Campaign SHA-256 values:

- `native-mini-swe-dryrun/campaign.json`:
  `f0d0bba977d2e739747bea2bf2ba390b6d4c64152531bd36de26b4a75dfc8514`
- `native-reasoning-dryrun/campaign.json`:
  `e112ebb3f54e3c69f6d0257df47d0efaf32694a97d8b29e7d015a1734c34f5f2`

Each invocation used the existing wrapper with common arguments below; use
different fresh output directories and each named backend:

```sh
uv run --locked --extra agentic python \
  benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --output-root FRESH_DRYRUN_DIRECTORY \
  --model deepseek-v4-flash --sample-families 1 --seed 20260830 \
  --form dut --form bugfix --form testbench \
  --comparison-profile executable-feedback-control --experimental-arm Agentic \
  --episode-backend BACKEND --per-turn-max-tokens 4096 \
  --workers 1 --native-max-attempts 1 --dry-run
```

The Reasoning invocation additionally fixed
`--reasoning-proposal-format native_tool_calls`. Both report `prepared: 3`,
null EVAS identity and no observed container IDs; these are not live execution
or billing-protection evidence. Provider thinking mode and spend guard remain
unimplemented in this preparation. No credentials were read and no paid calls
were made. The active-entrypoint/layout regression gate passed 48 tests.
