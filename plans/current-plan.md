# vaEVAS AI-Native Harness Evolution Plan

Updated: 2026-09-01

Completed detail and the original design matrix are preserved in the
[dated plan snapshot](archive/2026-08-30-harness-plan-snapshot.md).
This file is the active queue, not a cumulative execution log.

For the current cross-cutting backlog, read the [global follow-up roadmap](../docs/alphaapollo-migration/03_全局后续路线_2026-08-31.md).
It separates implemented core infrastructure from extension wiring, fairness,
real-model evidence, reporting and separately gated training work.

Human review checkpoint (2026-08-30): the user requested a current-state record
before reorganizing the project. Read the [capability and gap snapshot](../docs/alphaapollo-migration/02_项目现状与功能缺口_2026-08-30.md)
at baseline `f1a2a06db7`. This documentation-only checkpoint starts no new
implementation and does not change the phase statuses below.

## Current Status

- Implemented locally: [adversarial acceptance and read-only framework adapter](adversarial-and-result-adapter.md).
  These are separate goals: runtime/checker boundary regressions versus framework
  interoperability and execution-efficiency groundwork. Preserve r53/EVAS and
  existing scheduling/retry ownership; no paid run. Five real Docker/EVAS attack
  and control cases pass; the optional Inspect adapter passes its 13 official
  API tests. Active regression: 1,450 passed / 65 optional skips / one absent
  historical fixture deselected. Historical-inclusive sparse checkout failures
  are recorded, not hidden. Main closes review and fork publication separately.
  Next performance work is measured workers=1/2/4 execution profiling and a
  bounded execution-adapter design, not relabeling result-import timing.

- Activated: [authorized Verilog-A reference corpus](veriloga-corpus-activation.md),
  an AA-VAE-074 follow-up. User contributor authorization resolves project use.
  Four general files at `7c5d3f03a162ee8131103e9551eee842424360bb` are present
  locally and pass exact-byte plus deterministic source-retrieval tests; public
  manifest/authorization/tests reuse reviewed-v2 without runtime changes.
  Cadence was not found and is omitted as requested. Focused adjacent checks:
  **146 passed / 5 optional Docker skips**. No paid request, no full combined
  score on these real docs, no EVAS/r53 change or model-quality claim.
  Activation source is `7313f98507`; independent review found no actionable
  issue. Actual-source gate is 8/8. Hosted CI is separate from local acceptance.

- Implemented and published; exact-source hosted gates passed:
  [combined public-tool acceptance](combined-tools-acceptance.md), AA-VAE-073–075.
  Evolution coordinator waveform sharing, reviewed local corpus contracts and
  a separate combined live entrypoint are wired. Stable-tree actual Docker/EVAS
  with synthetic model replies/external HTTP: **36 passed** after final scope
  hardening; active local regression **1,380 passed / 53 optional skips**, one
  absent historical V3 fixture explicitly deselected. Reports require
  actual docs/waveform use and next-round exposure, not merely enabled flags;
  candidate/input binding, all-branch costs and one final replay are preserved.
  Existing legacy comparison, r53 and EVAS 0.8.7 remain unchanged. No actual keys,
  paid calls or third-party corpus text imported in that earlier slice.
  Main owns integration/Git;
  delegated writing is closed. Seven focused commits through `6ac7482d4b`
  are on fork main; Evaluator Closure, Runner Smoke and Public Agent Runtime
  all passed. Hosted full checkout: **1,557 passed / 56 optional skips**;
  new combined Docker/live-fixture stage: **36 passed**. See verification log.
  Source: `cbfe1e2743` (corpus), `ff17ec4788` (Evolution waveform),
  `18bcd2a547` (combined wiring), `73b6a4aa8f` (CI), `421e430808` (claim labels).
  Real-doc activation is addressed above. Next gates: re-review dated
  provider profile after 2026-08-31 UTC, then a separately budgeted real-model
  run. These are experimental/activation gates, not missing tool wiring.

- Implemented: [explicit live comparison entrypoint](legacy-native-live-entrypoint.md),
  AA-VAE-072. Reuse AA-VAE-071 with a frozen provider profile and explicit
  manifest/cap launch assertion; prepare/inspect/run/report remain separate.
  Runtime `00eb11e7c1`, CI wiring `39123500cc`: real Docker/EVAS with synthetic
  external HTTP **62 passed**; active regression **1,398 passed / 50 optional
  skips**; independent review found no required correction. Four focused commits
  are on fork main through `58829c7172`; all three exact-source hosted workflows
  passed (**1,500 full-checkout regression passes / 53 optional skips**, new live
  stage **21 passes**, all existing Docker stages). No actual key, provider
  request or paid run was used.
  A real comparison still needs fresh dated preparation and new fee authority;
  implemented launch controls do not constitute model-performance evidence.

- Implemented free [legacy/native comparison engineering gates](legacy-native-comparison-engineering.md),
  AA-VAE-071: shared spending admission, immutable six-cell schedule, observed
  public-input/environment/request audit, and read-only cross-backend joins.
  Real Docker/EVAS with scripted responses: **41 passed**, including six scored
  cells, three matched surfaces, unknown-cost/admission stops and no reentry.
  Independent follow-up review found no remaining source-level blocker.
  Active r53/harness gate: **1,380 passed / 46 optional skips**. Six focused
  commits are published to fork main through `8609747ccb`; full hosted
  exact-source Evaluator Closure, Runner Smoke and Public Agent Runtime all
  passed (**1,482 regression passes / 49 optional skips**, plus all Docker
  stages). The local full
  historical suite is not GREEN because sparse checkout
  excludes V3/old-v4/r52/provenance fixtures. Preserve this storage choice;
  the successful hosted full checkout verifies their compatibility separately.
  The [archived native coverage audit](../docs/alphaapollo-migration/experiments/native-toolchain-coverage-20260831.md)
  has one historical real native DUT score out of six native combinations.
  It is separate from this free family001 six-cell fixture and the family029
  paid pilot. No new paid call, benchmark/evaluator change or budget reuse.
  AA-VAE-072 now supplies the explicit live transport gate. Next experimental
  step: freshly review/freeze named service/model/rates/decoding and obtain new
  fee authority, then run the separate real-model comparison.

- Publication correction: all nine commits through `e2498952bb` are on
  BucketSran main. Exact-source Evaluator Closure, Runner Smoke and Public Agent
  Runtime workflows passed. Dated local-only entries below describe the earlier
  handoff, not the current publication state; their historical evidence is kept.

- Implemented: [batch-level recovery](batch-resume.md), AA-VAE-070. Add verified
  terminal-cell reuse and missing-cell scheduling to native/Evolution; preserve
  frozen configuration, attempt/call accounting and final no-reentry. Main owns
  integration; independent source reviews are complete. No paid
  run, keys, r53/EVAS mutation or historical evidence adoption. Acceptance and
  test-first execution sequence are in the linked brief. Native and Evolution
  cross-process reuse and real task-form regressions pass; final full gate is
  1,226 passed / 39 skipped. Local closure does not imply hosted CI, publication
  or real-model quality evidence.

- Completed bounded repair (audit-task handoff, base `dee9ccfeb0`): pass the frozen
  pilot manifest's `cap` into the existing `DeepSeekPilotBudget`. Main owns only
  the exact leaves in `work-ownership.md`. Acceptance/KPIs: a CNY 0.01 fixture
  opens journal/index at that cap and admits no HTTP; manifest-cap drift rejects
  before native execution; six-row, unknown-cost and no-resume behavior stays
  intact. Plan: regression RED, minimal parameter binding, drift regressions,
  focused/static checks, independent review, local commit and handoff. Stop on
  ownership drift or a required guard/scoring redesign. No paid run, credentials,
  private trace access, r53/EVAS edit or push is authorized by this repair.
  KPIs met: focused 119 passes / 5 optional Docker skips; layout/navigation
  64 passes; independent read-only review found no required correction. Local
  commit only; full typechecking, fresh Docker/final scoring and hosted CI are
  not claimed. Main returns the exact commit to the requesting audit task.

- Prepared: [legacy/native mini-swe comparison protocol](legacy-native-comparison-protocol.md)
  ([AA-VAE-069](../docs/alphaapollo-migration/features/AA-VAE-069-legacy-native-comparison-protocol.md)).
  Six planned Agentic cells cover family001 DUT/bugfix/Testbench; public source
  snapshots and synthetic request differences are separate from full export
  audit. Focused gate: 115 passes / 3 skips; real common-environment Docker
  mount audit: 2 passes. No model call or production/r53/EVAS change.
  Source `8ccb616fe7` is published to fork/main; both exact-source hosted
  workflows pass (1,348 regression passes / 42 skips and all existing Docker
  stages). Protocol preparation is closed; the live-study gates below stay open.
  The original real-study blueprint stays unstarted and immutable. AA-VAE-071
  separately implements/tests its free launch gates, and AA-VAE-072 supplies
  the opt-in live adapter. Fresh model/rates/decoding/fee authorization and the
  real run remain. This is a workflow comparison, not pure-controller attribution.

- Completed bounded repair: [legacy native r53 compatibility](legacy-native-r53-contract-compatibility.md)
  ([AA-VAE-068](../docs/alphaapollo-migration/features/AA-VAE-068-legacy-native-r53-contracts.md)).
  Repaired the separate `--agent-scaffold native` sensitivity public tool using
  the canonical r53 selector, while preserving historical supported behavior.
  New tool-boundary tests: 55 passes; local harness/entrypoint gate: 1,125 passes
  / 34 opt-in skips. Independent code/document review found no required correction.
  Source `08f2c9310f` is published to fork/main; both exact-source hosted gates
  pass, including 1,342 regression passes / 40 skips and all Docker stages.
  No release/evaluator, default backend, score, selection or paid-run change.

- Implemented bounded repair: [r53 public contract compatibility](r53-public-contract-compatibility.md)
  ([AA-VAE-067](../docs/alphaapollo-migration/features/AA-VAE-067-r53-portable-public-contracts.md)).
  The six released portable contracts are accepted by the fixed public adapter;
  all 1,200 contracts preserve command/scope and invalid combinations fail closed.
  Focused gate: 192 passed / 20 skips; three Docker groups cover 17 passing cases,
  including explicit negative simulation/verdict checks. No blocking review
  finding; source `2e1ec6ba32` is published to fork/main. Both exact-source hosted
  workflows pass; broader CI regression is 1,287 passed / 40 skips, followed by
  all real Docker stages. Exact evidence is in the verification log.
  EVAS 0.8.7 still rejects v4-102 public dynamic-array support. The separately
  identified old native sensitivity compatibility gap is handled by AA-VAE-068
  above; it was not part of AA-VAE-067's implementation or verification.
  No r53/EVAS, candidate ranking, behavioral scoring or paid-run change.

- Completed human-review preparation: [single-task case study plan](single-task-harness-case-study.md)
  and [Chinese code/evidence walkthrough](../docs/alphaapollo-migration/05_单任务代码与轨迹案例_2026-08-31.md).
  Existing scripted-provider waveform smoke validated read-only; code boundaries,
  event sequence, zero-score outcome and legacy/native differences are explicit.
  Independent review found no required correction; focused gates passed.
  The next matched experiment protocol remains separate from this case study.
  No new runtime feature, model API call, evaluator invocation or evidence rewrite.

- Completed overnight request: [engineering closure queue](overnight-engineering-closure.md).
  The user authorized completing current free engineering gaps, not only the
  two waveform slices. Preserve separate gates for real data, paid experiments,
  training and benchmark changes. AA-VAE-061–066 implement native waveform
  feedback, synthetic training metadata conversion, paired/case reports,
  Evolution generation-surface repair, branch-local synthetic docs and declared
  information-surface/failure reporting. Each is independently reviewed and
  separately committed. Full final harness gate: 1013 passed / 25 opt-in skips;
  final real Docker gate: 12 passed. Final source `8d782880c7` hosted gates are
  green (broader suite 1253 passed / 31 skipped); exact links are in the log.
  Read the [morning audit](../docs/alphaapollo-migration/04_夜间工程闭环审计_2026-08-31.md)
  for commits/code maps and external data/experiment/protocol gates. No new paid run.

- Implemented bounded follow-up: [trusted public waveform executor](trusted-public-waveform-executor.md)
  ([AA-VAE-060](../docs/alphaapollo-migration/features/AA-VAE-060-isolated-public-waveform.md)).
  Fresh public-only execution binds candidate/profile/invocation/output receipts.
  Final local gate: 939 harness passes / 21 opt-in skips; two real DUT/Testbench
  Docker tests (two fresh executions each). Independent review found no code issue;
  LSP/typecheck was unavailable, with Ruff/AST/compilation checks recorded instead.
  Published source/CI head `cfd11121a0`: all three triggered hosted workflows
  passed; exact source-bound links are recorded in the verification log.
  AA-VAE-060 itself did not activate a model tool. The separately reviewed
  [explicit native feedback slice](native-public-waveform-feedback.md) now adds
  opt-in tool activation, source-container pause/resume, incomplete-candidate
  recovery, budget admission and score identity joins. No paid run.

- Implemented bounded slice: [synthetic extension implementation](rag-waveform-training-implementation.md).
  [AA-VAE-057](../docs/alphaapollo-migration/features/AA-VAE-057-synthetic-offline-docs.md)
  adds explicit synthetic docs to native mini-swe/Reasoning through a Python API,
  shared budgets and trajectory/freeze/score identity. That slice did not activate
  Evolution; AA-VAE-065 subsequently adds its explicit synthetic Python API.
  No default/CLI activation; ordinary aggregate rejects extensions until a matched protocol is frozen.
  [AA-VAE-058](../docs/alphaapollo-migration/features/AA-VAE-058-bounded-waveform-parser.md)
  is a verified standalone CSV parser (12 tests), not a model-visible waveform tool.
  [AA-VAE-059](../docs/alphaapollo-migration/features/AA-VAE-059-synthetic-training-export.md)
  is a verified synthetic projection/validator (24 tests), not real trace export
  or training. Main owns shared wiring/review/publication; see verification log
  for final suite and Docker evidence. No real data, credentials or paid calls.
  Published runtime head `fdff3460f2`: all three triggered hosted workflows passed.
  Local final gate is 908 harness passes / 19 opt-in skips and two real docs
  Docker/EVAS passes. Feature commits and source-specific hosted links are in
  the verification log; this is not evidence of model-quality improvement.

- Remaining extension gates, from [AA-VAE-056](../docs/alphaapollo-migration/features/AA-VAE-056-rag-waveform-training-design.md):
  approve/license/decontaminate an actual public corpus and freeze matched RAG
  conditions before real-corpus/CLI/aggregation rollout. Native waveform feedback
  and synthetic Evolution docs are now implemented; extending waveform into
  Evolution selection/shared feedback requires a separately defined protocol;
  separately authorize actual trajectory export, splits/provider use and training.
  These are explicit follow-ups, not evidence from synthetic tests. r53/EVAS and
  stopped live evidence stay unchanged; no automatic paid rerun.

- Implemented follow-up: [public EVAS feedback and extension design](public-evas-feedback-and-extension-design.md).
  [AA-VAE-055](../docs/alphaapollo-migration/features/AA-VAE-055-public-evas-process-feedback.md)
  adds native layered Bash/EVAS reports and reported-operation diagnostics.
  Review identified forgeable sandbox markers: data is explicitly unauthenticated,
  not hard-budget/validator/final authority. Trusted per-process accounting needs
  a separate isolated executor. Three read-only extension designs are complete;
  no RAG/waveform tool activation, corpus ingestion, training or paid run in AA-VAE-055.
  Final local gate: 849 harness passes / 17 opt-in skips; 2 real Docker/free-HTTP
  smoke passes. Independent scoped review approves; historical compact-checkout
  missing-script test limitation is retained in the verification log.
  Runtime repair published separately as `9da787b638` to fork/main.

- Implemented authorized repair: [native operational contract and optional call budget](native-operational-contract-and-call-budget.md).
  [AA-VAE-053](../docs/alphaapollo-migration/features/AA-VAE-053-public-operational-contract.md)
  repairs Reasoning's condition-appropriate Bash/submit guidance, independently
  published as `ad40f11496`.
  [AA-VAE-054](../docs/alphaapollo-migration/features/AA-VAE-054-optional-model-call-budget.md)
  adds an optional positive call limit, trusted remaining-budget observations,
  unscored exhaustion and cumulative attempt accounting. Eight remains a pilot
  parameter, not a general harness/r53 rule. Independent reviews pass; final
  free-fixture verification and publication evidence are recorded in the log.
  No paid rerun is authorized by this implementation task.

- Bounded experiment executed and safely stopped: [DeepSeek pilot audit](../docs/alphaapollo-migration/experiments/deepseek-pilot-20260830.md).
  The user confirmed GLM Coding Plan only, then explicitly chose DeepSeek API.
  Use the saved DeepSeek key and `deepseek-v4-flash`; do not call GLM.
  Keep one seeded family, three forms, two Agentic backends, one repetition
  and the CNY 5.00 ceiling. Safe local credential parsing is verified (AA-VAE-051);
  the earlier DeepSeek-only guard remains verified separately (AA-VAE-050).
  Driver/free Docker/EVAS gates passed (AA-VAE-052). Live run: 16 HTTP attempts,
  2 censored DUT cells and 4 unstarted cells; no scored submission. An SSL
  handshake failure stopped the shared budget. CNY3.420315 is the conservative
  committed/reserved upper bound, not an invoice. No automatic paid rerun.
  [Offline trajectory diagnosis](../docs/alphaapollo-migration/experiments/deepseek-pilot-20260830-diagnosis.md)
  is complete: the stopped run lacked Reasoning's public Bash/submit contract
  and both backends' call horizon. AA-VAE-053/054 now repair those defects for
  future runs; the old evidence remains unchanged. Path/status and installed-example
  boundaries are also recorded. This is not authorization for a paid rerun. The
  development pilot does not change r53's normal wall-time policy or authorize
  full-r53/Evolution execution.

- Completed authorized follow-up: [remaining harness closure](remaining-harness-closure.md).
  The user approved completing the remaining functionality. Native Testbench
  public authority and nine-cell Docker integration are locally verified in
  [AA-VAE-043](../docs/alphaapollo-migration/features/AA-VAE-043-native-testbench-reference-authority.md).
  Evidence/metering and safe reviewer exports are integrated and locally verified
  in [AA-VAE-044](../docs/alphaapollo-migration/features/AA-VAE-044-native-evidence-metering.md).
  Fresh-attempt recovery is runtime-integrated in
  [AA-VAE-045](../docs/alphaapollo-migration/features/AA-VAE-045-native-fresh-attempt-recovery.md).
  Reasoning is runtime-integrated in
  [AA-VAE-046](../docs/alphaapollo-migration/features/AA-VAE-046-reasoning-runtime.md).
  The native result ledger is integrated in
  [AA-VAE-048](../docs/alphaapollo-migration/features/AA-VAE-048-native-result-ledger.md).
  Evolution is runtime-integrated in
  [AA-VAE-049](../docs/alphaapollo-migration/features/AA-VAE-049-production-evolution.md),
  with real Docker two-model/two-round connectivity across all three forms.
  Final runtime commit `164131a8a4` is published to fork/main; all three triggered
  hosted workflows passed. Local final harness gate: 702 passed / 11 skipped.
  Implementation and real-model experimental evidence remain separate gates.
  The bounded DeepSeek pilot above is complete as a stopped operational run,
  not as a scored six-cell experiment; broader real-model evidence remains open.

- Earlier completed milestone: [native DUT/bugfix three-arm campaign](native-three-arm-campaign.md).
  Implemented absent public authority, native conditions and minimal
  existing-campaign dispatch/accounting. Testbench is extended by AA-VAE-043;
  opt-in infrastructure retries are added by AA-VAE-045. Legacy defaults and frozen assets are unchanged.
  Shared absent-authority contract is locally verified in
  [AA-VAE-040](../docs/alphaapollo-migration/features/AA-VAE-040-absent-public-authority.md);
  launcher/campaign integration and real six-cell smoke are locally and hosted verified
  in [AA-VAE-042](../docs/alphaapollo-migration/features/AA-VAE-042-native-three-arm-campaign.md).
  Final runtime commit `c2da249c8a` is published to fork main; all workflows
  triggered by it passed. No new implementation slice is opened by this closeout.

- Phase 0/1/3/4 bounded contracts and compatibility work are complete.
- Phase 2/5 native integration is implemented: all three forms/arms,
  fresh-attempt recovery, private capture, safe ledgers and Evolution composition
  are verified through deterministic integration gates.
- Phase 6 is runtime-integrated and deterministically verified (AA-VAE-046),
  with real-model evidence still pending. Phase 7/8 runtime integration is
  implemented; Phase 9's authorized bounded DeepSeek pilot ran and safely stopped,
  without a scored submission or authorization for a new paid run. Phase 10
  runtime closeout is verified and fork-published.
- Legacy mini-swe remains default. Native format recovery, multi-action and
  deadline behavior intentionally differ; see [AA-VAE-038](../docs/alphaapollo-migration/features/AA-VAE-038-mini-swe-behavior-differential.md).
- Earlier local broad regression retained **636 passed / 7 skipped / 1 failed**
  (the legacy one-second timeout case). Hosted CI success is separate evidence,
  not a replacement for that failure. The newer compact-checkout result below
  has additional missing-asset failures. Exact results: [verification log](../logs/verification-log.md).

## Earlier bounded slice: all-native DUT/bugfix campaign (AA-VAE-040–042)

Native OneShot uses one logical output-only generation; No-EVAS uses explicit
authority absence and the paired no-EVAS runtime; Agentic keeps public EVAS.
The existing campaign wrapper now has a distinct native opt-in and the scorer
requires the frozen schedule, preserving null-score infrastructure failures.
Six deterministic Docker/EVAS cells pass, with immutable evidence joins and
read-only aggregation. Relevant local suite: 492 passed / 5 skipped.
Broad historical suite is not green on the compact checkout (34 failed,
657 passed, 8 skipped, 12 errors); absent V3/r45/r52/provenance/runtime assets
are an explicit validation limitation, not permission to restore history.
Independent review has no substantive blocker; LSP diagnostics were unavailable.
Final runtime commit `c2da249c8a` passed hosted Evaluator Closure (703 passed /
11 skipped), every Docker smoke including all six native cells, and Runner Smoke.
Hosted full-checkout success is separate from the local missing-asset limitation.
No paid model experiment or full closure is claimed.

### Previous bridge checkpoint (AA-VAE-039)

Implemented, fork-published and hosted-verified: a deterministic one-task/three-arm gate
reuses the campaign manifest, legacy OneShot / Agent-No-EVAS, and opt-in native
Agentic. The read-only native evidence projection checks trajectory, freeze,
profile and sidecar joins, preserves null-score failures, and gates aggregation
on the exact scheduled cells. No fake legacy record or repeated final scoring.
Real Docker passes; independent review is COMMENT (code APPROVE, architecture
WATCH for private-path coupling). Hosted regression: 660 passed / 10 skipped;
both mixed-native and legacy Docker smokes pass. Exact evidence is in the log.

This is explicitly mixed-backend connectivity, not parity or model quality.
Its absent-authority and bounded campaign CLI follow-ups are now implemented
above. Retry, Testbench and broader experiment coverage remain separate slices.
Keep legacy defaults, r53 and EVAS unchanged; no API experiment yet.

## Objective

Evolve the current VABench r53 evaluation harness into a reusable AI-native
agent harness by combining:

- AlphaApollo-style reasoning, round-based multi-model evolution, explicit
  memory, and verifier-driven refinement;
- coding-agent workspace, shell, editing, sandbox, and event-loop patterns;
- vaEVAS-owned validation/test authority, submission freeze, trusted replay,
  evidence, and claim boundaries.

The first production target is not SFT or RL. It is a differential harness with
the existing mini-swe backend retained, a new single-trajectory AlphaApollo
reasoning backend, and a separately named AlphaApollo evolution condition.

## Frozen boundaries

- Benchmark: immutable VABench v4/r53 at
  `benchmark-vabench-release-v4/release/benchmarkv4-r53/`.
- Evaluator/runtime: `evas-sim==0.8.7`.
- Do not modify r53 task bytes, manifests, evaluator fixtures, or EVAS.
- Spectre remains outside the routine path unless EVAS changes or an explicit
  external protocol activates the compatibility gate.
- Write only to the BucketSran behavioral-eval fork. Do not push upstream.
- Preserve the older dirty EVAS worktree and its existing
  `fix/dynamic-zero-period-timer` changes.
- Use only public AlphaApollo and public coding-agent implementations and
  documentation. Do not read or copy private AlphaApollo project material.

## Development ownership and integration

The main coordinator owns shared interfaces, plans/logs, integration, and all
Git publication. Delegated tasks are read-only unless assigned exact,
non-overlapping files in [work-ownership.md](work-ownership.md). The native
condition and campaign leaf lanes are closed there; shared contracts remain
coordinator-owned. The historical result-store task is complete;
the unfinished dispatch task's interface question is reassigned to the main
coordinator for review, not automatic implementation. This ownership register
does not alter benchmark model/evolution concurrency; current runtime closure
is recorded separately in the phase statuses and verification log.

## Approved architecture decisions

1. Keep mini-swe as a supported backend and regression baseline.
2. Add AlphaApollo reasoning as a matched single-trajectory backend.
3. Add AlphaApollo evolution as a separate, explicitly budgeted condition.
4. The first evolution version uses different models in parallel, immutable
   round feedback snapshots, and deterministic candidate selection.
5. Keep Bash as a sandboxed coding tool. Bash is an action capability, not the
   action serialization protocol.
6. Use versioned JSON/native function calls as the canonical action and
   observation protocol. XML may delimit prompt context but is not an
   authoritative tool protocol; regex extraction is not accepted in formal
   mode.
7. Add a capability-controlled tool registry with reserved vaEVAS extension
   points. The concrete domain-tool inventory is not approved yet and requires
   a separate design discussion and per-tool ablation decision.
8. Use public validation feedback for all evolution and candidate selection.
   Run the model-invisible final test only after submission freeze.
9. If a final-test outcome is used for further generation or selection, that
   invocation must be reclassified as a verifier call and cannot remain the
   terminal score for the same episode.
10. Keep final scoring EVAS-backed and explicitly bound to EVAS 0.8.7. Do not
    imply Spectre equivalence.

## Target component model

```text
campaign / evaluation authority
    |
    +-- condition and budget manifest
    +-- clean-room factory
    +-- public-validation profile
    +-- model-invisible final-test profile
    +-- result and claim gate
    |
episode controller
    |
    +-- backend adapter
    |     +-- mini-swe
    |     +-- AlphaApollo reasoning
    |     +-- AlphaApollo evolution policy
    |
    +-- canonical JSON action / observation protocol
    +-- capability-controlled tool registry
    +-- attempt-owned state and candidate lineage
    +-- append-only trajectory recorder
    |
public environment
    |
    +-- sandboxed shell
    +-- current public EVAS capability
    +-- current submission transport
    +-- reserved domain-tool extension points
    |
submission freeze
    |
model-invisible EVAS 0.8.7 final test
    |
immutable score sidecar and claim-to-evidence join
```

## Coding-Agent Design References

The approved SWE-agent/mini-swe interface, OpenHands controller/runtime, Aider
editing/checkpoint and Codex CLI sandbox-policy transfer matrix is preserved in
the [design snapshot](archive/2026-08-30-harness-plan-snapshot.md#coding-agent-framework-transfer-matrix).
These are design references, not new runtime dependencies or blanket reuse
approval. Land each adopted pattern through the [feature ledger](../docs/alphaapollo-migration/01_功能迁移台账.md)
with source, exact code, tests, experimental impact and rejected assumptions.
Domain editing, waveform and retrieval tools still require their own gate.

## Functional Work Plan

### Phase 0 - Reconcile the paused prototype

Status: `completed`

The prototype was reconciled into the common contracts/controller/state/event
surface (AA-VAE-015). Do not restart the old untracked-prototype assignment.

### Phase 1 - Freeze canonical protocols and manifests

Status: `completed`

Action/observation, backend/tool/authority profiles, memory/lineage and evolution
manifest contracts are implemented (AA-VAE-016 through AA-VAE-022).
Contract/reducer tests do not constitute an operational evolution backend.

### Phase 2 - Build the common controller, state, and event core

Status: `implemented / deterministically verified` for the opt-in native paths.

Goal: one controller contract serves mini-swe and AlphaApollo without changing
the evaluator authority.

Responsibilities:

- controller owns the bounded propose -> act -> observe -> update loop;
- environment owns workspace, tools, candidate state, budgets, and done state;
- backend owns model requests and action production only;
- candidate store owns immutable snapshots and parent lineage;
- public validator owns model-visible executable feedback;
- scoring coordinator/final judge owns terminal replay after freeze;
- trajectory recorder owns ordered, append-only evidence.

Implemented: capability-aware dispatch, classified rejections, effect checks,
tool/public-validation budget accounting, semantic trajectory validation and
CI selection (AA-VAE-023 through AA-VAE-026). Deadline finalization and decoded
provider evidence have an opt-in launcher implementation (AA-VAE-037), not
complete campaign coverage. Detailed contracts remain in the migration notes.

Phase 2 closure update (AA-VAE-043–048): native model/private transport/tool
events, reported token accounting, runtime wall/disk limits, fresh-workspace
attempt discard and all-form scheduled ledgers are integrated. Token values
remain unknown when a provider does not report them; token telemetry does not
replace r53's wall-clock stopping rule. Captures are bounded decoded evidence,
not an unlimited wire archive. Candidate-only controller snapshots and the
sealed-round core and production Evolution joins are verified in AA-VAE-049.
This is neither in-place transactional rollback nor a hard-real-time
guarantee for arbitrary callbacks.

Required event types include:

- episode and attempt lifecycle;
- model request/response identity and token accounting;
- action proposed, parsed, rejected, or executed;
- tool observation with output/truncation hashes;
- candidate created, modified, forked, validated, selected, and frozen;
- public-validation invocation and feedback snapshot;
- budget update and terminal reason;
- final-test invocation and immutable sidecar join;
- retry, cleanup, and infrastructure incidents.

Tests first:

- deterministic state transitions;
- hard turn/token/wall/tool/EVAS/disk budgets;
- candidate hash changes only after declared mutating actions;
- retry receives a fresh attempt and workspace;
- cleanup cannot overwrite the primary outcome;
- trajectory validation detects deletion, reordering, or mutation.

### Phase 3 - Preserve mini-swe through a backend adapter

Status: `completed` (bounded compatibility slice)

The typed policy/environment bridge and opt-in single-cell launcher reuse the
existing model, Bash, submission and freeze surfaces (AA-VAE-027/037).
AA-VAE-038 compares deterministic legacy/native behavior and fixes rejected
proposals misclassified as infrastructure failures. This is not blanket parity:
legacy format recovery/multiple actions and native deadline handling differ.
Provider failure taxonomy remains coarse; keep these differences frozen before
any matched model comparison. Legacy campaign selection stays unchanged.

### Phase 4 - Reserve domain-tool extension points and run a design gate

Status: `completed` (reservation/design gate only)

AA-VAE-028 reserves five non-callable namespaces: candidate, public validation,
retrieval, submission and waveform. Every concrete tool family is deferred.
Before activation, record the addressed failure/cost, why Bash is insufficient,
public/licensed information source, state/authority effects, matched conditions,
budget and evidence contract, leakage audit, ablation, RED test and clean-room
acceptance. A reserved name does not promise its future API or implementation.

### Phase 5 - Implement public validation / final test separation

Status: `implemented / deterministically verified` within immutable r53 authority.

Goal: allow strong iterative feedback without converting the terminal judge
into an adaptive oracle.

Public-validation behavior:

- callable inside the episode under a frozen budget;
- uses EVAS 0.8.7 and only declared public fixtures/observables;
- may return sanitized compile, runtime, property, metric, log, and waveform
  diagnostics;
- binds every result to candidate hash and validation-profile hash;
- may enter the next-round memory snapshot.

Final-test behavior:

- callable only by the harness after submission freeze;
- uses the model-invisible final profile and checker;
- runs once for the selected terminal submission, subject only to explicit
  infrastructure retry policy;
- writes an immutable sidecar and never a model observation;
- cannot participate in candidate repair, ranking, selection, or later r53
  tasks.

r53 interpretation:

- Testbench tasks already provide strong separation: reference-DUT public
  validation versus evaluator-only certified faults.
- DUT and bugfix tasks currently provide a shared visible stimulus deck with a
  held-out checker. Report this as `shared_stimulus_heldout_checker`, not as a
  fully held-out stimulus/test set.
- A future disjoint DUT/bugfix stimulus profile would require a named successor
  protocol/release and is not part of this r53 plan.

Tests first:

- final checker paths and outputs are unavailable to the model container;
- final-test results are absent from policy and evolution memory;
- using a final result for another generation step invalidates terminal-score
  classification;
- candidate selection uses public-validation evidence only;
- final sidecar binds submission, judge, profile, checker, and result hashes.

Implemented bounded slices: public/final authority profiles, immutable sidecar
store, production final replay receipt, candidate-bound public simulation,
native result join, single-cell mini-swe launcher, behavior differential and
mixed-backend evidence bridge (AA-VAE-029 through AA-VAE-039). Real r53 Docker
smokes verify the composed path with deterministic providers; they are not model-quality or full-campaign
experiments. Legacy defaults and r53/EVAS bytes remain unchanged.

The current score contract labels EVAS replay `development_only`; formal
authority is not inferred from terminal position. DUT/bugfix public simulation
remains the existing Bash capability, not activation of a reserved domain tool.

AA-VAE-043–048 close Testbench reference-only support, all-form profile
distribution, infrastructure-only fresh attempts and native result ledgers.
Single-trajectory clean-room gates pass with deterministic providers. The
Evolution public-feedback/candidate-store composition and selected-only final
replay are now verified in AA-VAE-049. Never fabricate native evidence
from incomplete legacy traces or classify a connectivity smoke as a model
comparison.

### Phase 6 - Add the AlphaApollo single-trajectory reasoning backend

Status: `implemented / deterministically verified` (AA-VAE-046); real-model
matched comparison awaits named model/service and budget.

Goal: compare AlphaApollo-style reasoning with mini-swe under matched task
capability and budget.

Adapt from public AlphaApollo:

- agent/environment turn separation;
- tool-group registration pattern where useful;
- explicit short-term memory;
- local and OpenAI-compatible model adapters;
- structured trajectory collection.

Replace rather than copy:

- informal-math environment;
- XML answer/tool parsing;
- math ground truth and answer scoring;
- math Python/RAG corpus defaults;
- LLM verifier voting as score authority.

Matched comparison requirements:

- same task bytes and clean-room image;
- same model/provider/snapshot and decoding policy;
- same public prompt information;
- same effective Bash, candidate, EVAS, waveform, RAG, and submission
  capabilities;
- same turn, token, wall, tool, and EVAS budgets;
- same submission freeze and final-test judge.

Tests first:

- backend contract tests with deterministic fake models;
- local and API model adapter normalization tests;
- matched-capability manifest test against mini-swe;
- one-task clean-room reasoning smoke per task form.

### Phase 7 - Add round-based multi-model evolution

Status: `implemented / deterministically verified`; AA-VAE-047 supplies the
core and AA-VAE-049 supplies real provider CLI, production composition,
three-form Docker gate and separate terminal result index.

Goal: implement the first explicitly named AlphaApollo-Evolution+EVAS
condition without scheduling-dependent feedback exposure.

Reuse/adapt from public AlphaApollo with license/NOTICE preservation:

- branch configuration and result records;
- parallel branch execution and failure isolation;
- multi-round orchestration;
- shared solution/candidate memory concepts.

vaEVAS-specific evolution protocol:

1. Freeze model roster, branch IDs, rounds, budgets, validation profile, and
   selection rule before the first call.
2. At round `r`, every branch starts from the same immutable feedback snapshot.
3. Branches run independently and cannot read in-flight peer state.
4. Wait for all branches or apply a predefined timeout/failure policy.
5. Run public validation on eligible candidates.
6. Canonically sort candidates and feedback, then freeze the round snapshot.
7. Begin round `r+1` with the same snapshot visible to every surviving branch.
8. Select the final candidate using only declared public-validation metrics and
   a deterministic hash tie-break.
9. Freeze that candidate and run the model-invisible final test once.

Memory restrictions:

- memory scope is one task, cell, and episode;
- no cross-task, cross-model-cell, or cross-condition memory;
- candidate source and sanitized public diagnostics may be shared;
- model identity need not be exposed to peer models unless it is a named
  intervention;
- final-test outcome never enters the evolution snapshot.

Tests first:

- provider latency/order cannot change the round-`r+1` visible snapshot;
- candidate ordering and selection are stable under completion-order changes;
- failed/timeout branches follow the frozen policy;
- no mutable candidate directory is shared across branches;
- total budget equals the sum of recorded branch/tool/model budgets;
- final-test output cannot trigger another round.

### Phase 8 - Complete trajectory, evidence, and result generation

Status: `implemented / deterministically verified`; private capture/reviewer
export (AA-VAE-044), single-trajectory result/paired/claim ledger (AA-VAE-048)
and separate Evolution terminal index/all-branch costs (AA-VAE-049) are present.
Tables for actual model claims still require real experiments, not smoke rows.

Goal: make every model result derivable from raw trajectory through frozen
submission and final score.

Required joins:

- campaign -> cell -> episode -> attempt -> branch -> round;
- model request/response -> action -> tool result;
- action -> before/after candidate hashes;
- public validation -> candidate and validation profile;
- feedback snapshot -> member candidate/result hashes;
- selected candidate -> immutable submission freeze;
- final test -> submission, evaluator, checker, profile, and sidecar hashes;
- record-level ledger -> aggregate table/figure and claim index.

Export policy:

- retain raw sensitive traces in the private evidence store;
- generate public ledgers through a versioned normalizer;
- preserve event ordering and join keys after redaction;
- report tool use, revisions, and EVAS calls as process metrics, not correctness;
- classify model, candidate, protocol, infrastructure, timeout, and cleanup
  outcomes separately.

Tests first:

- every aggregate row resolves to an immutable terminal record;
- no row has a missing denominator or silent retry/replacement;
- redacted exports validate against the raw hash-bound index;
- score reports reject missing identity, missing structured verdict, hash drift,
  and judge/profile mismatch.

### Phase 9 - Define experimental conditions and ablations

Status: `bounded DeepSeek pilot stopped / no scored result`. Frozen design is
in `deepseek-budget-pilot.md`; execution audit is linked in Current Status above.
Conditions and runtime entrypoints remain distinct; no broader paid experiment
is authorized. Deferred domain tools are not required closure work.

Primary conditions:

- existing `One-shot`;
- existing `Agent-No-EVAS`;
- existing mini-swe `Agentic+EVAS`;
- new `AlphaApollo-Reasoning+EVAS`, matched to mini-swe;
- new `AlphaApollo-Evolution+EVAS`, separately budgeted and reported.

Required ablations after core parity:

- backend only: mini-swe versus AlphaApollo reasoning with matched tools/budget;
- evolution only: AlphaApollo single trajectory versus round-based evolution;
- Bash-only versus structured candidate/edit helpers;
- raw EVAS logs versus waveform/diagnostic helpers;
- no retrieval versus frozen documentation RAG;
- single-model versus multi-model evolution;
- deterministic round barrier versus asynchronous sharing only as a separately
  named exploratory condition.

Reporting rules:

- never merge pass@1, best-of-k, multi-branch, and oracle-guided estimands;
- report total model, token, wall, validation, tool, and branch costs;
- compare matched conditions only where capability and budget equality holds;
- report r53 Testbench held-out faults separately from DUT/bugfix
  shared-stimulus held-out-checker results;
- do not promote single-task smokes into model-quality claims.

### Phase 10 - CI, clean-room smoke, documentation, and merge gates

Status: `completed` for the approved AA-VAE-043–049 runtime scope. Focused tests,
final stable-tree harness gate and all triggered hosted gates passed. Exact
commit/run links and the compact-checkout/LSP limitations are recorded in the
verification log. This does not complete Phase 9 real-model experiments.

CI layers:

1. schema and canonicalization tests;
2. controller/state/trajectory unit tests;
3. backend contract tests;
4. tool security/capability tests;
5. validation/final-test leakage tests;
6. deterministic evolution tests with fake models and reordered completions;
7. mini-swe regression suite;
8. one-task-per-form clean-room smoke;
9. result/claim protocol suite;
10. Ruff, bytecode/type/static checks where configured, workflow parsing, and
    `git diff --check`.

Documentation updates:

- maintain `docs/alphaapollo-migration/` as the feature migration ledger;
- add one feature note per migrated capability with public source, idea,
  implementation files, deviations, tests, status, and license notice;
- add a coding-agent comparison note covering the exact SWE-agent/mini-swe,
  OpenHands, Aider, and Codex CLI patterns, landing files, tests, and rejected
  assumptions recorded in this plan;
- update `AGENTS.md` only after the implemented runtime and tests support the
  corresponding contract;
- update runner documentation and campaign examples without changing sealed
  r53 artifacts.

Merge gates:

- review architecture and duplicated abstractions before integration;
- independently review leakage, final-judge authority, schedule determinism,
  retry lineage, denominator handling, and claim scope;
- commit each independently reviewable feature slice after its focused tests;
  never bundle the full harness migration into one history entry and never
  commit the paused prototype as-is;
- keep local RED steps unpublished, publish only CI-safe GREEN commits, and
  push each completed slice only to the BucketSran fork after review passes.

## Suggested implementation slices

1. Protocol schemas and RED tests.
2. Common state/event/controller core.
3. mini-swe adapter and parity smoke.
4. Capability registry, non-callable extension points, and tool-design gate.
5. Public-validation/final-test split.
6. AlphaApollo reasoning backend.
7. Round-based multi-model evolution.
8. Any separately approved domain tool as its own feature and ablation slice;
   waveform and RAG remain deferred examples, not scheduled commitments.
9. Campaign conditions, ablations, evidence joins, and claim gates.
10. Final clean-room verification, independent review, and fork-only merge.

Each slice follows RED -> minimal implementation -> focused tests -> affected
v4 suite -> clean-room smoke when the formal path changes -> independent
review -> documentation/evidence update.

## Stop condition

This plan is complete only when:

1. mini-swe remains reproducible through the common harness;
2. AlphaApollo reasoning runs as a matched backend;
3. AlphaApollo evolution runs as a separately budgeted multi-model condition;
4. Bash and any separately approved domain tools use one capability policy;
   unapproved tools remain reserved, not mandatory implementation work;
5. all continued generation uses public-validation information only;
6. final-test results are terminal, model-invisible, and sidecar-bound;
7. round scheduling cannot change the declared shared feedback snapshot;
8. trajectories join every model/tool/candidate event to the frozen submission
   and EVAS 0.8.7 result;
9. r53 and EVAS 0.8.7 remain byte-for-byte unchanged;
10. CI, targeted tests, clean-room smokes, independent review, and claim gates
    are green with unresolved risks explicitly recorded.

## Open risks

- New backends must reuse the integrated controller/runtime boundaries rather
  than revive the reconciled prototype or duplicate the existing runner.
- Public validation diagnostics can overfit the visible profile; final claims
  must retain the held-out-checker/fixture distinction.
- Multi-model evolution changes compute budget and estimand even when the base
  model is unchanged.
- Local/API model endpoints may not expose identical token or sampling
  controls; unmatched metadata must be reported rather than silently ignored.
- RAG licensing, corpus contamination, embedding nondeterminism, and hidden
  benchmark overlap require explicit audit.
- Structured helper tools may improve results independently of the reasoning
  backend and therefore require separate ablations.
- Round barriers improve information-set reproducibility but do not eliminate
  model-sampling or provider nondeterminism.
