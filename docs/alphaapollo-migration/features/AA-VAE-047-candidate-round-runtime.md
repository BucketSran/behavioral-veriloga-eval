# AA-VAE-047 — Candidate-only episodes and sealed parallel rounds

Status: reviewed reusable runtime; production Evolution composition is now
implemented and separately verified in AA-VAE-049. These unit tests alone do
not establish runnable Evolution.

## Public idea and deviations

AlphaApollo public `712a04dcdefb0eabdb6622350460f187e9bb5941`,
`core/generation/evolving/utils/agent.py`, `evolving_multi_models.py`, and
`core/environments/memory/memory.py` motivate independent branches and shared
feedback. Apache-2.0 reference, architectural adaptation without copied code.
vaEVAS adds strict round barriers, immutable public-only memory, bounded total
costs, deterministic selection and a separate final authority. It does not
adopt completion-order-dependent sharing, voting, math verification or training.

## Code

- `runners/agent_harness/{contracts,state,controller,trajectory}.py`: a
  candidate-only terminal handler reuses the existing controller. It captures
  `CandidateSnapshot` and returns `CandidateEpisodeResult`, never calls final
  `freeze_submission` or a fake final judge, and cannot contain scores.
  Candidate and final validators stay separate; candidate trajectories reject
  every trusted-visibility event, including unknown event types.
- `runners/agent_harness/evolution_runtime.py`: actual thread-pool branch
  execution, preallocated budgets, common previous-round snapshot, stable
  reducer inputs, candidate ancestry, write-once requests/receipts/memory and
  selection. Final judging is absent from branch callbacks.
- Failed usage is unknown, not zero; typed partial evidence survives failure
  and overrun. Total-budget accounting reserves unknown consumption.
  Branch identifiers are safe single path segments with confinement checks.

## Verification and limits

Tests: candidate_episode, controller, trajectory, evolution_runtime and
evolution_manifest suites. Independent reviews repaired unknown trusted-event
acceptance, unsafe branch paths and failed-cost zeroing. Shared final-episode
behavior remains covered by existing tests.

Deadlines are cooperative: callbacks must honor provider/tool watchdogs. The
coordinator waits for cleanup, discards an unsealed late round and uses the last
sealed incumbent; it does not claim to kill arbitrary Python threads. Production
must provide actual candidate generation/public validation and freeze/judge only
the selected final candidate. No model-quality result is asserted here.
