# Native public waveform feedback — next bounded slice

Updated: 2026-08-31. Prerequisite: verified AA-VAE-060 executor.
Status: implementation-ready design; independent read-only review ACCEPT on
2026-08-31 after the incomplete-candidate/request-accounting repair. Runtime
integration has not started; register exact leaf ownership before opening writes.

## Goal and non-goals

Expose AA-VAE-060 through an explicit native Agentic opt-in, identically in
mini-swe and Reasoning, without changing arbitrary Bash or legacy defaults.
Reuse the common controller's `public_validation` budget class, typed observation
and frozen authority/result joins. No new evaluator, raw-path waveform reader,
campaign CLI, Evolution activation, real corpus, provider expense or training.

## Reviewed interface / boundaries

- A distinct zero-argument fixed public-simulation action (provider name
  `vaevas_public_simulate`) avoids overloading legacy `run_evas` command semantics.
  It dispatches to `IsolatedPublicWaveformExecutor`, not the marker-based
  `PublicEvasValidator` or the original generation container's shared outputs.
- Python API `public_waveform_max_calls: int | None = None`: `None` leaves the
  tool disabled; a positive non-boolean integer enables it and freezes the
  public-validation request limit before generation. A zero-argument schema
  rejects arbitrary commands and file paths. No-EVAS and OneShot reject
  activation before reserving runtime.
- Count each admitted call through existing `public_validation` capability
  accounting (tool_calls + public_validation_calls). Deny exhausted calls before
  pausing generation, snapshotting or Docker startup. Bind remaining model-call
  and episode wall budgets without introducing a hard-coded eight-call rule.
- An admitted request made before every declared candidate artifact exists is
  recoverable. After quiescing and safely checking the current candidate tree,
  return `rejection_kind="candidate_incomplete"`, `usable_feedback=false`,
  `evas_invocation_executed=false`, and `task_correctness="not_evaluated"` in a
  profile/candidate-bound public observation. Do not call AA-VAE-060, start an
  execution container, manufacture an invocation ID/receipt, or invalidate the
  executor. Resume the generator and let the model finish its files. Use the
  canonical current partial-tree hash, not a fabricated complete-submission hash.
- Only absent declared files are recoverable here. Unsafe paths, symlinks,
  nonregular/oversized/extra files, private references, identity drift, or
  terminal-state conflicts fail closed. Validate unsafe entries before classifying
  incompleteness. Do not add a precompiler: syntactically invalid but complete
  candidates reach EVAS and return its actual failed-process receipt.
- `public_validation_calls` counts admitted feedback requests, including the
  recoverable incomplete case. Separate telemetry
  `public_waveform_evas_invocations_executed` counts actual fixed simulation
  launches only (including launched failures/timeouts, not preflight probes).
  It is not a second budget and never counts marker-reported Bash operations.
  Neither counter is a global cap on all EVAS processes: unchanged ordinary Bash
  may still invoke EVAS outside this fixed-action path. Report that scope rather
  than claiming all simulator usage is authoritatively metered.
- Controller serialization alone does not stop background Bash children. The
  generation Docker container must be paused while its candidate is snapshotted
  and verified; always attempt resume, preserve resume/cleanup incidents, and
  fail closed on unavailable isolation. Do not merely assert exclusive access
  to a workspace that model Bash can still modify in the background.
- Configure the isolated executor's profile before generation. Its policy applies
  to this trusted action only; ordinary Bash EVAS markers remain unauthenticated.
  Before config hashing, `manifest.extensions.public_waveform` declares exactly
  `intervention="isolated-public-waveform-v1"`, `tool_name`, and
  `max_public_validation_calls`; the normal source map binds implementation
  hashes. After config hashing, bind the executor profile through the existing
  `public_validation_profile` request field and manifest
  `public_validation_profile_sha256`. Do not embed that full profile or its hash
  inside the config-hashed extension: its `campaign_config_sha256` would cycle.
  Default Agentic profile behavior remains unchanged when the extension is absent.
- `_RecordedEnvironment` records the fixed action and public receipt, converts
  it to the common Observation, and carries candidate/profile/payload identities.
  Unusable receipts or infrastructure failures never become successful feedback.
- `score_campaign.read_native_cell` reconstructs the exact new capability and
  checks declared receipt/profile/candidate/input hashes. Unknown or missing
  extension declarations reject; ordinary aggregate/ledger still refuses new
  intervention rows until a matched comparison protocol is frozen.
  An incomplete observation has no execution receipt or waveform payload; the
  reader rejects contradictory execution claims and rebuilds admitted-request
  and actual-execution totals from the trusted action/outcome events.

## Test-first acceptance

1. Explicit permission/closed arguments; disabled conditions and legacy unchanged.
2. A request before `model.va` exists consumes one request budget, launches no
   executor Docker container, returns the bound incomplete observation, and
   allows model reentry. With limit 1 the second request rejects before pause or
   Docker. A missing-file tree that also contains a symlink fails closed.
3. Background generation cannot race source snapshots; pause/resume failures are
   infrastructure incidents, not fabricated model mistakes or usable receipts.
4. Both native backends and Reasoning JSON/native-tool formats see the same bound
   public feedback on the next request; no final sidecar enters observations.
5. Trace/manifest/profile/receipt/source hashes join; undeclared or tampered
   capabilities reject at read-only scoring; no second final evaluation.
   Contradictory no-execution receipts/counters reject. A complete syntax-invalid
   candidate records an actual failed invocation, not `candidate_incomplete`.
6. Free scripted-provider real Docker smoke reaches submission freeze and one
   EVAS final score, separately from the public simulation. Invalid/failed public
   simulation remains diagnostic, not a correctness label.

## Ownership and publication

Main owns the calibration-pilot `run_native_mini_swe.py`, `score_campaign.py`
and `public_waveform.py`; `runners/agent_harness/tools/` descriptor/bridge leaves;
the directly corresponding `tests/test_agent_harness_*` regressions; CI, plans,
logs and migration docs. Reuse existing controller/budget APIs; changes to their
shared contracts require an explicit reviewed plan amendment rather than a
second controller or budget loop. Register exact new leaf paths before opening
writes or delegating; independent design/code reviewers remain read-only.
Review pause/resume and profile/budget contracts first, then vertical TDD and
separate GREEN commits. Completion of AA-VAE-060 does not itself claim this next
integration has been implemented.
