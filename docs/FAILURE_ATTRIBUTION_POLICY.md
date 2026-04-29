# Failure Attribution Policy

Date: 2026-04-27

The repair loop must classify a failed run before asking the LLM to repair
behavior. Otherwise a checker/runtime/scoring issue can be misreported as a
circuit bug and push the LLM toward the wrong edit.

## First Split

| Domain | Meaning | Typical next action |
|---|---|---|
| `functional` | The DUT/TB compiled, EVAS produced a waveform, and the checker returned a trustworthy behavior mismatch. | Repair the circuit behavior or generated behavioral testbench logic. |
| `validation` | A trustworthy behavior verdict was blocked by compile, interface, simulator, file, timeout, checker, or scoring issues. | Fix candidate syntax/interface, harness, checker, runtime, or scoring pipeline before behavior repair. |
| `pass` | All required score axes pass. | No repair. |

This is a routing label, not a scoring change. A task can still have the same
`status` and `scores`; the attribution only decides where the next repair
attempt should be aimed.

## Validation Subtypes

| Subtype | Examples | Repair owner |
|---|---|---|
| `candidate_compile` | Verilog-A syntax/preflight failure, `dut_not_compiled` | `llm_candidate_syntax` |
| `interface_or_harness` | missing include, undefined module, TB compile failure | `candidate_or_harness_interface` |
| `missing_waveform` | `tran.csv missing` | `verification_pipeline_or_harness` |
| `simulator_runtime` | `evas_timeout`, simulator `TimeoutExpired` | `ambiguous_runtime` |
| `checker_runtime` | `behavior_eval_timeout` | `verification_pipeline` |
| `file_artifact` | missing generated DUT/testbench | `generation_or_materialization` |
| `scoring_schema` | `PASS` status but required axes disagree | `verification_pipeline` |
| `infrastructure` | generic `FAIL_INFRA` | `verification_pipeline` |

## Implemented Hooks

- `runners/failure_attribution.py` contains the classifier.
- `runners/score.py` attaches `failure_attribution`, `failure_domain`, and
  `repair_owner` to each `result.json`.
- `runners/behavior_contract_triage.py` reports failure-domain and repair-owner
  counts even for old result directories that do not yet contain the fields.

## Repair Rule

The repair prompt should only request behavior changes when
`failure_domain=functional`.

If `failure_domain=validation`, the loop should first route by `repair_owner`:

- `llm_candidate_syntax`: ask the LLM for syntax/compatibility repair only.
- `candidate_or_harness_interface`: repair ports, includes, save policy, or TB
  linkage before touching behavior.
- `verification_pipeline`: inspect checker/scoring/runtime code.
- `ambiguous_runtime`: inspect waveform size, maxstep, simulation stop time,
  and checker streaming options before deciding whether behavior is wrong.
