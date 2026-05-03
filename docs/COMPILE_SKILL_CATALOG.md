# Compile Skill Catalog

## Purpose

This catalog is the management layer above individual compile `SKILL.md` cards.
It answers four questions:

1. Which compile failures are covered today?
2. Where is each skill allowed to act?
3. How portable is the skill beyond the current benchmark?
4. Which residual compile failures need new skills instead of ad-hoc patches?

Compile skills are intentionally failure-class assets, not task-specific
patches. A skill should route from public diagnostics, such as
`spectre_strict:*` notes, compiler messages, or artifact-presence checks. It
must not route from `task_id`, gold code, checker internals, or hidden benchmark
identity.

## Layer Model

Compile skills can participate at several layers, but each layer has a different
risk profile.

| Layer | Example condition | What the skill does | Allowed feedback |
| --- | --- | --- | --- |
| Prompt-side repair | `C-SKILL` | Injects matched `SKILL.md` guidance into the LLM compile repair prompt. | Public prompt/spec, candidate files, public validator diagnostics, same-task repair history. |
| Local deterministic repair | `C-SKILLPLUS` | Applies safe mechanical fixers selected by public diagnostics. | Public diagnostics only; no behavior tuning. |
| Local accept/reject repair | `C-ULTRA(full)` | Applies one fixer at a time, plus optional batch fallback, then accepts only if quick EVAS compile-closure rank improves. | Public diagnostics plus executable strict-EVAS compile/score result. |
| Final audit | EVAS/Spectre targeted audit | Confirms pass/fail parity and failure-domain attribution. | Final candidate artifacts and backend outputs. |

The same skill card should be readable by both humans and LLMs. A deterministic
fixer is optional. Judge-only skills are still useful because they provide stable
failure attribution and route future prompt-side repair.

## Skill Taxonomy

| Taxonomy | Definition | Typical action | Circuit knowledge needed |
| --- | --- | --- | --- |
| Syntax legality | A generated construct is not accepted by Spectre syntax or strict preflight. | Small local rewrite. | Low. |
| Source and netlist legality | Spectre source or instance syntax is legalizable without changing behavior intent. | Local rewrite with strict boundaries. | Low to medium. |
| Interface materialization | Public harness nodes and generated Verilog-A ports disagree. | Local rewrite only for static, unambiguous structures. | Medium. |
| Artifact presence | A required generated file is missing. | Judge-only unless an LLM regenerates the artifact. | Medium. |
| Port-role boundary | A DUT-driven port is tied to a fixed source node. | Judge-only locally; prompt-side repair preferred. | Medium to high. |
| Wrong-function generation | Candidate implements the wrong module or public function. | Regeneration or LLM repair. | High. |
| Dynamic structure | Runtime-selected analog accessors such as `V(out[idx])`. | Dedicated structural skill required. | High. |

## Current Skill Inventory

| Skill | Taxonomy | Trigger | Fixer | Safe local autofix | Portability | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `conditional_transition_target_buffer` | Syntax legality | `spectre_strict:conditional_transition` | `transition_target_buffer` | Yes | Medium-high | Portable for ordinary `V(out)` targets. Not sufficient for dynamic `V(out[idx])`. |
| `parameter_default_range` | Syntax legality | `spectre_strict:parameter_default_range`, `spectre_strict:parameter_open_upper_range` | `parameter_default_range` | Yes | High | Removes only incompatible range clauses and preserves defaults. |
| `pwl_monotonic_time` | Source and netlist legality | `spectre_strict:nonincreasing_pwl_time` | `pwl_monotonic_time` | Yes | Medium-high | Assumes simple `wave=[time value ...]` sources. |
| `instance_parameter_keyword` | Source and netlist legality | `spectre_strict:instance_parameters_keyword` | `instance_parameter_keyword` | Yes | High | Removes unsupported instance `parameters` keyword while preserving assignments. |
| `vector_scalar_interface` | Interface materialization | `spectre_strict:dynamic_analog_vector_index`, `spectre_strict:instance_port_count_mismatch` | `vector_unroll` | Yes, when static | Medium | Good for fixed-index vector expansion. Not enough for scatter-index targets. |
| `module_name_linkage` | Interface materialization | `spectre_strict:undefined_module=` | `module_name` | Yes, with accept/reject | Medium | Only fixes unique name mismatches. Reject if the renamed body still has wrong ports/function. |
| `sourced_port_drive_boundary` | Port-role boundary | `spectre_strict:sourced_port_voltage_drive` | None | No | Medium | Judge-only until port role can be inferred safely. |
| `missing_testbench_artifact` | Artifact presence | `missing_generated_files=testbench.scs`, `spectre_strict:missing_staged_tb` | None | No | High for detection | Needs prompt-side regeneration or explicit provenance rules. |
| `sourced_port_role_repair` | Port-role boundary | `spectre_strict:sourced_port_voltage_drive` | `sourced_port_role_repair` | Yes, with accept/reject | Medium | Detaches a proven DUT-driven port from a source-fixed node using public instance/module signatures. |
| `missing_testbench_generation` | Artifact presence | `missing_generated_files=testbench.scs`, `spectre_strict:missing_staged_tb` | `missing_testbench_skeleton` | Yes, with accept/reject | Medium | Builds a minimal public-interface smoke harness; does not synthesize expected behavior. |
| `dynamic_scatter_index_materialization` | Dynamic structure | `spectre_strict:dynamic_analog_vector_index` | `dynamic_scatter_materialization` | Yes, with accept/reject | Medium | Materializes runtime `V(out[idx])` scatter writes into guarded scalar contributions. |
| `wrong_function_regeneration_gate` | Wrong-function generation | `spectre_strict:undefined_module`, rejected rename plus `instance_port_count_mismatch` | None | No | Medium-high for detection | Routes to prompt-side regeneration when name repair exposes a wrong public function body. |

## Why Skills Are Split

Skills are split by failure class so they can be routed, tested, accepted, and
rolled back independently. Combining everything into one large compile skill
would make the system harder to maintain:

| If combined into one mega-skill | Resulting risk |
| --- | --- |
| Many triggers point to one action bundle | Wrong repair can be applied to a partially related failure. |
| Multiple edits happen together without attribution | We cannot tell which rule helped or regressed. |
| One fix needs rollback | Safe fixes may be rolled back together with unsafe fixes. |
| A new benchmark has only one failure class | The entire mega-skill must be ported and reviewed. |
| A reviewer asks why a candidate changed | Manifest lacks a precise skill-level explanation. |

The registry is the central management point:

`runners/compile_skills/registry.json`

The individual cards are the maintainable unit:

`runners/compile_skills/<skill_id>/SKILL.md`

## Deterministic Fixer Policy

A compile skill may include a deterministic fixer only when all conditions hold:

1. The trigger comes from public diagnostics.
2. The rewrite has a narrow, syntax/interface legality purpose.
3. The rewrite does not tune gains, thresholds, timing constants, or state
   semantics.
4. The fixer can abstain when preconditions are ambiguous.
5. The edited candidate is revalidated by strict-EVAS.
6. Representative accepted edits are audited with Spectre.

If a fix needs circuit intent, testbench synthesis, or functional redesign, keep
it as prompt-side guidance or judge-only until a safe protocol exists.

## Advanced Skill Follow-Up

Three advanced compile skills were promoted from backlog into the registry:

1. `sourced_port_role_repair`
2. `missing_testbench_generation`
3. `dynamic_scatter_index_materialization`

Target: the 7 residual compile/interface failures from `C-ULTRA(full)`.

Strict-EVAS result for the advanced candidate:

| Candidate | Pass@1 | dut_compile | tb_compile | sim_correct | residual DUT compile | residual TB compile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C-ULTRA(full)` | 81/143 | 0.9925 | 0.9580 | 0.5234 | 1 | 6 |
| `C-ULTRA-ADVANCED` | 83/143 | 0.9925 | 1.0000 | 0.5312 | 1 | 0 |

Accepted advanced actions:

| Task | Accepted skill/action | Closure effect |
| --- | --- | --- |
| `balanced_analog_limiter_tb` | `sourced_port_role_repair` | `FAIL_TB_COMPILE -> FAIL_SIM_CORRECTNESS` |
| `completion92_testbench_e2e` | `sourced_port_role_repair` | `FAIL_TB_COMPILE -> PASS` |
| `original92_cppll_freq_step_reacquire_smoke` | `missing_testbench_generation` | `FAIL_TB_COMPILE -> FAIL_SIM_CORRECTNESS` |
| `original92_dwa_ptr_gen_no_overlap_smoke` | batch: `instance_parameter_keyword` + `dynamic_scatter_index_materialization` + `conditional_transition_target_buffer` | `FAIL_TB_COMPILE -> FAIL_SIM_CORRECTNESS` |
| `original92_dwa_ptr_gen_smoke` | `missing_testbench_generation` + bootstrap `conditional_transition_target_buffer` | `FAIL_TB_COMPILE -> FAIL_SIM_CORRECTNESS` |
| `original92_parameter_type_override_smoke` | `sourced_port_role_repair` | `FAIL_TB_COMPILE -> PASS` |

Spectre audit status: attempted three times on the 7-task advanced set, but the
bridge failed before simulation with SSH upload timeout:

`Failed to upload files: Connection timed out during banner exchange`

Therefore `C-ULTRA-ADVANCED` is currently an EVAS-validated candidate row, not
yet a Spectre-audited maintained row.

Artifacts:

- `generated-balanced-CULTRA-ADVANCED-skill-acceptreject-kimi-k2.5-2026-05-03`
- `results/balanced-CULTRA-ADVANCED-skill-acceptreject-kimi-k2.5-quick-2026-05-03`
- `results/balanced-CULTRA-ADVANCED-skill-acceptreject-kimi-k2.5-spectre-strict-evas-2026-05-03`
- `results/balanced-CULTRA-ADVANCED-skill-acceptreject-kimi-k2.5-both-advanced7-r3-2026-05-03`

## Current Residual Compile Failures

Current Spectre-audited maintained row: `C-ULTRA(full)` on
`benchmark-balanced`.

Result: `81/143`, with residual compile/interface failures `7/143`.

Current EVAS-only advanced row: `C-ULTRA-ADVANCED`, result `83/143`, with
residual compile/interface failures `1/143`.

| Task | Advanced status | Failure class | Current skill status | Why not solved locally |
| --- | --- | --- | --- | --- |
| `completion92_calibration_bugfix` | `FAIL_DUT_COMPILE` | Wrong-function generation | `module_name_linkage` attempted/rejected, then `wrong_function_regeneration_gate` routed | The generated body is not merely misnamed; rename exposes `IV2B:v2b_4b:nodes=6:ports=38`, so the missing `v2b_4b` converter must be regenerated rather than locally patched. |

Wrong-function gate proof:

| Artifact | Result |
| --- | --- |
| `generated-balanced-CULTRA-WRONGFUNC-GATE-kimi-k2.5-2026-05-03` | Candidate copied unchanged after rejecting unsafe rename. |
| `results/balanced-CULTRA-WRONGFUNC-GATE-kimi-k2.5-quick-2026-05-03` | Single-task quick EVAS: `FAIL_DUT_COMPILE`, with manifest action `wrong_function_regeneration_gate`. |
| Gate evidence | `undefined_module=v2b_4b;available_modules=dwa_ptr_gen_no_overlap`; after rename trial: `instance_port_count_mismatch:IV2B:v2b_4b:nodes=6:ports=38`. |

Prompt-side regeneration implementation:

| Artifact | Result |
| --- | --- |
| `runners/run_wrong_function_regeneration.py` | Builds a public-only regeneration prompt and asks the model to regenerate only the missing module. |
| `generated-balanced-WRONGFUNC-REGEN-kimi-k2.5-2026-05-04` | Single-task Kimi attempt for `completion92_calibration_bugfix`. |
| `results/balanced-WRONGFUNC-REGEN-kimi-k2.5-quick-2026-05-04` | Blocked before generation by expired Bailian token: `invalid access token or token expired`. |
| `generated-balanced-WRONGFUNC-REPLAY-historical-v2b-2026-05-04` | Offline replay mode using a historical model-generated `v2b_4b.va`; `api_call_count=0`, `call_mode=replay_va`. |
| `results/balanced-WRONGFUNC-REPLAY-historical-v2b-quick-2026-05-04` | Single-task strict-EVAS replay: DUT compile `1.0`, TB compile `1.0`, sim correctness `0.0`; compile closure validated, live Kimi regeneration not validated. |

Offline validation boundary:

- Replay mode validates the regeneration plumbing and whether replacing only
  the missing public module is sufficient to close the compile failure.
- Replay mode must not be reported as a live model result because it does not
  call the provider.
- Live model validation still requires a valid provider token, and Spectre audit
  still requires a healthy `virtuoso-bridge-lite` upload path.

## Backlog

The next compile-skill work should be added in this order.

| Priority | Proposed skill | Layer | Goal | Acceptance evidence |
| --- | --- | --- | --- | --- |
| P0 | Spectre audit retry for advanced skills | Final audit | Re-run the 7-task advanced set once `virtuoso-bridge-lite` SSH upload is healthy. | EVAS/Spectre pass mismatch `0/7` or explicit Spectre compile reasons. |
| P0 | `missing_testbench_generation` refinement | Prompt-side plus local accept/reject | Improve missing-TB cases where a smoke skeleton reveals deeper DUT legality problems. | `original92_dwa_ptr_gen_smoke` moves beyond TB compile without task-id templates. |
| P1 | `dynamic_scatter_index_materialization` hardening | Local accept/reject plus guidance | Generalize scatter materialization beyond the observed DWA shape. | Additional dynamic-vector cases compile-clean under EVAS and Spectre. |
| P1 | Prompt-side wrong-function regeneration | LLM repair | Regenerate the missing public module after `wrong_function_regeneration_gate` fires. | The replacement module compiles under EVAS/Spectre without using task-id templates or hidden gold code. |

## Promotion Checklist For New Skills

Before adding a new skill to the registry:

1. Add or update `runners/compile_skills/<skill_id>/SKILL.md`.
2. Define public triggers in `registry.json`.
3. Decide `fixer` vs judge-only.
4. Add a unit test for routing and, if applicable, the fixer.
5. Run the smallest targeted strict-EVAS validation.
6. If accepted edits affect benchmark results, run targeted EVAS+Spectre audit.
7. Update this catalog and `COMPILE_SKILL_PIPELINE.md`.

## Relationship To Mechanism Skills

Compile skills are not mechanism guidance. They do not teach the model what a
comparator, DWA, VCO, PLL, or sample-and-hold should do. They only make the
candidate legal enough for the evaluator to judge the behavior.

Mechanism knowledge belongs in the `G` or `I` family:

| Knowledge type | Correct layer |
| --- | --- |
| Spectre syntax legality | Compile skill. |
| Public testbench/interface legality | Compile skill or prompt-side compile repair. |
| Circuit operation principle | Mechanism guidance (`G`). |
| Structured behavioral representation | Functional/materialized IR (`I`). |
| Checker-specific behavior repair | Not allowed for compile closure. |
