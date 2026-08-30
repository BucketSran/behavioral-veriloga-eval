# AA-VAE-046 — Runnable Reasoning backend

Status: production opt-in integrated; deterministic provider and real Docker
verification, not a paid-model experiment or performance claim.

## Reference and adaptation

AlphaApollo public commit `712a04dcdefb0eabdb6622350460f187e9bb5941`,
`workflows/api.py` and `core/environments/env_manager.py`: separate model-facing
reasoning from environment-owned execution/state. Apache-2.0 public reference;
this implementation is an architectural adaptation, not copied math/XML code.

## Implementation

- `runners/agent_harness/backends/reasoning.py`: episode-local message history,
  one candidate-bound normalized action, unique provider call IDs, native tool
  calls or standalone strict JSON, deadline-clamped provider request, measured
  usage without invented token totals. No training, implicit repair or judge.
- `operations/calibration_pilot/run_native_mini_swe.py` (under v4): shared
  launcher chooses ReasoningPolicy for the two Bash conditions, retains the
  shared output-only OneShot control, and reuses environment/controller/freeze/
  final authority/private capture/reviewer export. It records a distinct backend
  profile and policy source hash, not a renamed mini-swe policy.
- The v4 wrapper, campaign runner and score reader accept
  `--episode-backend native-reasoning`; proposal format is frozen by
  `--reasoning-proposal-format native_tool_calls|strict_json` (native default).
  Score reading independently joins actual backend, proposal format and model
  to frozen campaign configuration. AA-VAE-045 recovery applies without a
  second retry implementation.

## Run and inspect

Use the existing three-arm campaign wrapper with `--episode-backend
native-reasoning`. The score command uses the same backend flag. Keep separate
campaign roots for mini-swe and Reasoning; do not silently pool their conditions.
The endpoint can be API-hosted or local if it implements the existing compatible
chat transport. This is a harness policy, not a special class of model.

Native OneShot deliberately shares the one-output transport across backends;
strict JSON selection changes the Reasoning Bash policy, not the OneShot artifact
submission tool contract. No domain/RAG tool or SFT/RL dependency is activated.

Tests: `test_agent_harness_reasoning_backend.py`,
`test_agent_harness_reasoning_integration.py`, native campaign/conditions/
differential tests and the nine-cell Docker gate. The scripted candidates are
not reference solutions; expected behavior failures demonstrate joined evidence
and condition isolation, not Reasoning superiority or baseline reproduction.

## Boundaries

Legacy remains default. The old `--agent-scaffold native` retains its sensitivity
meaning. r53 and EVAS 0.8.7 are unchanged. No paid calls or Spectre were run.
Round-based Evolution and formal result claims have separate acceptance gates.
