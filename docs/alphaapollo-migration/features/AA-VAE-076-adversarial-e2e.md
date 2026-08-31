# AA-VAE-076 — Bounded adversarial end-to-end acceptance

Date: 2026-09-01. Scope: r53 native mini-swe, scripted provider, real Docker and
EVAS 0.8.7. This is distinct from AA-VAE-077 framework reporting/efficiency work.

## Idea and implementation

Unit checks for permissions, trajectory semantics and frozen evidence already
exist. The additional evidence connects them through the production lifecycle:
scripted model action -> sandbox Bash -> submission gate/freeze -> trusted EVAS
replay -> sidecar -> verified readback. Negative cases must reach the intended
boundary, not pass just because any unrelated compile error occurred.

`tests/test_agent_harness_adversarial_e2e.py` reuses the existing native launcher,
scripted Provider, r53 public-contract stubs, final replay and score reader. No
new security runtime, evaluator, custom scorer or model backend is introduced.

| Case | Intended evidence |
| --- | --- |
| Ordinary submitted candidate | A valid submission reaches actual final scoring and produces a readable bound sidecar, even if the neutral candidate is behaviorally wrong. |
| Private/sibling reads | Actual host-side sentinel files are not exposed in the sandbox or subsequent model observations. |
| Forged success feedback | Model-controlled success text/EVAS markers remain diagnostics; the independently replayed wrong candidate still scores zero. |
| Frozen submission tamper | Existing evidence readback rejects modified frozen bytes; reentry does not replace sidecar/outcome or invoke the model again. |
| Testbench output bypass | Directly driving DUT output is rejected by the intended security rule through the final scoring path. |

The CI workflow explicitly enables Docker for this file; ordinary offline
tests skip it. Reproduce from repo root after installing locked agentic
dependencies and building the pinned public images:

```sh
VABENCH_TEST_DOCKER_RUNTIME=1 uv run --locked --extra agentic python -m pytest -q \
  tests/test_agent_harness_adversarial_e2e.py
```

Fixtures own temporary directories under ignored `benchmark-vabench-release-v4/reports`
for Docker host sharing and remove their own temporary evidence on completion.
Only tests and compact verification records are committed, not generated judge
assets or trajectories. Exact outcomes are in `logs/verification-log.md`.

## Claim limits

- A behavior-failure control demonstrates an operating scoring path, not a
  passing model baseline. Scripted candidates do not measure model quality.
- This is bounded native-path adversarial acceptance, not an exhaustive red-team,
  proof against host compromise, or parity for every legacy/Reasoning/Evolution
  entrypoint. Hashes are integrity joins, not authenticated execution proofs.
- R53 DUT/bugfix retain shared visible stimuli and held-out checker authority.
  These tests do not create independent hidden stimuli or prove absence of
  semantic overfitting, checker blind spots or benchmark training contamination.
- Forged Bash telemetry may still affect explicitly untrusted process counters;
  those counters are not evidence of actual EVAS execution or correctness.
- No released benchmark bytes, EVAS semantics, score policy or Spectre gate change.
