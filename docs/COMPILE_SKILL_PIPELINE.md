# Compile Skill Pipeline

## Goal

Compile skills turn Spectre-strict compile knowledge into reusable project
assets.  A skill is not only prompt text.  It has a stable id, triggers,
human/LLM guidance, judge semantics, and optionally a deterministic fixer.

This lets the same knowledge participate in two places:

1. LLM repair loop guidance (`C-SKILL` style ablations).
2. Post-generation judge/fixer passes (`C-PLUS` / `C-SKILLPLUS` style
   ablations).

## Skill Shape

Current compile skills live under:

`runners/compile_skills/`

The management catalog is:

`docs/COMPILE_SKILL_CATALOG.md`

Each skill has:

| Field | Purpose |
| --- | --- |
| `id` | Stable name used in manifests and prompts. |
| `version` | Incremented when the rule semantics change. |
| `triggers` | Public EVAS/Spectre-strict notes that route this skill. |
| `SKILL.md` | Human/LLM-readable repair guidance. |
| `judge` | The validation surface that checks the rule. |
| `fixer` | Optional deterministic action. `null` means judge-only. |
| `safe_autofix` | Whether local repair is allowed without LLM synthesis. |

The registry is:

`runners/compile_skills/registry.json`

## Current Skills

For taxonomy, portability, layer placement, and residual-failure mapping, see
`docs/COMPILE_SKILL_CATALOG.md`.

| Skill | Action |
| --- | --- |
| `conditional_transition_target_buffer` | Fixer: rewrite branch-local `transition()` contributions into target-buffer form. |
| `module_name_linkage` | Fixer: align unique missing module name with unique generated module declaration. |
| `parameter_default_range` | Fixer: remove incompatible Spectre parameter range clause while preserving default value. |
| `pwl_monotonic_time` | Fixer: make PWL time tokens strictly increasing. |
| `instance_parameter_keyword` | Fixer: remove unsupported Spectre instance `parameters` keyword. |
| `vector_scalar_interface` | Fixer: delegate scalar/vector materialization to `compile_vector_unroll_guard.py`. |
| `sourced_port_drive_boundary` | Judge-only: flag DUT-driven ports tied to source-fixed nodes. |
| `missing_testbench_artifact` | Judge-only: flag missing required Spectre testbench artifact. |
| `sourced_port_role_repair` | Fixer: detach a proven DUT-driven port from a source-fixed node under accept/reject validation. |
| `missing_testbench_generation` | Fixer: materialize a minimal public-interface smoke harness when the generated testbench is missing. |
| `dynamic_scatter_index_materialization` | Fixer: turn runtime electrical-vector scatter targets into guarded scalar contributions. |
| `wrong_function_regeneration_gate` | Judge/gate: classify rejected module-name repairs that expose wrong-function bodies and route them to prompt-side regeneration. |

## Execution Flow

### Prompt-side skill guidance

`run_adaptive_repair.py --compile-skill-guidance` routes current validator notes
through the skill registry and injects matched `SKILL.md` guidance into
compile-only LLM repair prompts.

This is intended for future `C-SKILL` experiments.

### Post-generation judge/fixer

`materialize_cplus_candidates.py` copies an existing generated root, selects
compile/interface failures from a prior strict-EVAS summary, routes notes
through the skill registry, applies safe fixer actions, and writes an auditable
manifest.

`materialize_cultra_candidates.py` adds rollback discipline. It applies one
safe skill fixer at a time, validates with a quick spectre-strict EVAS score,
and accepts the edit only when the compile-closure rank improves. With
`--batch-fallback`, it also tries one transaction candidate containing all
currently routed safe fixers when individual actions do not improve rank. That
full ULTRA mode is the one that can cover coupled PLUS fixes.

The manifest records:

- selected skill ids and versions
- judge/fixer action
- source EVAS/Spectre-strict notes
- deterministic edits

## Safety Rules

1. Skills must route from public diagnostics, not task identity.
2. Fixers must abstain when preconditions are ambiguous.
3. Behavior constants, thresholds, gains, and state semantics should not be
   tuned by compile skills.
4. Every edited candidate must be revalidated by spectre-strict EVAS.
5. Representative skillized candidates should be audited with real Spectre.

## Current Experiment

The first compile-skill series is summarized in:

`results/adfgi-ablation-compile-skill-series-2026-05-03.md`

Full strict-EVAS results:

| Condition | Result |
| --- | ---: |
| `C` | `75/143` |
| `C-SKILL` | `78/143` |
| `C-SKILLPLUS` | `80/143` |
| `C-ULTRA` per-action only | `79/143` |
| `C-ULTRA(full)` with batch fallback | `81/143` |
| `C-ULTRA-ADVANCED` with three advanced skills | `83/143` EVAS-only pending Spectre audit retry |

Targeted EVAS+Spectre audits:

| Candidate | Targeted set | EVAS | Spectre | Pass mismatch |
| --- | --- | ---: | ---: | ---: |
| `C-SKILL` | 35 D residual compile/interface failures | `11/35` | `11/35` | `0/35` |
| `C-SKILLPLUS` | 17 C residual compile/interface failures | `5/17` | `5/17` | `0/17` |
| `C-ULTRA` | 17 C residual compile/interface failures | `4/17` | `4/17` | `0/17` |
| `C-ULTRA(full)` | 18 C residual compile/interface failures after parity fixes | `6/18` | `6/18` | `0/18` |

`C-SKILLPLUS` verifies that the skillized execution path preserves the earlier
hard-guard improvement while making the mechanism reusable and auditable.
`C-ULTRA` adds rollback discipline through per-action EVAS quick accept/reject.
The full `C-ULTRA` mode adds transaction fallback and now covers the PLUS gains:
it has no pass loss relative to the current PLUS artifact and additionally
closes `original92_pipeline_stage`.
The original `C-SKILL` audit exposed two EVAS/Spectre mismatches; these are now
closed by string-parameter propagation in EVAS and an open-upper-range strict
preflight skill.

`C-ULTRA-ADVANCED` adds `sourced_port_role_repair`,
`missing_testbench_generation`, and
`dynamic_scatter_index_materialization`.  It improves full strict-EVAS from
`81/143` to `83/143` and reduces residual compile/interface failures from
`7/143` to `1/143`.  A 7-task EVAS+Spectre audit was attempted three times, but
all runs failed at the `virtuoso-bridge-lite` upload layer with SSH banner timeout,
so this row is not yet Spectre-audited.

## Residual Compile Boundary

The remaining full-ULTRA compile failures are not all safe local rewrites:

| Failure class | Current action |
| --- | --- |
| `sourced_port_voltage_drive` | Advanced local accept/reject now closes several cases under EVAS; Spectre audit retry is required before promotion. |
| `missing_generated_files=testbench.scs` | Advanced smoke-harness generation plus transition-skill bootstrap closes the current missing-TB compile cases under EVAS. |
| Wrong generated module body behind an `undefined_module` note | Local module rename is attempted and rejected unless compile rank improves; wrong-function bodies need regeneration. |
| Dynamic scatter indexing such as `V(out[idx])` | Dedicated scatter-index materialization works when combined with vector scalarization and transition buffering; more shapes need coverage. |

The current wrong-function gate proof is:

```text
completion92_calibration_bugfix
module_name_linkage rejected:
  undefined_module=v2b_4b;available_modules=dwa_ptr_gen_no_overlap
  after rename trial: instance_port_count_mismatch:IV2B:v2b_4b:nodes=6:ports=38
wrong_function_regeneration_gate:
  decision=route_to_prompt_regeneration
```

Prompt-side regeneration runner:

```text
runners/run_wrong_function_regeneration.py
```

This runner copies the gated candidate, builds a public-only regeneration prompt
from the task prompt, strict-EVAS notes, and public harness instance evidence,
then asks the LLM to regenerate only the missing module.  It does not synthesize
a replacement module locally.  The first `completion92_calibration_bugfix` run
was blocked before generation by an expired Bailian token:

```text
AuthenticationError: invalid access token or token expired
```

When the provider is unavailable, the same runner supports offline validation:

```text
--replay-response saved_response.txt
--replay-va historical_model_candidate.va
```

Replay mode sets `api_call_count=0` and records `call_mode=replay_*` in
`generation_meta.json` and the manifest.  It is only a strategy/plumbing
validation, not a live model result.

The current historical replay for `completion92_calibration_bugfix` uses an
older model-generated `v2b_4b.va` and produces:

```text
DUT compile: 1.0
TB compile: 1.0
Sim correctness: 0.0
Status: FAIL_SIM_CORRECTNESS
```

This confirms that prompt-side regeneration of the missing public module can
close the remaining compile failure, while behavior correctness remains a
separate mechanism/functional-repair problem.
