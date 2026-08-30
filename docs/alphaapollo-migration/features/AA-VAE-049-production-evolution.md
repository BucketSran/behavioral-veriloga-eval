# AA-VAE-049 — Separate multi-model Evolution runtime

Status: runtime-integrated, with deterministic providers through real Docker /
EVAS for DUT, bugfix and Testbench. Model-quality experiments are not claimed.

## Reference and adaptation

Public AlphaApollo commit `712a04dcdefb0eabdb6622350460f187e9bb5941`
(Apache-2.0), especially `evolving_multi_models.py`, `core/generation/evolving/`,
`core/environments/informal_math_evolving/` and `memory/memory.py`, motivates
parallel model branches, explicit candidate memory and iterative public feedback.
This is an architectural adaptation; no third-party implementation was copied.

vaEVAS retains its controller, JSON/native-tool protocol, isolated Bash,
r53 authority profiles and immutable replay sidecars. It does not import math
answer extraction, XML/regex tools, verifier voting, SFT/RL, cross-task solution
memory or completion-order-dependent sharing.

## Code map

- `runners/agent_harness/evolution_runtime.py` (AA-VAE-047): concurrent callbacks,
  immutable previous-round snapshots, deterministic reducer and candidate ancestry.
- `benchmark-vabench-release-v4/operations/calibration_pilot/run_native_evolution.py`:
  composes `ReasoningPolicy`, existing controller and recorded Bash/model adapters;
  bootstraps profiles; saves candidates; validates publicly; freezes/scores only
  the selected candidate. No duplicate model transport or controller is introduced.
- `run_evolution_campaign.py` in the same directory: real OpenAI-compatible
  API/local factories, frozen roster and separate `AlphaApollo-Evolution+EVAS`
  cell. Dry-run makes no provider/EVAS calls and reads no credentials.
- `tests/test_agent_harness_native_evolution.py`,
  `test_agent_harness_evolution_candidate_store.py`,
  `test_agent_harness_evolution_campaign.py` and the evaluator-closure workflow:
  contract, failure, snapshot and real three-form gates.

The calibration README documents roster/dry-run commands. Single-trajectory
`--episode-backend native-reasoning` remains a different condition.

## Frozen execution and information boundaries

1. Freeze task/campaign source, code hashes, model identities, structured
  protocol, rounds, per-branch/total budgets and both profiles before generation.
  Each branch creates one fresh client/workspace; its preflight-resolved Docker
  image ID is recorded before the model client is created.
2. Generation uses the pinned no-EVAS image. The coordinator invokes the fixed
   profile-bound public validator once for each eligible branch candidate,
   within its allowance. This information schedule differs from ordinary
   Agentic direct-EVAS Bash and must be reported as a separate condition.
3. Stop sandbox writers, verify/copy the declared tree and verify its bytes
   again. These are candidate snapshots, not final submissions. Cleanup failure
   discards the branch; public install/validation errors invalidate that authority.
4. Next-round branches receive identical sealed IDs, hash-verified code and
   public Observation feedback. Lookup uses branch/round identity, not global
   hash search. Feedback bytes bind to the sealed event, profile and candidate.
   No in-flight peer outputs or final results are shared.
5. Select using public simulation success and the existing deterministic tie
   rule. This is a process signal, not hidden behavioral correctness. Only the
   selected candidate is frozen and scored in the separate final runtime.

## Evidence and failures

`request.json`, profile documents and `evolution/` bind campaign, rounds,
lineage and candidate/feedback hashes. Branches have canonical candidate
trajectories and redacted private event chains. Reviewer-only `branch-audit.json`
links completed files after cleanup and retains provider/tool meters. The CLI
removes named API keys from process environment before sandbox launch; frozen
campaign JSON contains only endpoint hashes and environment-variable names.

`final-result.json` preserves one scheduled cell and every planned branch,
including not-started, failed and incomplete branches. It joins final sidecar,
source hashes and all-branch costs. Unknown token/transport usage stays null
with known subtotals/unknown counts; actual overruns are never clamped down to
allowance. Setup, no-candidate, public cleanup and final executor failures leave
immutable records instead of dropping rows. Final outcomes never trigger repair.

This index is separate from the single-trajectory ledger: budgets/estimands
must not be pooled. It forbids automatic model-quality claims and memory reuse.
Capture is bounded decoded evidence, not exact unlimited wire capture. Global
deadlines rely on cooperative bounded callbacks, not hard-real-time thread
termination. Abrupt host/process loss may leave incomplete evidence, which is
preserved rather than silently resumed or scored as success.

## Verification and claim boundary

RED tests exposed redundant client initialization, frozen tuple memory ignored,
unbound feedback bytes, dropped failure records, clamped overrun counts,
candidate cleanup acceptance and missing bootstrap cleanup. These were repaired
before publication. Independent boundary and result/cost reviews found no
remaining scoped blocker.

Real smoke uses incomplete public candidates, two scripted model identities and
two rounds per form. It checks public validation, next-round code sharing, four
branch records and one final submission/sidecar. Exact commands, hashes and
hosted results are in `logs/verification-log.md`. Paid model pilots, full-r53
scores, causal benefit, backend superiority and Spectre equivalence need
separate evidence; none follows from these deterministic connectivity tests.
