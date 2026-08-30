# Native DUT/bugfix three-arm campaign

Date: 2026-08-30. Base: `24f2b834b012271af8d05221cc6e4855e2488f72`.
Status: implementation authorized after the human scope discussion.

## Brief

Layer: behavioral-veriloga-eval. Extend the opt-in native path to the existing
OneShot, Agent-No-EVAS and Agentic conditions for DUT/bugfix, then reuse the
existing campaign executor and scorer for a small, fully accounted campaign.
This is execution/evidence hardening, not a model-quality experiment.

Non-goals: native Testbench, automatic episode retry/recovery, Reasoning,
Evolution, new domain tools, raw transport archival, paper plots, paid model
runs, r53 changes, EVAS changes and routine Spectre execution. Legacy defaults
and the old `--agent-scaffold native` sensitivity path retain their meanings.

## KPI and acceptance

- Both supported forms can execute all three named conditions through native
  evidence, freeze and EVAS 0.8.7 final sidecars.
- OneShot makes one logical generation request with output-only submission
  transport; no Bash loop, executable feedback or format-repair reprompt.
- No-EVAS retains the multi-turn Bash agent but uses the paired no-EVAS image,
  no public EVAS profile, no public runtime manifest and no network access.
- Absence of public authority is explicit and hash-bound to condition/runtime;
  old profile-present artifacts remain valid. Final authority is still required.
- The existing campaign manifest/executor is reused via a distinct opt-in.
  Unsupported combinations fail before model execution; there is no silent
  legacy fallback. Each cell has an exclusive attempt workspace.
- Every scheduled cell has exactly one accounted terminal disposition.
  Protocol, timeout and infrastructure failures remain explicit and unscored;
  infrastructure failures are neither omitted nor converted to model zeroes.
  Missing/corrupt/duplicate identities block reports. Scoring never reruns a
  native final judge or manufactures a legacy generation record.
- Targeted tests, applicable legacy regression and deterministic clean-room
  Docker/EVAS evidence pass. No model-quality or full-r53-coverage claim follows.

Guardrails: fixed r53 bytes and EVAS 0.8.7; canonical 1,800-second wall policy;
final outcomes never enter model observations or memory; no in-place resume or
score-driven retry; fork-only publication and no old-worktree changes.

## Controlled implementation plan

1. Commit this scope and ownership checkpoint without runtime changes.
2. RED/GREEN explicit absent-public-authority contract and compatible result
   joins. Keep the final profile mandatory; reject contradictory evidence.
3. RED/GREEN native No-EVAS and one-request OneShot using existing model,
   workspace, submission and final replay machinery. Keep each condition's
   declared capabilities and protocol differences visible.
4. RED/GREEN native opt-in dispatch in existing campaign entrypoints, immutable
   cell terminal receipts and read-only scoring with planned denominator checks.
5. Exercise both forms and all arms with deterministic providers and real
   Docker/EVAS; inject provider/protocol/setup failures and broken joins.
6. Independent read-only review, focused static/regression checks, migration
   notes, and small GREEN-only commits/pushes to BucketSran origin/main.

## Risks and stop conditions

- Optional authority must not weaken enabled-feedback validation. Use negative
  tests for missing profiles, unexpected public observations and hash drift.
- Bash capability labels are not a syscall sandbox; prove no-EVAS with the
  existing image, network and mount boundaries, not command-string filtering.
- Reuse may collide with historical sensitivity flags or resume semantics;
  reject those combinations explicitly for the new native opt-in.
- A process death may leave an incomplete reserved attempt. Preserve evidence
  and block affected reporting; do not infer a terminal score or resume it.
- Stop affected writes on concurrent ownership/base drift, sealed release or
  evaluator changes, or any required new experimental authority.

## Evidence and review record

Commands, output locations, RED/GREEN counts, failures and review dispositions
are recorded in `logs/verification-log.md`; decisions in `logs/decision-log.md`.
Feature notes map each change to code, source idea and claim boundary. Final
review reports KPI status and unverified paths, keeping deterministic pipeline
evidence separate from real-model performance.
