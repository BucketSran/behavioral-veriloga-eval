# Shared agent harness

This package owns reusable native episode contracts and mechanisms. Concrete
Verilog-A runtime assembly lives in
[operations](../../benchmark-vabench-release-v4/operations/calibration_pilot/README.md#module-map).
It does not replace the default legacy mini-swe loop.

## Module map

| Responsibility | Owning modules |
| --- | --- |
| Interfaces and shared records | [contracts.py](contracts.py), [state.py](state.py); [__init__.py](__init__.py) exports selected public names |
| Single-episode lifecycle | [controller.py](controller.py), [budget.py](budget.py) |
| Action normalization and permission | [proposals.py](proposals.py), [tool_registry.py](tool_registry.py), [reserved_tools.py](reserved_tools.py) |
| Backend adaptation and identity | [backends/mini_swe.py](backends/mini_swe.py), [backends/reasoning.py](backends/reasoning.py), [backend_profile.py](backend_profile.py) |
| Public/final authority contracts | [authority_profiles.py](authority_profiles.py), [authority_adapters.py](authority_adapters.py) |
| Recorded events and safe exports | [trajectory.py](trajectory.py), [evidence_export.py](evidence_export.py) |
| Immutable terminal evidence | [result_artifact.py](result_artifact.py), [result_store.py](result_store.py) |
| Evolution coordination and lineage | [evolution_runtime.py](evolution_runtime.py), [evolution_state.py](evolution_state.py), [evolution_manifest.py](evolution_manifest.py) |
| Fresh-attempt recovery and batch resume | [attempt_sequence.py](attempt_sequence.py), [batch_resume.py](batch_resume.py) |
| Optional measurement | [phase_timing.py](phase_timing.py) |

## Tools: algorithm versus execution boundary

- [tools/offline_docs.py](tools/offline_docs.py) owns corpus validation and
  bounded retrieval; [offline_docs_tool.py](tools/offline_docs_tool.py) adapts
  it to a model-facing tool and observation.
- [tools/waveform_summary.py](tools/waveform_summary.py) owns bounded CSV
  reading and summaries; [public_waveform_tool.py](tools/public_waveform_tool.py)
  adapts trusted public execution receipts to model-facing observations.
- The concrete isolated EVAS waveform executor is
  [public_waveform.py](../../benchmark-vabench-release-v4/operations/calibration_pilot/public_waveform.py)
  in operations. Parsing bytes alone does not establish candidate provenance.

## Read one episode

Start with `contracts.py` and `state.py`, then `controller.py`. A policy proposes
an action; the controller resolves permission through the registry; an
environment executes with that capability; the recorder captures events with
explicit visibility. The terminal path freezes a submission and calls the
final judge, or captures a candidate for an Evolution branch. Those are distinct
contracts, not two labels for the same terminal operation.

Final judgments do not become policy observations or shared Evolution memory.
This boundary is enforced by code and concrete runtime isolation, not by this
README alone. For commands and current capability/evidence status, use the
[architecture guide](../../docs/ARCHITECTURE.md) and
[current plan](../../plans/current-plan.md).
