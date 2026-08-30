# AA-VAE-045 — Native fresh-attempt recovery

Status: integrated; local verification and independent review recorded in the
verification log. This is recovery infrastructure, not a model-quality result.

## Idea and public reference

AlphaApollo separates trajectory state and environment failure from candidate
quality. Public reference: commit `712a04dcdefb0eabdb6622350460f187e9bb5941`,
`core/environments/env_manager.py`. This is an architectural adaptation, not
copied code; AlphaApollo is Apache-2.0. vaEVAS additionally owns immutable retry
policy, attempt identity, final authority and scheduled-result denominators.

## Code and behavior

- `runners/agent_harness/attempt_sequence.py`: frozen policy, fresh attempt
  contexts, hash-linked receipts and immutable terminal selection.
- `benchmark-vabench-release-v4/operations/calibration_pilot/run_native_attempts.py`:
  production adapter, confined runtime/source/lineage joins, conservative retry
  classification and all-attempt costs.
- The existing campaign runner, native launcher, v4 wrapper and score reader
  compose the adapter. `--native-max-attempts` defaults to 1; opt-in retry policy
  is frozen in the campaign and cannot change at execution or score time.
- Only typed provider transport or sandbox-startup infrastructure failure before
  freeze/final/deadline is retryable. Protocol, candidate, cleanup, agent-deadline
  and final-score failures do not trigger fresh generation. Cancellation and
  process exit propagate rather than become normal scored cells.
- Every retry exports a fresh workspace, instantiates a fresh client and records
  parent/retry lineage. No resume, overwritten evidence or feedback inheritance.
- Score reading verifies all attempts and selects one terminal row per scheduled
  cell without invoking a judge. Failed-attempt costs remain in totals; unknown
  usage stays null with known subtotals. Detailed evaluator outcomes remain
  explicitly selected-attempt scope.
- Transport capture uses an explicit client capability rather than Python class
  identity, so CLI `__main__` loading does not silently lose private capture.

## Tests and limitations

Unit/integration tests: `test_agent_harness_attempt_sequence.py`,
`test_agent_harness_native_attempts.py`,
`test_agent_harness_attempt_integration.py`, native dispatch/capture tests.
The nine-cell Docker smoke now covers both no retry and first-attempt transport
outage followed by fresh successful pipeline completion. Its incomplete public
fixtures yield structured behavior failures; it proves connectivity, not quality.

No automatic post-final repair, interrupted-attempt resumption, EVAS/r53 change,
legacy default change, Spectre or paid model experiment is introduced.
