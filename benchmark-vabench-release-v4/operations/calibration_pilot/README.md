# V4 Calibration Pilot

## Start here

This is a command/protocol reference, not a feature checklist. Use the
[runner guide](../../runners/README.md) to choose an existing default, opt-in
experiment or diagnostic entrypoint; use the
[current plan](../../../plans/current-plan.md) for active work.

- Normal generation and final evaluation: [general campaign tools](#general-campaign-tools)
  and [native backend / Evolution](#native-backend-and-evolution-entrypoints).
- Named experiments: [legacy/native comparison](#explicit-live-legacynative-comparison)
  or [combined tools](#opt-in-combined-public-tool-acceptance-aa-vae-075).
- Analysis only: [Inspect export](#read-only-inspect-results-export) and the
  separate fixed-workload profiler described there.

Examples below do not grant paid-run authority. Historical pilot contracts and
their dated provider profiles are not current default launch instructions.

## Read-only Inspect results export

`result_adapter.py` imports an existing explicitly frozen native-mini-swe or
native-reasoning campaign through the same verified readers used by
`score_campaign.py`. Its optional Inspect 0.3.261 log writer never runs a model,
tool, freeze, repair or final judge. Use a fresh output directory outside the
source run tree; incomplete/mismatched evidence is an error, not a model zero.

```sh
uv run --locked --extra agentic \
  --with-requirements environment/requirements-inspect-reporting.txt \
  python benchmark-vabench-release-v4/operations/calibration_pilot/result_adapter.py \
  --campaign /absolute/campaign.json --run-root /absolute/run \
  --output-dir /absolute/new-export --workers 4
```

Output: `results.eval` for the Inspect viewer, the original safe `ledger.json`,
and a hash-bound export receipt. All scheduled records, eligibility/exclusions,
unknown costs and per-condition denominators remain visible. Import timing is
not evaluation latency; `--workers` parallelizes only evidence reads. Default
runner/environment dependencies are unchanged. Legacy/Evolution/combined results
are not silently converted into this ordinary native ledger. Code map and
execution-performance follow-up: [AA-VAE-077](../../../docs/alphaapollo-migration/features/AA-VAE-077-inspect-readonly-results.md).

Additional explicit `--source-kind` values are `legacy-native-comparison`,
`evolution-single`, and `combined-tools`. Omit `--campaign` and keep `--workers 1`
for these sources; `--run-root` is their sealed comparison/attempt/combined root.
Evolution single-attempt export is not a batch/retry aggregation. Scores, costs,
and denominators stay in separate protocol groups; unknown costs remain null.
See [AA-VAE-080](../../../docs/alphaapollo-migration/features/AA-VAE-080-multipath-readonly-reporting.md).

Fixed execution profiling is separate from the viewer/import path:

```sh
.venv/bin/python scripts/profile_native_execution.py \
  --output-root benchmark-vabench-release-v4/reports/my-fresh-profile \
  --native-docker --workers 1,2,4
```

This reuses scripted public stubs, real Docker/EVAS, and fresh native attempts;
no paid model calls. It checks frozen content/verdict consistency and reports
actual elapsed/queue/phase time. It does not infer CPU/RAM usage, recommend a
production worker count, or claim model-quality speedup. Details and limitations:
[AA-VAE-079](../../../docs/alphaapollo-migration/features/AA-VAE-079-fixed-execution-profile.md).

## Explicit live legacy/native comparison

`comparison_live.py` adds separate `prepare`, `inspect`, `run`, and read-only
`report` commands. It reuses the free coordinator below with the same six cells,
existing budgeted DeepSeek transport and final readers. It is not the default
campaign runner, and preparing a profile does not grant spending authority.

Free local preparation (replace placeholders with local identities; no key or HTTP):

```bash
.venv/bin/python benchmark-vabench-release-v4/operations/calibration_pilot/comparison_live.py \
  prepare --output-root /absolute/fresh-private-comparison \
  --currency CNY --cap PROPOSED_CAP --image vabench-agent-runtime:0.8.7 \
  --evas-command /absolute/path/to/evas
.venv/bin/python benchmark-vabench-release-v4/operations/calibration_pilot/comparison_live.py \
  inspect --output-root /absolute/fresh-private-comparison
```

Only after separate fee approval, `run` requires `--output-root`,
`--expected-manifest-sha256`, `--approve-cap`, `--currency`, `--credential-file`
and `--evas-command`. There are no default fee, credential, hash or resume flags.
The cap string/currency must exactly match the inspected manifest; the key file
must be repository-external and owner-only. The loader reads literal fields,
never sources shell. Known provider environment keys are removed before runtime
work. `prepare` also clears those names before local executable inspection.

The dated v1 provider profile permits launch only on its reviewed UTC day,
2026-09-01; old profiles stay readable but must not be automatically refreshed.
It records the complete official CNY/USD peak and off-peak schedule while the
spending guard reserves conservatively at the peak cache-miss/output rates.
The operator receipt prevents accidental unapproved/repeated starts, not a
host-authenticated identity check. Metadata checks retain only currency,
availability and hashes; the reused conservative preflight requires balance
at least the guard's supported maximum even when the proposed cap is smaller.
Any reserved launch or fee stop requires inspection, never rerun with reset funds.

`report --output-root ...` validates existing launch, budget and score evidence
without reading a key, contacting a provider, refreezing or scoring again.
Potentially billable attempts and guard upper bounds are not invoice charges;
live `paid_requests` is null rather than an invented zero. Real model quality
evidence and fresh fee authorization remain unexecuted in this implementation.
See [AA-VAE-072](../../../docs/alphaapollo-migration/features/AA-VAE-072-explicit-live-comparison.md)
for official source references, code map, tests and model-alias limitations.

## Free legacy/native workflow comparison

`run_legacy_native_comparison.py` is an opt-in **scripted-response Python API**,
not a paid CLI or a replacement for the default legacy runner. It derives the
AA-VAE-069 family001 six-cell schedule (DUT/bugfix/Testbench, legacy/native-mini-swe),
observes actual public exports/Docker isolation/requests, and reuses one shared
spending guard and existing freeze/final readers. `read_comparison(root)` checks
existing evidence only: no model, re-freeze, repair or second final judge.

Run the free Docker/EVAS fixture from the repository root after building the
pinned public images and installing the locked agentic dependencies:

```bash
comparison_test_root=$(mktemp -d benchmark-vabench-release-v4/reports/comparison-check-XXXXXX)
VABENCH_TEST_DOCKER_RUNTIME=1 .venv/bin/python -m pytest -q \
  tests/test_agent_harness_workflow_comparison.py \
  tests/test_agent_harness_comparison_surface.py \
  --basetemp "$comparison_test_root/pytest"
```

The synthetic response path does not load keys or send HTTP. Shared cost values
test conservative reservation arithmetic, not real invoices. It preserves every
scheduled row on insufficient funds/unknown costs and blocks reentry. Matched
score/cost/time deltas require valid paired surface evidence. Unknown scores are
null, not zero. EVAS results remain development-only; these scripted fixtures
do not reproduce a model baseline. The separate live entrypoint above supplies
the transport gate; a real comparison still needs a freshly reviewed frozen
profile and fee approval. This free API never grants that authority.
See `docs/alphaapollo-migration/features/AA-VAE-071-comparison-engineering-gates.md`
for code mapping, tests and claim boundaries.

## Opt-in budgeted DeepSeek engineering pilot

`run_deepseek_pilot.py` composes the existing native harness for the predeclared
family029 three-form/two-backend pilot. It is not the normal campaign CLI:
one shared CNY 5.00 (USD 0.70 for USD accounts) cap, eight calls/cell by pilot default, one attempt,
serial execution, no resume. It loads only `DEEPSEEK_API_KEY` from an external
owner-only literal credential file; never use `source` or pass the two-key file
to the older raw-key argument. GLM is not called.

Use `--output-root FRESH_PRIVATE_DIRECTORY --credential-file EXTERNAL_ENV_FILE
--evas-command ABSOLUTE_EVAS_COMMAND` with a clean committed source tree and
the pinned local Docker image. This is a live paid entrypoint, not a dry-run:
only use it for the explicitly authorized pilot. Freeze/execute once; do not
rerun it with a new budget after a stop. See `plans/deepseek-budget-pilot.md`
at the repository root for the design and prior execution status.

The private pilot index preserves all six scheduled rows, including operational
stops and unstarted cells. Read-only native evidence validation never invokes
another final judge. Raw outputs remain outside Git; costs are protective
upper bounds rather than invoices, and scores are development-only.

## General campaign tools

The default release target is
`benchmark-vabench-release-v4/release/benchmarkv4-r53`, paired with the pinned
EVAS 0.8.7 public runtime. Tools that support
historical inspection require the frozen r44 path explicitly; the active
direct-EVAS runner never falls back to it.
Use `--sample-families N --seed S` for reproducible random complete-family
campaigns, or pass an explicit `--selection` manifest when reproducing a
historical pilot. `CALIBRATION_FAMILIES.json` is retained only as historical
selection evidence.

The pilot is used only to freeze real skill snapshots, the agent wall-time cap,
provider per-turn output cap, safety limits, runner behavior, repetition count,
and telemetry. Skill text must remain task-agnostic and is not inlined into the
task prompt. G1/G3 expose the `veriloga` language skill, G4 exposes the
`vabench-feedback` public-EVAS diagnosis skill, and G5 exposes both. Neither
skill may contain a selected family ID, title, equation, threshold, stimulus
constant, checker rule, or mutation hint.

Because model outcomes from these families influence experimental settings,
their 30 forms are excluded from the primary post-calibration result. The
primary denominator is therefore 390 families and 1,170 scored forms. The
complete 400-family result may be reported only as a clearly labeled secondary
or sensitivity analysis.

The selection does not modify task assets, existing EVAS/Spectre evidence, or
the sealed 1,200-task release. A later campaign manifest must reference this
file by SHA-256 and record the frozen parameters produced by the pilot.

## Native backend and Evolution entrypoints

Legacy mini-swe remains the default. The opt-in `--episode-backend`
selection is distinct from the older `--agent-scaffold native` sensitivity
option. `native-mini-swe` and `native-reasoning` share the controller, sandbox,
submission freeze and final replay; they select different model policies.
Reasoning defaults to native tool calls; freeze `--reasoning-proposal-format
strict_json` explicitly to study that protocol. Run separate matched campaigns,
not a mixture of backend identities in one result table. Native fresh-attempt
recovery is opt-in with `--native-max-attempts` (default one): it recovers only
eligible infrastructure failures before terminal activity, not wrong answers.

### Batch-level recovery (AA-VAE-070)

For native campaigns, create a fresh run through the normal wrapper; reopening
it uses the same command and output root plus `--resume`. The frozen campaign
and `.batch/manifest.json` must match source bytes, ordered cells, model/backend,
runtime options, budgets and observed Docker IDs. Completed terminal cells
(including zero scores and unscored failures) reuse verified evidence without
model or judge calls. Only missing cells or fully sealed eligible native
attempt prefixes may execute; the original attempt/call caps still apply.

The Evolution entrypoint below adds an explicit `--batch` option with repeated
`--cell ORIGINAL_AGENTIC_CELL_ID`, `--batch-max-attempts N` (default one) and
`--resume`. Each cell owns fresh `attempt-NNNN` directories. Retry is restricted
to a verified setup failure containing only a bound `setup-request.json` and
terminal result with zero-start/cost evidence. Even residual public-validation
or final runtime directories block automatic retry; partially run Evolution
rounds are not restored. Final results never feed the next attempt.
Evolution results remain separate from the single-trajectory score ledger.

Both paths use an exclusive local-process lock, immutable terminal receipts
and append-only `.batch/index-NNNNNN.json` snapshots retaining the full roster.
They reject source/config/roster/image drift, changed terminal evidence and
unknown in-flight state before provider creation. Native roots live under the
wrapper's `run/`; Evolution batch roots are `--output-root` directly. Batch
records are private operational evidence, not reviewer-safe exports. A dry-run
is a separate frozen batch and cannot be converted into real execution.

This is not arbitrary checkpoint recovery, distributed scheduling, or an
invoice-budget guarantee. Use local POSIX filesystems with `flock`, hard links
and `fsync`; do not delete locks/receipts or force-adopt old outputs. The guarded
DeepSeek pilot still has no resume path and its fee guard is unchanged.
The legacy conversation `--resume` and single-cell native no-reentry contract
are unchanged. See [AA-VAE-070](../../../docs/alphaapollo-migration/features/AA-VAE-070-batch-resume.md)
for upstream rationale, code map and tests.

The campaign wrapper also accepts `--native-model-call-limit N` for either
native backend, with N a positive integer. Omission adds no model-call limit;
eight is only the named DeepSeek pilot's default, not a harness or r53 rule.
The frozen execution config and every model request carry the configured limit
and current remaining calls. Each admitted logical policy request counts,
including failed requests, and fresh infrastructure attempts cannot refund it.
Underlying HTTP retries and provider output-token caps are separate controls.
The Nth response's legal action can execute and submit; exhaustion without a
submission is `budget_exhausted / model_call_limit`, with a null score and no
automatic freeze/judge. Other time, tool and cost limits still apply. An actual
terminal failure keeps its own cause even if it consumed the last allowance.
OneShot still makes only one output-only generation. Legacy rejects this opt-in.
The historical single-cell CLI has no new flag; its native Python API accepts
`model_call_limit`. Evolution retains its separately frozen branch budgets.
See [AA-VAE-054](../../../docs/alphaapollo-migration/features/AA-VAE-054-optional-model-call-budget.md)
for exact counting, evidence fields and tests. This does not authorize a paid run.

For native campaigns, `score_campaign.py --ledger-output /absolute/new-ledger.json`
adds a write-once reviewer-safe ledger outside the generation directory. It
preserves all scheduled cells, null infrastructure scores, all-attempt costs,
source hashes and unmatched pairs. The ordinary private score report remains
available. Missing provider token counts remain unknown, not zero.

`run_evolution_campaign.py` is a separate one-cell entrypoint for the explicitly
budgeted `AlphaApollo-Evolution+EVAS` condition. Select an original Agentic cell
from a valid r53 campaign and supply a JSON branch roster, for example:

```json
[
  {"branch_id": "local", "model": "YOUR_LOCAL_MODEL", "base_url": "http://127.0.0.1:8000/v1"},
  {"branch_id": "api", "model": "YOUR_API_MODEL", "base_url": "https://YOUR_PROVIDER/v1", "api_key_env": "EVOLUTION_API_KEY"}
]
```

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/run_evolution_campaign.py \
  --campaign /absolute/source-campaign.json --cell ORIGINAL_AGENTIC_CELL_ID \
  --branches-json /absolute/branches.json --output-root /absolute/new-evolution-run \
  --rounds 2 --model-calls 8 --tool-calls 8 --public-validation-calls 1 --dry-run
```

Dry-run freezes provenance and budgets without reading credentials, starting
EVAS or contacting a provider. For an authorized real run, choose a fresh output
root, remove `--dry-run` and provide `--evas-command /absolute/path/to/evas`.
The CLI reads named API keys into the host-side clients and removes those names
from process environment before sandbox creation; callers importing `main()`
should account for this process-global security behavior. Never put credential
values or credential-bearing URLs in the roster. Endpoint URLs are represented
by hashes in the frozen campaign.

Each branch generates in a fresh no-EVAS sandbox. The coordinator alone runs
the fixed public validator on its candidate, so public validation is metered and
profile-bound. Next-round branches receive the same sealed public feedback and
candidate code; no in-flight peer state or final verdict is shared. A deterministic
public-only reducer selects one candidate for final freeze/replay. This is a
different information schedule and compute budget from single-trajectory
Agentic, not an equal-budget replacement. The output has its own final result
index; the single-trajectory ledger intentionally rejects Evolution records.

Deterministic providers test connectivity, not model quality. Actual model
experiments require a named model/service, explicit budget and frozen controls.
The plain Evolution example does not enable docs/waveform. Their explicit
APIs and combined entrypoint are documented below. Synthetic training prototypes
are retired; real SFT/RL remains deferred. Spectre is conditional, not part of
this example.

## Offline docs development API

`run_prepared_native_mini_swe(..., docs_corpus=corpus)` explicitly adds the
`vaevas_docs_search` tool to native mini-swe or Reasoning in Agentic/Agent-No-EVAS.
Build `corpus` through `OfflineDocsCorpus.from_manifest`; synthetic v1 remains
compatible, and reviewed local v2 additionally records provenance, rights and
contamination review. OneShot rejects it before runtime reservation.
Omitting the argument preserves the existing Bash-only native path and legacy default.

The corpus profile freezes sources, policy, limits and index identity. It binds
tool capability, observations, launcher configuration and final evidence joins;
the controller still owns admission and `tool_call` charging. Single-cell reading
can verify this intervention, but ordinary aggregation and paired result ledgers
reject extension rows pending a separately frozen comparison protocol. There is
no automatic online retrieval. The separate combined entrypoint below accepts
an explicit local corpus; no third-party corpus text is bundled.
The separate `run_native_evolution(..., docs_corpus=corpus)` API now supports the
exact `AlphaApollo-Evolution+EVAS` condition ([AA-VAE-065](../../../docs/alphaapollo-migration/features/AA-VAE-065-synthetic-evolution-docs.md)).
Each NoEVAS generation branch has its own docs tool wrapper. Initial prompts
carry only profile identity; retrieved observations stay branch-local and use
the shared tool budget. Config/final result retain the frozen intervention;
ordinary single-trajectory aggregation still rejects Evolution, with or without docs.
See [AA-VAE-057](../../../docs/alphaapollo-migration/features/AA-VAE-057-synthetic-offline-docs.md).
This API does not activate the separate waveform tool or authorize paid runs.
Synthetic training projection was retired; it is not part of docs retrieval.

## Isolated waveform development API (not a campaign flag)

`run_prepared_native_mini_swe(..., public_waveform_max_calls=2)` explicitly adds
zero-argument `vaevas_public_simulate` for Docker Agentic only. `None` leaves it
disabled. It works with native mini-swe and Reasoning (tool calls or strict JSON).
The controller charges each admitted request; missing candidate files return
recoverable feedback without execution. The source container is paused during
snapshot/validation and resumed before model reentry. Fresh EVAS execution and
bounded waveform summaries are diagnostic, never a final correctness verdict.

The manifest freezes the extension and limit. Score reading reconstructs public
receipt/profile/candidate joins, request counts and confirmed execution counts;
unknown post-executor failures yield a null total and incomplete-count flag.
This is not a global cap on ordinary Bash EVAS processes. Final replay remains
post-freeze and never feeds the model. Ordinary aggregation rejects intervention
rows. Evolution's explicit `public_waveform=True` instead runs this executor
at the coordinator, once per candidate public-validation allowance; generation
branches remain NoEVAS. Only candidate/profile-bound bounded observations enter
the next sealed round. The old validator does not run a second time, and final
scores never enter shared memory. See AA-VAE-073 and the combined protocol below.
See [AA-VAE-061](../../../docs/alphaapollo-migration/features/AA-VAE-061-native-public-waveform-feedback.md).

## Opt-in combined public-tool acceptance (AA-VAE-075)

`run_combined_tools.py` composes the existing native Reasoning or Evolution
engine, docs search, isolated public waveform execution, submission freeze and
one selected final EVAS replay. It does not replace legacy mini-swe or alter the
six-cell comparison. Reasoning is the harness backend, not a claim that the
provider's internal thinking mode is enabled. The named live service retains
the existing reviewed DeepSeek profile and disabled thinking.

- `prepare` freezes a single family/form, corpus profile, runtime IDs, source,
  rounds/branches and model/tool/public budgets without reading credentials.
  `--intervention baseline` freezes Bash-only generation with zero docs/waveform
  use; `--intervention rag-waveform` (the compatibility default) enables both.
- `inspect` reads that preparation; `run` requires exact manifest hash, cap,
  currency and an external owner-only credential file. No automatic resume.
- `report` validates existing receipts without model/tool/freeze/judge reentry;
  reports actual successful retrieval, waveform use, and Evolution feedback
  exposure separately from declared capability and task score. Missing evidence
  is not a model zero. All branches' call and conservative cost counts remain.

Use four separate roots for the preregistered 2×2 diagnostic: native Reasoning
and Evolution, each with `baseline` and `rag-waveform`. The read-only ledger puts
the intervention in the record identity and report group. Baseline acceptance
requires zero attempts/exposure for both disabled tools; combined acceptance is
reserved for the enabled condition. This supports a matched combined-surface
contrast, not separate attribution to RAG versus waveform. See
[the active study](../../../plans/real-model-differential-and-incremental-study.md).

Run `.venv/bin/python benchmark-vabench-release-v4/operations/calibration_pilot/run_combined_tools.py --help`
from the repository root; each subcommand has its own `--help`. Preparation/run
accept `--docs-root`, `--docs-manifest`, `--evas-command`, and `--output-root`.
Default Evolution schedule is two branches of the same model for two rounds;
this is not heterogeneous multi-model evidence. Native uses one branch/round.
The controller enforces per-round model/tool budgets; the shared provider guard
also caps each branch across all rounds and retains unknown-cost reservations.
`--public-calls` is a ceiling: the current coordinator validates each candidate
once, not repeated retries until the allowance is used.

The provider profile is dated **2026-09-01 UTC** and expires after that UTC day.
Before a later live run, independently review provider model/rates/decoding,
update the dated service contract, and freeze a fresh root; do not just edit an
old manifest or bypass expiry. This implementation authorizes no paid run.

Reviewed v2 corpus permission for local model context does not imply permission
to send it to an API. Live preparation and launch both check this before keys.
Four authorized, pinned general veriloga-skills files are available through the
local ignored corpus path and committed manifest; Cadence material was not found
and remains omitted. Source pins, allowlist and rights/source-path requirements are recorded in
[AA-VAE-074](../../../docs/alphaapollo-migration/features/AA-VAE-074-reviewed-local-docs.md).
Automated combined acceptance uses synthetic provider replies with reviewed
local documents plus real Docker and EVAS 0.8.7. It proves wiring, not retrieval quality,
individual-feature benefit, independent hidden stimuli, or a model ranking.

## Opt-in public validation observations

Native single-trajectory Agentic Bash observations also carry `public_evas`
diagnostics (AA-VAE-055). Bash's pipeline returncode remains unchanged; the
bounded marker reports distinguish help/version from simulate and expose
reported EVAS failures to the next mini-swe/Reasoning request. All new records
are explicitly unauthenticated (`captured_sandbox_markers`, `diagnostic_only`):
arbitrary Bash can forge or bypass the public wrapper. Per-cell score rows keep
the new reported counters in `untrusted_operation_summary`, never as a budget,
validator or final verdict. Historical all-marker counters remain unchanged.
This diagnostic surface is distinct from the profile-bound validator below.
Legacy default and No-EVAS/OneShot capabilities are unchanged.

`public_validation.py` adapts the existing sandbox EVAS execution to the generic
candidate/profile-bound `Observation` contract. Trusted callers first build a
public profile with `build_public_validation_profile`, then construct
`PublicEvasValidator` with the same environment and `EpisodeContext`. Call
`validate(candidate_tree_sha256=...)` only through the owning controller's
capability and budget checks; the adapter does not maintain another budget ledger.

The contract supports fixed r53 DUT/bugfix public simulation and Testbench
reference-DUT-only commands in Docker, including the already-released portable
variants for families 102/112. Strict DUT/bugfix uses runtime-v2; portable uses
runtime-v3 plus `compatibility_mode=portable`. Testbench keeps reference-v1 and
uses the explicit portable mode only with its exact no-strict command. Unknown
or mixed schema/mode/command combinations are rejected; a strict simulation
failure never triggers a portable fallback. No release or EVAS bytes are changed.
It rejects unsupported contracts, undeclared
submission files, authority/candidate drift, incomplete invocation evidence,
resource overflow, and validation after submission/final reservation. A contract
failure invalidates the adapter; discard the attempt rather than reconstructing
it to retry. AA-VAE-070 recovers only outer batch/eligible sealed attempt
boundaries; it does not reconstruct this adapter mid-invocation.

Feedback is public process diagnostics, not a task pass/score. Profiles fingerprint
observed runtime inputs; the coordinator still owns sealed-release provenance,
pre-generation campaign freezing, and exclusive environment use. This does not
activate a new domain tool or change default mini-swe Bash/campaign execution.
See [AA-VAE-035](../../../docs/alphaapollo-migration/features/AA-VAE-035-production-public-validation-observation.md)
for exact code mappings, tests, and remaining boundaries.

Full-release contract coverage and portable native/waveform/Evolution regressions
are recorded in [AA-VAE-067](../../../docs/alphaapollo-migration/features/AA-VAE-067-r53-portable-public-contracts.md).
Contract recognition is not full-release simulation or model-quality evidence.
Evolution next-round inputs reload sealed candidate code and public log receipts;
the reducer still uses binary `sim_success`, not behavioral correctness. DUT/bugfix
public contracts declare shared visible replay stimuli with held-out checker
authority, not an independent hidden stimulus set. Testbench public reference
execution does not measure final held-out fault detection. Final verdicts remain
outside model feedback and candidate selection.

## Build The Campaign

The calibrated primary episode limit is wall-clock time. Its only authoritative
value and timeout-finalization behavior live in
`benchmark-vabench-release-v4/EXPERIMENT_POLICY.json`; campaign builders and
runners do not accept an override. The current policy gives every mode one
30-minute episode. Setup, model requests, tool calls, and judges use separate
infrastructure ceilings. The provider token value is
`per_turn_max_tokens`: a per-model-call safety cap passed as `max_tokens`, not a
cumulative G0-G5 stopping budget. Provider completion, hidden reasoning, visible
completion, and feedback-delivered text are recorded as telemetry and must be
reported separately from functional score.

If a model/provider rejects the next turn because the conversation exceeds its
native context window, the legacy campaign wrapper records
`context_window_exceeded` separately. Direct-mode responses at the provider
output cap record `termination_reason=model_output_limit`. Both mini-swe loops
currently retain `finish_reason=length` as telemetry and execute a complete
valid Bash call; they do not add an output-cap stopping rule. Accumulated tokens
are not the experimental ability budget. If wall time expires, the latest valid
workspace artifact is still eligible for judging, and otherwise the cell is
reported as `agent_timeout`.

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/build_campaign.py \
  --sample-families 10 \
  --seed 20260715 \
  --model qwen3.5-flash \
  --per-turn-max-tokens 65536 \
  --repetitions 1 \
  --output /tmp/v4-api-pilot-campaign.json
```

This produces 180 cells: ten families, three forms, and six modes. Use
`--repetitions` only after the single-episode smoke is sound.

Each model event records the requested per-turn maximum, provider-reported
completion, reasoning and visible tokens, and `finish_reason`. Hosted-model
aliases and provider timestamps must also be retained in external run metadata.

## Reuse A Completed Pilot

Completed episodes may be mechanically reused only when the model, prompt hash,
release hash, selection hash, endpoint hash, decoding settings, wall-time
policy, per-turn token cap, tools, and candidate files are unchanged. Prepare a
derived runtime containing only mechanically eligible episodes:

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/prepare_budget_reuse.py \
  --source-output /tmp/v4-calibration-4096 \
  --source-campaign /tmp/v4-calibration-4096.json \
  --target-campaign /tmp/v4-calibration-65536.json \
  --output /tmp/v4-calibration-65536
```

`REUSE_MANIFEST.json` records every accepted or rejected cell, source-result
hashes, candidate hashes, and rejection reasons. Reuse requires the same
provider, model, endpoint hash, temperature, streaming mode, prompt, EVAS
executable identity, wall-time policy, per-turn token cap, and release. A submitted
file is not by itself reusable: any episode whose model turn hit the provider
output limit must be rerun because an agent may have written an intermediate
file before truncation.
Run the full target campaign with `--resume`; reused cells are skipped and all
rejected cells start fresh.

## Dry Run

Install the pinned agent scaffold and build the upstream shared environment
before executing G2--G5:

```bash
uv sync --extra agentic --group dev
benchmark-vabench-release-v4/public-agent-runtime/build.sh
benchmark-vabench-release-v4/public-agent-runtime/verify.sh
```

`auto` selects Docker. Formal results require the matched images built from the
repository's top-level `environment/`: `vabench-agent-runtime:0.8.7` and
`vabench-agent-runtime:0.8.7-no-evas`. Other sandbox backends remain
legacy/test sensitivity paths and are not paper-valid. Record the Git commit,
image references, and observed image IDs by experimental arm with every
campaign.

G2--G5 use `mini-swe-agent==2.4.5` with its `DefaultAgent` controller and one
`bash` tool. The benchmark runner still owns campaign construction, runtime
export, credentials, wall-time enforcement, telemetry, trusted replay, and
final scoring; it does not implement a second model-control loop. Mini-SWE
step, cost, and consecutive-format-error limits are disabled. Accumulated
tokens are recorded but never terminate an episode.

Mini-SWE fixes the model--tool interaction scaffold; upstream vaBench's shared
Docker image fixes where those commands execute. This adapter does not fork or
modify mini-SWE-agent. It creates one container per task, forwards mini-SWE's
Bash calls through `docker exec`, and destroys the container at episode end.

Dry-run exports isolated runtime packages without contacting a model:

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/run_campaign.py \
  --campaign /tmp/v4-calibration-campaign.json \
  --output /tmp/v4-calibration-dryrun \
  --dry-run --limit 18
```

The mini-SWE shell starts at `/workspace` in the shared container and exposes
`public/task/` read-only, `public/submission/` writable, and `work/` writable.
Skill-enabled modes additionally expose `public/skills/<id>/` read-only with a
hash-bound `SKILL.md` package and `public/skills/SNAPSHOT_MANIFEST.json`; G2 has
no skill directory. All agentic modes receive the same minimal EVAS contract: a
pinned, real `evas` executable is discoverable in `PATH`, `evas --help` works,
and the task-local `evas_runtime.json` gives the public command.

The main-table executable-feedback profile adds `Agent-No-EVAS`, which keeps
the G2 mini-SWE controller, Bash workspace, wall-time policy, task prompt base,
and submission gate but uses the paired no-EVAS image. Its effective prompt
states that EVAS is unavailable, `evas_runtime.json` is removed, and neither
the `evas` command nor Python module is installed. This is an availability
control, not evidence that an Agentic episode causally used feedback.

G1 is still a direct artifact-envelope mode, but may use provider-side
`list_skills` and `read_skill` tools before the final answer. These tools read
only `public/skills`, reject path escape and symlinks, cache repeated reads, and
record skill lookup events. G0 receives no tools.

The old `prompt_assets/form_skills/` and `prompt_assets/evas_guides/` files are
retained only to reproduce sealed pre-r50 releases. The r50 materializer does
not copy or render them; all new comparisons use the real package/mode matrix
above.

The model invokes the image's fixed EVAS directly through ordinary bash,
including pipes, redirection, and compound commands, and inspects logs and
`tran.csv` under `/tmp/vabench-visible/evas-output` itself. The adapter does not
expose a waveform-specific helper or experiment arm, and does not run a
feedback broker, checker, gold comparison, or property diagnosis.
`vabench-submit` is likewise a real,
discoverable shell command that requests runner validation of the final
artifact set.

The shell wrapper records each actual `evas` process invocation independently
of the surrounding bash spelling, so pipes, redirections, and compound commands
do not disappear from telemetry. Campaign results expose the raw invocation
records, skill availability/hash metadata, bash commands that reference
`public/skills`, and a `v4-direct-evas-usage-v2` summary. Each invocation records
the deterministic `candidate_tree_sha256` computed immediately before EVAS
starts over only the task-declared candidate artifact paths; missing artifacts
have a stable state marker. The summary retains succeeded, failed, timed out,
and interrupted counts and adds unique candidate hashes, per-hash call counts,
modified-rerun count, and unchanged-repeat count. These records describe
candidate versions at tool invocation, not causal feedback use; an EVAS nonzero
exit is not promoted to a hidden-checker or behavioral verdict.

An explicit `vabench-submit` ends the episode early and records
`submission_mode=explicit`. It is not a score-eligibility gate: when wall time
expires with a complete declared artifact set, the runner snapshots that final
workspace as `status=workspace_ready` and
`submission_mode=workspace_at_deadline`, then sends the snapshot to the same
trusted judge. `termination_reason=agent_timeout` remains visible, so artifact
correctness and the agent's ability to recognize completion are reported
separately.

Evaluator, gold, and trusted-replay assets remain outside the model-visible
container. A production G2--G5 run requires the shared Docker environment;
`none` is allowed only for unit tests and dry runs. Docker denies network
access and mounts only the current task, submission, and work directories.
Each command has a 64 MiB per-file limit. The runner permits at most 64 MiB in
submission and 512 MiB in work, and captures at most 1 MiB of command output in
host memory. Model observations receive a 12 KiB head/tail summary when output
is larger; telemetry records the original, captured, and truncated byte counts.
Quota violations are reported as `agent_resource_exhausted`, not as benchmark
behavior failures or hidden-test zeroes.
Before trusted
replay starts, the runner also rejects submission symlinks and candidate source
includes that can escape the declared artifact set.

G0/G1 parse exact artifact blocks into the submission directory. In the
mini-SWE path, the model controls direct EVAS invocations over the public
runtime package. DUT/bugfix tasks expose their visible deck. For r52/r53 testbench
tasks, the public runtime exposes only the reference DUT; the five scored
faults remain evaluator-only and are used only during trusted replay.
The legacy native scaffold retains its restricted `run_evas` tool only as a
sensitivity path and is not the default G2--G5 agent.
Its r53 dispatch reuses the canonical public contract selector before executing
fixed argv: runtime-v2 is strict, runtime-v3 is explicitly portable, and
reference-v1 Testbench follows its validated strict/portable mode. Testbench
accepts only the public reference, never a scored mutation. Historical r45-r52
paths keep their existing behavior. This compatibility repair adds no new
trajectory protocol, isolation guarantee, behavioral metric or final feedback.
See [AA-VAE-068](../../../docs/alphaapollo-migration/features/AA-VAE-068-legacy-native-r53-contracts.md).

Direct responses must use the exact artifact envelope contract. The live runner
rejects filename-only markers, input-artifact markers, Markdown fences,
duplicate or out-of-order blocks, undeclared paths, and non-whitespace text
outside the blocks. It preserves the extracted body bytes and records the raw
response hash, parser version, diagnostics, and artifact hashes. A format
failure remains `invalid_submission` and is not passed to a judge.

`audit_direct_protocol.py` can classify deterministic recoverability in stored
historical responses. `reparse_direct.py` may materialize those recovered files
under `evidence/recovered_direct_submission` for diagnosis, but it does not
change the episode status or make the result score-eligible. Recovery therefore
stays separate from the benchmark execution path.

## Provider Credentials

Credentials are loaded from an environment variable or a repository-external
file and are never included in prompts or result JSON. Credential-file paths
and injected operator commands are redacted from wrapper metadata:

```bash
export DEEPSEEK_API_KEY='...'
python3 benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --task-id v4-001 \
  --mode G0 \
  --model deepseek-v4-flash \
  --base-url https://api.deepseek.com/v1 \
  --api-key-env DEEPSEEK_API_KEY \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --output-root /tmp/benchmarkv4-api-smoke
```

Executable campaigns require `--evas-command`; there is no PATH-derived
default. Before the first model request, the wrapper resolves it to an absolute
command and records the executable SHA-256, complete `--version` output
(including version, ABI, and revision), and version-output SHA-256 in
`campaign.json`. The cell runner rechecks that identity before loading provider
credentials. Dry runs may omit EVAS because they execute neither model nor
evaluator.

The provider adapter uses the OpenAI-compatible chat-completions protocol.
Changing providers requires only `--base-url`, the campaign model ID, and
`--api-key-env` or `--api-key-file`.

## Evaluator Adapters

`--final-judge-command` injects the benchmark-controlled trusted replay. It
receives these environment variables:

- `VABENCH_RUNTIME_DIR`
- `VABENCH_PUBLIC_DIR`
- `VABENCH_SUBMISSION_DIR`
- `VABENCH_EVALUATOR_DIR`

The final judge adapter runs once after submission and must use the
release-pinned strict EVAS evaluator. It may additionally dispatch Spectre as
a non-blocking parity audit. Neither its command string nor evaluator directory
is sent to the model. A formal pilot must configure the EVAS final adapter; a
provider-only smoke may omit it only to test API transport and artifact
handling.

### Result protocol

Every completed G0-G5 cell now writes an `experiment_result` object in
`evidence/campaign_result.json` conforming to
`schemas/vabench-experiment-result.schema.json`. The record preserves the exact
last assistant message and its hash, snapshots every declared final artifact
under `evidence/final_submission/`, and records per-file and tree hashes. This
snapshot is the scored submission; later edits to `public/submission` do not
change it. Trusted replay receives the snapshot path in both
`VABENCH_SUBMISSION_DIR` and `VABENCH_FINAL_SUBMISSION_DIR`, and its record binds
the replay to the snapshot tree hash.

The final judge is a trusted replay, not another model-feedback turn. Before it
runs, the runner hashes the exported evaluator tree and records the already
pinned EVAS identity. The adapter
must write JSON to `VABENCH_TRUSTED_REPLAY_RESULT` with one of these statuses:

```json
{
  "status": "behavior_failure",
  "diagnostics": ["slew_limit violated in corner-fast"],
  "failure_taxonomy": {
    "schema_version": "vabench-failure-taxonomy-v1",
    "primary_class": "property",
    "secondary_classes": ["functional"],
    "stage": "property_check",
    "responsibility": "candidate",
    "retryable": false,
    "case_ids": ["corner-fast"],
    "property_ids": ["slew_limit"],
    "mutation_ids": []
  }
}
```

Allowed terminal replay statuses are `passed`, `compile_failure`,
`runtime_failure`, `behavior_failure`, and `infrastructure_failure`. Missing or
malformed structured JSON is an infrastructure failure, even when the adapter
exits zero; process success is not a candidate verdict.

### Opt-in profile-bound final evidence

The trusted Python scoring API now accepts `final_test_profile` and
`episode_context` together. Build the profile with
`final_replay.build_final_test_profile(...)` using the exported evaluator,
r53 release, frozen campaign-config hash, exact judge command/watchdog, and
explicit EVAS 0.8.7 command. Supply that profile and an `EpisodeContext` matching
the cell's episode/task/condition to `score_campaign.evaluate_cell(...)` with
`write_back=False` and `reuse_existing=False`. The campaign CLI's default
generation/scoring route is unchanged; full CLI profile distribution is pending.

The bound path verifies submission and authority identities before and after
replay, writes an immutable content-addressed sidecar, and returns
`row["trusted_replay"]["score_sidecar_receipt"]`. It does not update the original
generation result, checkpoint, or model trajectory. The receipt adds attempt
identity to the sidecar/profile/submission hashes; identical sidecar content in
different runtimes does not mean the attempts are identical.

`evidence/bound-final-test/` reserves terminal execution before the judge starts.
Once reserved, scoring and generation entrypoints reject in-place retry/reentry,
including after an infrastructure failure. Do not remove this directory to
resume a run. AA-VAE-070 cannot retry a reserved final replay either.
The score is `development_only`; no Spectre equivalence, model-quality claim,
complete dependency fingerprint, or native typed trajectory is implied.

For a deterministic three-arm integration check, run
`scripts/run_v4_r53_clean_room_smoke.py --bound-final-authority` with the existing
explicit `--evas-command`, `--output-root`, and `--out` options. On local Docker
VMs, use an output root shared with the daemon. See
`docs/alphaapollo-migration/features/AA-VAE-033-production-final-replay-receipt.md`
and `AA-VAE-034-bound-final-clean-room-ci.md` for exact scope and evidence.

Experiment-result schema v2 adds a required `failure_taxonomy` object to both
the replay and terminal episode record without changing `status`, `outcome`, or
binary-score semantics. Canonical primary classes are `invalid`, `compile`,
`runtime`, `functional`, `mutation_survival`, `property`, `timeout`,
`resource_exhaustion`, `behavior_unspecified`, and `infrastructure`; passing
and not-yet-scored records use `null`. The runner derives unambiguous classes
from artifact gates, execution state, and coarse replay status. A
`behavior_failure` adapter should provide `functional`, `mutation_survival`, or
`property` plus any applicable `case_ids`, `property_ids`, and `mutation_ids`.
For compatibility, an adapter that omits `failure_taxonomy` remains scoreable
as `behavior_unspecified`. An invalid or status-incompatible supplied taxonomy
marks the replay as `infrastructure_failure` instead of silently corrupting
analysis labels; the raw adapter JSON is retained.

`score_campaign.py` copies the normalized object into each analysis row and
flattens `failure_class`, `failure_stage`, `failure_responsibility`, and
`failure_retryable`. Score-report schema v2 aggregates `failure_classes`,
`secondary_failure_classes`, `failure_stages`, `failure_responsibilities`,
`failure_retryability`, failed case/property/mutation ID counts, and
per-form/per-mode/per-arm `failure_breakdown`.

Model execution is separate from replay execution. `agent_timeout` without a
complete artifact and `no_submission` have `score_eligible: false` and
`score: null`; neither is reported as a hidden-test or behavior zero. A complete
workspace produced before the wall-time boundary may still enter trusted replay.
Trusted replay timeouts are
`runtime_failure`, while launch and malformed-result failures remain
`infrastructure_failure`.

Operational failures are also recorded on an orthogonal `incidents` axis.
Each incident identifies its phase, component, category, responsibility, and
retryability. This separates provider request timeouts, sandbox/preflight
failures, runner failures, and direct EVAS command failures without replacing
the final artifact/checker outcome. In particular, a failed exploratory EVAS
call can coexist with a later passing final submission.

The historical `feedback_adapter.py` remains only to reproduce old experiments.
It reads evaluator assets and must never be configured as an active G2-G5 model
tool. The legacy native sensitivity scaffold retains `run_evas`; current
mini-SWE runs invoke the pinned `evas` executable directly and receive only its
raw public simulation output, never a checker or score oracle.

Generated campaign manifests, runtime workspaces, API responses, simulator
outputs, and credentials belong outside the repository. Only runner source,
tests, schemas, and compact aggregate reports should enter a PR.

## Opt-in Native Episode Result Join

`native_episode.run_native_episode(...)` composes a caller-owned typed policy
and environment with the existing controller and production final replay. It
does not replace `DefaultAgent`, launch a provider, install `run_evas`, or add a
campaign CLI mode. Mini-swe bridges remain available as caller components.

The trusted coordinator supplies a fresh, exclusively owned runtime,
`EpisodeContext`, policy/environment/registry, a validated backend profile hash,
public/final profiles frozen before generation, and the existing final command,
watchdog and EVAS executable. The environment's freeze callback must use the
existing submission snapshot and return its real `FrozenSubmission`.

The API reserves `evidence/native-episode` before policy entry. It writes a
request journal, the controller's native trajectory, and an outcome journal;
only verified terminal evidence produces an atomic, non-overwritable
`scored-results/<artifact_sha256>.json`. The returned `NativeEpisodeRun` contains
the typed outcome, trajectory path, optional artifact path and verified sidecar
receipt. All of these terminal outputs are trusted coordinator data, never
model feedback. Unscored failures have no fabricated score; classified final
infrastructure failures retain `score=null`.

Native attempts cannot resume in place, including through the old campaign
entry point after a pre-scoring failure. A crash or publication failure keeps
the runtime reserved. Later campaign retry/ledger/archive/public-dispatch
additions are documented above; AA-VAE-070 adds only outer batch recovery.
The caller retains environment cleanup responsibility on preflight rejection;
the controller owns normal cleanup after it starts.

Test the bounded same-chain integration after building the pinned images:

```sh
VABENCH_TEST_DOCKER_RUNTIME=1 uv run --locked --extra agentic python -m pytest -q \
  tests/test_agent_harness_native_episode.py::test_r53_docker_native_episode_result_join
```

On local Docker VMs, place pytest `--basetemp` under a shared workspace path.
The deterministic public-contract stub and test-only public-tool router prove
pipeline binding, not a model baseline or an activated domain tool. See
`docs/alphaapollo-migration/features/AA-VAE-036-native-episode-result-join.md`.

## Score A Completed Campaign

Run a judge adapter over every complete submission and aggregate model, form,
mode, token, tool, and outcome records:

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py \
  --campaign-output /tmp/v4-calibration-smoke \
  --judge-kind final_trusted_replay \
  --judge-command \
    "python3 /path/to/trusted_replay_adapter.py"
```

`score_campaign.py` resolves campaign/output paths and existing judge-command
script paths to absolutes before invoking adapters, so the command is safe to
run from either the workspace root or `behavioral-veriloga-eval/`.

`feedback_evas` reports are always marked `provisional_feedback_only`; they
are useful for pilot tuning but are not benchmark scores. A paper-facing run
must use `--judge-kind final_trusted_replay` with the sealed, pinned strict
EVAS adapter. `--judge-kind final_spectre` is retained only for optional parity
audits and does not gate a score claim. Missing or invalid submissions remain
explicit denominator failures and are never silently dropped.

Historical pilot runs produced before submission-path normalization can be
repaired without another model call when every required candidate is found
under one unique common extra directory and no competing target copy exists:

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/repair_submission_layout.py \
  --campaign-output /tmp/v4-calibration-smoke
```

The repair is path-only, preserves artifact hashes, and records the stripped
prefix and each promotion. It rejects partial bundles, symlinks, and ambiguous
or competing prefixes. Recovered candidates remain
`submission_protocol_compliant=false`, and the formal scorer treats them as not
submitted.

Legacy agentic episodes checkpoint the public conversation, cumulative provider
output tokens, tool events, and current submission after every model and tool action.
`--resume` continues the same episode after an infrastructure interruption;
it does not reset the wall-time episode budget, create another sample, or grant another
pass@k opportunity.

Independent cells may run concurrently with `--workers N`. Each worker writes
only its own cell runtime; keep `--workers 1` when diagnosing provider rate
limits or simulator resource contention.

## Opt-in native mini-swe single-cell launcher

`run_native_mini_swe.py` is a separate, development-only entry point for a
OneShot, Agent-No-EVAS or Agentic DUT/bugfix/Testbench cell from `build_campaign.py`. It does not replace the
legacy runner or reinterpret `--agent-scaffold native`.

```bash
uv run --locked --extra agentic python \
  benchmark-vabench-release-v4/operations/calibration_pilot/run_native_mini_swe.py \
  --campaign /absolute/path/campaign.json \
  --cell v4-001-G2-r00-agentic \
  --output /absolute/path/new-native-attempt \
  --dry-run
```

Dry-run only exports a fresh runtime: no credentials, Docker, model, or scoring.
For a separately authorized executable run, omit `--dry-run` and provide
`--base-url`, `--api-key-env` (default `VABENCH_API_KEY`) or `--api-key-file`, and
an absolute pinned `--evas-command`. Agentic uses the pinned public Docker image;
No-EVAS uses the paired no-EVAS image; OneShot has no Bash runtime image.
Legacy `execution_config` overrides are rejected; this
launcher currently fixes its own documented runtime/watchdog defaults.

Every invocation requires a new output directory, including after dry-run or
failure. There is no resume or automatic episode retry. Campaign integration
uses the explicit backend option described below, not this single-cell CLI.
Canonical wall time applies; complete timeout workspaces remain score-eligible
with `terminal_reason=agent_timeout`. Request/command timeouts plus verified
Docker pause before freeze are not an asynchronous hard real-time guarantee.

Private decoded provider exchanges and bounded Bash observations are kept in
`runtime/evidence/native-launcher/`; controller trajectory and the immutable
scored artifact remain in `runtime/evidence/native-episode/`. Final EVAS output
never becomes the next model observation. Raw transport retries/SSE frames and
untruncated tool logs are not archived. Strict single-action parsing differs
from legacy recovery/multi-action handling, so this is not a parity claim.
See `docs/alphaapollo-migration/features/AA-VAE-037-native-mini-swe-launcher.md`
for code mapping, evidence and remaining gates.

The executable legacy/native behavior matrix is documented in
`docs/alphaapollo-migration/features/AA-VAE-038-mini-swe-behavior-differential.md`.
Native model-format rejections now terminate as `protocol_failure`, not a
provider/infrastructure outage. Provider timeout/API/context exceptions remain
coarse `backend_failure` in the native result, with the original type retained
in private events; the legacy campaign's finer taxonomy is not yet integrated.
Normal scripted single-action request/feedback/candidate parity does not imply
equivalence of recovery, multi-action, deadline, or full campaign behavior.

### Mixed-backend campaign evidence bridge

The existing `scripts/run_v4_r53_clean_room_smoke.py` now accepts
`--agentic-backend native-mini-swe --bound-final-authority` for DUT/bugfix.
OneShot stays legacy direct and Agent-No-EVAS stays legacy mini-swe. The
pre-generation campaign file and report explicitly name this routing as
`mixed-backend-connectivity-v1`; it cannot support a matched backend or EVAS
effect comparison. Without the new option the legacy smoke is unchanged.

`score_campaign.read_native_cell(runtime, cell, campaign_file_sha256=...)`
validates and reads already-terminal native evidence without executing a judge,
refreezing a candidate, or writing a fake legacy generation record. Unscored
protocol/provider failures retain null scores. Corrupt or missing evidence
blocks reading; the smoke retains the affected native cell as an infrastructure
failure. `summarize(..., scheduled_cells=cells)` rejects missing/duplicate/extra
or mismatched identities before aggregation. The legacy scorer CLI does not
automatically discover or rescore native runtimes.

See `docs/alphaapollo-migration/features/AA-VAE-039-native-campaign-evidence-bridge.md`.
That dated mixed-backend slice is preserved as regression evidence. Native
three-condition support and bounded infrastructure retries are now available
via the separate opt-in below; real-model comparisons remain separately gated.
R53 and EVAS 0.8.7 are unchanged.

### Opt-in all-native three-form campaign

The existing wrapper accepts `--episode-backend native-mini-swe` with
`--comparison-profile executable-feedback-control`. Select the intended forms
explicitly; Testbench public feedback uses only the supplied reference DUT.
In-place resume and post-freeze `--cell`/`--limit`
selection are unsupported. Keep `--agent-scaffold mini-swe` (default): the old
`--agent-scaffold native` flag still means the legacy sensitivity controller.

```bash
uv run --locked --extra agentic python \
  benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --output-root /absolute/path/fresh-native-campaign \
  --model MODEL_ID --task-id v4-001 --form dut \
  --comparison-profile executable-feedback-control \
  --episode-backend native-mini-swe --dry-run
```

An executable run needs another fresh output root, declared provider credentials
and endpoint, and `--evas-command /absolute/path/to/evas`. OneShot is one logical
generation using output-only `submit_artifacts`; No-EVAS uses the paired
no-EVAS image and absent public profile; Agentic retains public EVAS access.
All conditions use the same native freeze/final sidecar path. No automatic
episode retry is enabled by default; existing low-level provider transport retry remains.
For Reasoning, use `--episode-backend native-reasoning` in both wrapper and
score command. Freeze `--reasoning-proposal-format native_tool_calls` (default)
or `strict_json` before generation; scoring rejects mismatches. The two Bash
arms use the distinct Reasoning policy; OneShot keeps the common output-only
artifact submission transport. Use separate roots for backend comparisons.

For a reviewer-safe record ledger, add `--ledger-output /absolute/path/new-ledger.json`
to native scoring. Keep this new file outside the generation output root. It
contains complete schedule/attempt identity, paired coverage, all-attempt costs,
deadline analysis and a bounded claim index, not prompts or hidden diagnostics.
The private score report references the ledger hashes. Evolution cannot be
pooled into this single-trajectory ledger.

For fresh-attempt infrastructure recovery, set `--native-max-attempts N` on the
campaign wrapper before freezing the campaign. Only typed pre-final transport
or sandbox-startup failure can retry, never cleanup/protocol/deadline/final
failure. Every attempt has a fresh export/client and immutable lineage. Scoring
counts one terminal row per cell and includes failed attempts in primary costs;
unknown usage stays null. In-place resume remains unsupported. See AA-VAE-045.

Native scoring reads the full frozen schedule and existing evidence, without
calling EVAS again or requiring `--judge-command`:

```bash
uv run --locked --extra agentic python \
  benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py \
  --episode-backend native-mini-swe \
  --campaign /absolute/path/fresh-native-campaign/campaign.json \
  --campaign-output /absolute/path/fresh-native-campaign/run \
  --judge-kind final_trusted_replay
```

Missing/corrupt evidence blocks the report; valid infrastructure failure
receipts remain in the denominator with null scores. The score authority is
`development_only`, never Spectre-backed implicitly. The nine-cell Docker gate
uses deterministic public-contract candidates, not a model benchmark result.
See migration notes AA-VAE-040 through AA-VAE-043 for code/evidence maps.
