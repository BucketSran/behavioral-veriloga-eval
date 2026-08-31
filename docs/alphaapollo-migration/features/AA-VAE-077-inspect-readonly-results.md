# AA-VAE-077 — Inspect read-only results integration

Date: 2026-09-01. Scope: optional native-result import, not a new evaluator.

## Purpose and reused design

The user's framework goal is better evaluation ergonomics, parallel throughput,
and result analysis. It is separate from AA-VAE-076 adversarial acceptance.
Use Inspect's official typed log API instead of inventing a dashboard/archive
format or running a second solver/scorer. Pin `inspect-ai==0.3.261` in the
optional `environment/requirements-inspect-reporting.txt`; default project
dependencies, agent images and the EVAS lock remain unchanged.

Official sources (reviewed 2026-09-01):

- [Log API](https://inspect.aisi.org.uk/reference/inspect_ai.log.html):
  `EvalLog`, `EvalSpec`, `EvalSample`, `EvalResults`, `write_eval_log`, `read_eval_log`.
- [Score API](https://inspect.aisi.org.uk/reference/inspect_ai.scorer.html):
  `Score.unscored` represents exclusion using Inspect's NaN sentinel, not zero.
- [Pinned source](https://github.com/UKGovernmentBEIS/inspect_ai/tree/0.3.261/src/inspect_ai/log)
  and [release](https://pypi.org/project/inspect-ai/0.3.261/).
- [Parallelism](https://inspect.aisi.org.uk/parallelism.html) and
  [model concurrency](https://inspect.aisi.org.uk/models-concurrency.html)
  motivate the separate execution-efficiency follow-up below.

## Code mapping

| File / function | Responsibility |
| --- | --- |
| calibration-pilot `score_campaign.py::read_native_campaign_rows` | Extract the existing bounded parallel score reader, including retry-policy and backend/model/proposal/budget identity checks; reused by original CLI. |
| calibration-pilot `result_adapter.py::read_campaign_ledger` | Verify existing terminal evidence through that reader, then reuse `result_ledger.build_native_campaign_ledger`. No model/tool/freeze/judge execution. |
| `result_adapter.py::build_inspect_log` | Convert safe ledger records to official log objects; retain per-condition metrics and original metadata, with no pooled headline. |
| `result_adapter.py::export_inspect` | Reserve a new output directory, write ledger and official `.eval`, then publish an export receipt with hashes and read timing. Never write under source run root. |
| `tests/test_agent_harness_result_adapter.py` | Serial/parallel equality; malformed/incomplete inputs; null/zero/denominator preservation; official log round-trip; separate-process scored-evidence import without judge reentry. |

Simplified data flow:

```python
rows = existing_verified_readers(frozen_campaign, run_root, workers=N)
ledger = existing_safe_ledger(frozen_campaign, rows)
samples = [Score(value=r.score) if r.eligible else Score.unscored(r.reason)
           for r in ledger.records]
write_eval_log(typed_log(samples, metadata=ledger), fresh_export)
```

## Usage

From repository root, using a completed, explicitly frozen native campaign:

```sh
uv run --locked --extra agentic \
  --with-requirements environment/requirements-inspect-reporting.txt \
  python benchmark-vabench-release-v4/operations/calibration_pilot/result_adapter.py \
  --campaign /absolute/campaign.json --run-root /absolute/run \
  --output-dir /absolute/new-export --workers 4
```

The new directory contains `results.eval`, `ledger.json`, and `receipt.json`.
Open it with the official Inspect viewer, for example:

```sh
uv run --locked --extra agentic \
  --with-requirements environment/requirements-inspect-reporting.txt \
  inspect view --log-dir /absolute/new-export
```

`status=success` and `completed_samples` mean the import completed, not that
the tasks passed. Original status, eligibility, zero/null score, selected/all
attempt costs, source hashes and paired coverage remain in ledger metadata.
Per-condition `pass_rate` stays `passed / score_eligible`; if no eligible sample
exists, the rate remains null in the ledger and its numeric metric is omitted.
No synthetic transcript, model usage, evaluator identity or evaluation duration
is invented. Inspect stats timestamps describe import only. Sample scores use
Inspect's official unscored representation while metadata retains JSON null.

## Compatibility and limits

- Native mini-swe/Reasoning ordinary three-condition campaigns only. Existing
  readers still reject incomplete/tampered evidence; no silent recovery.
- Legacy comparisons and Evolution/combined interventions keep their separate
  readers and estimands; this adapter does not silently merge those records.
- The input is a trusted local evidence store. Hash checks detect inconsistencies,
  not host-wide forgery or remote attestation. Imports are not signed evidence.
- Missing receipt/cell is an explicit import error, not an unscored fabricated
  row. A recorded terminal infrastructure failure remains a visible unscored row.
- Output paths are new local directories outside the run tree. An interrupted
  export is incomplete, not reusable; the source is untouched.
- Full dependency closure for the optional viewer is resolved by uv overlay;
  only Inspect's API version is pinned here. It is not the evaluator environment.

## Execution-performance follow-up, not delivered by log import

Existing `run_campaign.py` and `run_native_batch.py` already use bounded worker
pools; native score reading also already supported workers. This slice extracts
and reuses it rather than introducing another scheduler. `read_elapsed_s` and
`read_workers` in the export receipt concern result ingestion only.

Before replacing execution scheduling, measure the same frozen scripted workload
at worker counts 1/2/4: total wall time, cells/minute, queue/setup/provider/tool/
judge time where actually observable, peak containers, timeout/rate-limit counts,
and complete identical result/attempt accounting. Do not fill missing phase
timings with inferred zeros. Then test Inspect Task/Solver delegation with one
owner for each retry/budget/final boundary and compare throughput under matched
resource caps. `max_tasks`, `max_samples`, model connections and sandbox capacity
are different bottlenecks; adding concurrency cannot guarantee higher throughput.
No performance gain or native Inspect Task registration is claimed by this slice.

## Verification

Official Inspect 0.3.261 round-trip and separate-process import are executed in
a reporting-only environment. Exact commands/counts and the broader regression
are recorded in `logs/verification-log.md`. No keys, paid calls or real-model
quality evidence; r53 and EVAS 0.8.7 remain unchanged.
