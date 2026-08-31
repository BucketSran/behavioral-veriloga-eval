# AA-VAE-078 — Opt-in execution phase timing

Date: 2026-09-01. This is execution observability, not score evidence.

## Idea and code map

Separate experiment infrastructure from agent reasoning. The earlier Inspect
adapter measures import only; measure actual execution at existing boundaries
before selecting a scheduler. No private reference implementation is imported.

- `runners/agent_harness/phase_timing.py`: standard-library context-local
  collector, synchronous decorators and spans, explicit cell/attempt identity.
- calibration `run_campaign.py`: native export boundary only.
- calibration `run_native_mini_swe.py`: preflight setup, recorded model/tool
  operations and startup-failure cleanup.
- generic `controller.py`: actual submission freeze and terminal cleanup.
- calibration `native_episode.py`: production final judgment, including its
  frozen-input verification and sidecar readback.
- `tests/test_agent_harness_phase_timing.py`: nested/thread isolation, original
  exception identity, no payloads and production native composition regression.

Use `with collect_phases(cell_id=..., attempt_id=...) as capture` around ONE
attempt, then `capture.to_document()` after exit. No collection is enabled by
default. The caller publishes the diagnostic report outside frozen run evidence;
no scorer, batch receipt, model message or retry contract is changed.

## Measurement boundaries

`model` includes decoded-request recording and any existing transport retries;
it is not pure remote inference latency. `tool` covers native dispatch including
local handling. `setup` currently means native sandbox preflight (absent for
OneShot), not every environment preparation operation. `export` is separate.
`ok` means the measured function returned; it does not mean the task passed.
Nested phase work is never summed as total elapsed time. Unknown/unobserved
phases remain absent, not zero. Captures are synchronous and worker-local;
thread workers must each open their own collector.

No raw command, prompt, model reply, exception message or judge payload is stored.
Measurements add some overhead when enabled and do not prove model quality or
throughput improvement. Legacy/Evolution execution profiling is not claimed by
the native boundary coverage. The next slice supplies a fixed workload CLI.
