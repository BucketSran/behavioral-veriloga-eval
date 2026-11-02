# Provider Evaluation Protocol

This protocol separates model capability, provider reliability, transport
normalization, and local vaBench execution. It applies to every
OpenAI-compatible vendor used in comparative experiments.

## 1. Submission transport is not a scored task

OneShot cells receive one transport-only `submit_artifacts` function:

- the JSON schema names the complete declared artifact set;
- the model supplies one string value per exact artifact path;
- the runner rejects missing, extra, duplicate, unsafe, empty, or non-text
  artifacts before writing any candidate;
- a successful call finalizes the cell immediately;
- the tool cannot read files, execute EVAS, reveal diagnostics, or access the
  checker.

Providers that reject named or required tool choice use `tool_choice=auto`.
The exported upstream public task prompt remains byte-for-byte unchanged.
A separate runner-owned system transport instruction requires exactly one
`submit_artifacts` call; this instruction is part of the API adapter rather
than the benchmark task. If a provider returns text instead, the runner may
apply only deterministic transport normalization:

- exact expected path set;
- safe paths;
- no duplicate or ambiguous mapping;
- a single fenced block only when exactly one artifact is declared;
- no inspection of Verilog-A or Spectre semantics.

Record the original transport and normalization, but do not score marker,
Markdown, or JSON-envelope spelling as circuit capability.

## 2. Outcome taxonomy

Every cell has one terminal category:

| Layer | Category | Counts as model capability failure |
| --- | --- | --- |
| Transport | `submitted` / `transport_normalized` | No |
| Candidate validity | `invalid_run` / `reference_invalid` caused by candidate code or deck | Yes |
| Candidate behavior | `behavior_failure` / `reference_behavior_failure` | Yes |
| Provider | HTTP error, rate limit, context rejection, request timeout, interrupted stream | No; report separately |
| Runner/runtime | export, container, filesystem, EVAS installation, or judge infrastructure failure | No |

Candidate syntax, unsupported strict-mode constructs, illegal include paths,
and malformed Spectre sources are real model failures. A simulator-coverage
gap is infrastructure only when the submitted construct is permitted by the
public contract and accepted by the final reference simulator.

Report both:

1. intent-to-test results over all scheduled cells, with infrastructure
   outcomes shown explicitly; and
2. model-capability pass rate conditional on an evaluable submission.

Do not silently convert provider failures into model failures or remove them
from the reliability report.

## 3. Timing decomposition

`agent_elapsed_s` is an operational wall-time metric. It includes provider
queueing, network transfer, generation, local tools, EVAS, and agent control.
It is meaningful only with a declared concurrency and provider configuration.

Record these components for every provider request:

- request scheduling time;
- response-header time;
- first SSE data time;
- time after first SSE data;
- completion and reasoning tokens;
- streaming chunk count;
- finish reason and provider request ID;
- HTTP status and structured provider error;
- timeout phase: connect, first data, idle stream, or total request.

Also record local EVAS/tool time separately. Do not subtract network time to
create a synthetic "true wall time"; instead report:

- observed cell wall time;
- provider request count and summed provider time;
- local tool/EVAS time;
- output and reasoning tokens;
- normalized streaming tokens per second.

Pass rate is the primary capability metric. Wall time is a system-level
efficiency metric and must not be compared across undeclared concurrency or
different timeout policies.

## 4. Timeout policy

A single `curl --max-time` limit cannot distinguish a dead connection from a
healthy long generation. Use separate limits:

- connect/response-header timeout: 120 seconds;
- idle-stream timeout: 180 seconds without a new SSE record;
- total request safety cap: 1800 seconds;
- agent episode cap: declared separately, currently 5400 seconds.

Retry a transport failure only if no model token/tool argument was received.
After partial generation, record `provider_stream_interrupted`; rerun the whole
cell only under a preregistered infrastructure-retry policy. Retries must have
their own per-attempt limit plus a separate total infrastructure budget.

The model's `max_tokens` remains 65536 for the experiment. It is a ceiling, not
a prediction that every request should finish quickly.

## 5. Concurrency calibration

Calibrate each `(vendor, endpoint, model, region)` independently before a
campaign. Do not reuse DeepSeek concurrency for another provider.

Run two fixed public workloads:

1. a short control request to measure gateway/network behavior;
2. a representative vaBench prompt with the campaign token ceiling.

For a pilot, run at least 10 requests per concurrency level. For a formal
calibration, run at least 30 requests per level in three time blocks and rotate
the level order between blocks. Include concurrency 1 and the intended maximum.

Use:

```bash
python operations/calibration_pilot/calibrate_provider_concurrency.py \
  --base-url https://provider.example/v1 \
  --model MODEL \
  --api-key-file /secure/path/key \
  --concurrency 1 5 10 \
  --requests-per-level 30 \
  --max-tokens 65536 \
  --output calibration.json
```

Select the largest tested concurrency satisfying all of:

- zero provider failures in the calibration sample;
- first-SSE-data P90 no greater than `max(1 second, 2 × concurrency-1 P90)`;
- median completion-token streaming rate at least 90% of the concurrency-1
  baseline.

The calibration script records raw requests, summaries, and this recommendation.
Keep local EVAS workers separate from an API in-flight semaphore. Local
simulation may use more workers than the provider-approved API concurrency.

Recalibrate after a model revision, endpoint/region change, material provider
incident, or a sustained latency shift greater than 20%.
