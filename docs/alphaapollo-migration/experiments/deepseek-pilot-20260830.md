# DeepSeek engineering pilot: safely stopped, no scored result

Date: 2026-08-30. This is a sanitized evidence summary, not a benchmark result.

## Frozen scope

- Source: `f3e12ac82672d7b27dd3accf01176aaa5f67e4fd` (fork/main).
- r53 + EVAS 0.8.7 unchanged; Docker image:
  `sha256:fe44bb54370160ee99bef939ae67a0ab1f51fb3b9a41d3d0c4cf29e7ea38115b`.
- Requested and observed model alias: `deepseek-v4-flash`. The service response
  exposed the alias, not an immutable provider snapshot/version guarantee.
- Seed 20260830 selected family029 before outcomes. Three forms, two Agentic
  backends, serial, one attempt, eight admitted calls/cell, max output 4096,
  non-thinking, temperature 0. CNY 5.00 shared operational ceiling.
- Private outputs: ignored `benchmark-vabench-release-v4/reports/deepseek-live-20260830-01/`.
  No raw provider response, credential, final diagnostic or candidate is committed.

## Complete denominator

| Form / task | Backend | HTTP attempts | Disposition | Final score |
| --- | --- | ---: | --- | --- |
| DUT / v4-029 | native-mini-swe | 8 | Censored: model-call limit | null |
| DUT / v4-029 | native-reasoning | 8 | Censored: unknown request cost | null |
| bugfix / v4-1029 | native-reasoning | 0 | Not started after shared stop | null |
| bugfix / v4-1029 | native-mini-swe | 0 | Not started after shared stop | null |
| Testbench / v4-529 | native-mini-swe | 0 | Not started after shared stop | null |
| Testbench / v4-529 | native-reasoning | 0 | Not started after shared stop | null |

The six scheduled rows remain present. Two runtimes started; none reached a
scored final submission. Native infrastructure terminal records are retained,
while the pilot layer distinguishes the operational call cap and cost stop.
No missing row is discarded, and no null score is converted to zero.

## Stop and accounting

16 HTTP attempts were captured. The first 15 returned valid terminal usage;
their conservative peak/cache-miss upper bound totals **CNY 0.237723**.
The final request returned curl code 35 (SSL handshake failure), after about
20.43s, with zero response-body bytes and no terminal usage. The shared guard
stopped before any further HTTP/retry and retained **CNY 3.182592** for that
uncertain attempt. Total committed/reserved upper bound: **CNY 3.420315 < 5.00**.

These numbers are not actual billed cost. Even though the transport evidence
suggests an early connection failure, no reservation is refunded on that
assumption. No new budget, rerun, model change or wider experiment was started.

## Immutable evidence and offline verification

- Pilot manifest SHA-256:
  `a5089ada82e77c81366ec052bbb1e83b437d975bc47d8e9294fb639eaf769082`
- Pilot index SHA-256:
  `25081177f004ec730d3d34af33ab3ab110fe8df9c780100aa43007af452ff394`
- Budget journal SHA-256:
  `f1ad92ac208d2288caa140e7c1bb1ddd3bd29253844d1730e663653fa7a15963`
- Execution journal SHA-256:
  `405eb4ae12a3936d586ae3a61e6a98b55b859c5f8aff7e74384f45c3c7c3c515`

Offline verification re-read both native results with the existing strict
`read_native_cell` validator, matched all index/journal hashes and 16 captured
transport attempts, and verified absent runtimes for all four unstarted cells.
No final judge or provider was called during verification.

## Claim boundary and next decision

Real API/native-tool connectivity, trace preservation and fail-closed budget
stopping are observed. No final-score, model-quality, backend superiority,
baseline reproduction or six-cell completion claim is supported. Free fixture
tests separately cover six-cell freeze/EVAS and stop behavior (AA-VAE-052).

The [offline trajectory diagnosis](deepseek-pilot-20260830-diagnosis.md) is now
complete: it identifies a missing Reasoning Bash/submit contract, an invisible
pilot call horizon, path friction and layered exit-status semantics. No runtime
repair or new generation is included in that diagnosis. A larger call
allowance or paid rerun requires a newly explicit design/budget decision; do
not silently loosen this run or merge a replacement into its denominator.
Family029 remains development exposure for subsequent study design.
