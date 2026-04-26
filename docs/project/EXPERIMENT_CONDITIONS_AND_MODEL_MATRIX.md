# Experiment Conditions And Cross-Model Matrix

This document unifies the `A/B/C/D/E/F/G/H` condition definitions used in vaEvas and
defines the recommended cross-model comparison protocol.

Important scope note:
- `full86` is the historical split name used by the scripts.
- In the current benchmark tree, `full86` resolves to **92 scored tasks**.
- Unless explicitly noted otherwise, "full benchmark" below means the current
  `full86` split as returned by `list_task_dirs()`.
- Several historical result folders were produced before later prompt-system
  improvements landed, including:
  - benchmark `prompt.md` port-list repairs
  - stronger module-name / contract injection in `generate.py`
  - stricter Verilog-A syntax guidance in baseline prompts
- Therefore, older baseline result folders are useful for **failure-pattern
  exploration**, but they should be treated as **legacy baselines**, not as the
  final apples-to-apples numbers for the current method snapshot.

## 1. Unified Condition Table

| Condition | Checker In Prompt | Skill In Prompt | EVAS Feedback Used | Repair Rounds | Current Runner Mapping | Primary Question |
|---|---|---|---|---:|---|---|
| `A` | No | No | No | 0 | `generate.py` baseline | Absolute raw model baseline: what can the model do with only the task prompt? |
| `B` | Yes | No | No | 0 | `generate.py --include-checker` | Does checker transparency alone improve generation? |
| `C` | Yes | Yes | No | 0 | `generate.py --include-checker --include-skill` | What does domain Skill add on top of checker visibility? |
| `D` | Yes | No | Yes | 1 | `run_model_assisted_loop.py --mode evas-guided-repair-no-skill` | What is the value of one EVAS-guided repair step without Skill? |
| `E` | Yes | Yes | Yes | 1 | `run_model_assisted_loop.py --mode evas-guided-repair` | What is the value of one EVAS-guided repair step with Skill? |
| `F` | Yes | No | Yes | 3 | `run_model_assisted_loop.py --mode evas-guided-repair-3round` | What is the value of generalized multi-round EVAS repair without model-specific tuning? |
| `G` | Yes | Yes | Yes | 3 | `run_model_assisted_loop.py --mode evas-guided-repair-3round-skill` | What is the value of generalized multi-round EVAS repair with Skill enabled? |
| `H` | Yes | Yes | Yes + EVAS fitness search | Adaptive | `signature_guided_h.py --anchor-root <G artifacts>` prototype | Can signature-gated mechanism templates rescue failures left after `G` without task-id overfitting? |

## 2. Condition Semantics

### `A`: Raw Generation
- No checker source or checker summary is exposed to the model.
- No Skill bundle is exposed.
- No EVAS diagnosis is fed back.
- This is the cleanest "model alone" baseline.
- For formal reporting, `A` must be rerun on the **current prompt snapshot**.

### `B`: Checker-Transparent Baseline
- The model sees checker information, but there is still no repair loop.
- This isolates the value of making pass conditions explicit.
- `B` is also the canonical baseline that feeds `D` and `F`.
- Historical `B` results produced before prompt repairs should not be mixed with
  current `D/F` results in final claims.

### `C`: Checker + Skill Baseline
- Adds compact domain knowledge on top of `B`.
- Still no EVAS repair.
- This isolates the value of Skill without closed-loop diagnosis.
- Like `A/B`, `C` should be rerun whenever the underlying prompt construction
  changes materially.

### `D`: Single-Round EVAS Repair, No Skill
- Starts from the `B` baseline.
- Uses one EVAS result to construct a repair prompt.
- No Skill bundle is injected during repair.
- This is the cleanest "EVAS diagnosis value" condition.

### `E`: Single-Round EVAS Repair, With Skill
- Starts from the `B/C` style setup but includes Skill during repair.
- This is the "complete single-round system" condition.

### `F`: Multi-Round EVAS Repair, No Skill
- Starts from the `B` baseline.
- Runs three EVAS-guided repair rounds.
- Current implementation includes generalized, model-agnostic system changes:
  - best-round retention instead of always taking the last round
  - structured checker target extraction
  - gold contract anchor extraction
  - contract-first vs behavior-first repair routing
  - two-phase repair policy across rounds
- `F` is the current main condition for testing whether EVAS can support
  robust multi-round optimization.

### `G`: Multi-Round EVAS Repair, With Skill
- Starts from the `B` baseline.
- Runs three EVAS-guided repair rounds with Skill injection enabled.
- Mirrors `F` except for Skill, isolating whether multi-round Skill improves
  repair convergence.

### `H`: G + Signature-Guided Template Search
- Starts from the best available `G` artifact for each task.
- Re-scores the exact artifact before attempting repair; stale historical G
  metadata is not trusted for rescue counts.
- Current prototype is DUT-side: it uses the benchmark gold/reference testbench
  as the behavior harness. End-to-end generated-testbench closure should be
  reported separately.
- If the re-scored `G` artifact fails, the runner first classifies the EVAS
  failure notes, then checks the generated DUT module/interface signature.
- A bounded mechanism-template branch may run only when both the failure
  signature and interface signature match a reusable family.
- EVAS is used as the fitness oracle to select the first passing candidate or
  the best metric-moving candidate.
- Current implementation is a prototype, not yet the final full92 condition:
  `runners/signature_guided_h.py`.
- Earlier `runners/template_guided_smallset.py` results remain useful
  exploratory evidence, but formal H promotion should use the signature-gated
  runner rather than task-id-selected templates.
- `H` is designed to test whether EVAS speed can support generate-and-validate
  mechanism search where free-form LLM repair fails to generate the right
  candidate mechanism.

## Current Scoring System Snapshot

The current run system includes several safeguards that should be kept fixed
when refreshing `A/B/C/D/E/F/G/H` numbers:

- `score.py` uses per-task output isolation so parallel EVAS scoring cannot
  share or corrupt `tran.csv`.
- `score.py --resume` uses fingerprinted caches for generated files, gold
  files, runner code, and simulation config.
- `score.py --save-policy contract` is the default paper-facing setting; it
  preserves only contract/gold observables needed by the checker.
- `score.py --save-policy debug` keeps broader observables for repair/debug
  runs where extra signals help failure attribution.
- Parity-validated streaming/fast checkers are enabled by default. Use
  `VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS=1` to force the original row-based
  checker path for audit. Unvalidated experimental streaming checkers still
  require `VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS=1` and should not be
  used in formal scoring unless equivalence is separately validated.
- Latest partial refresh status is tracked in
  `docs/project/LATEST_SYSTEM_SNAPSHOT_2026-04-26.md`.

## 3. Fair Comparison Rules

To keep claims model-agnostic and methodologically clean, use the following rules.

### Rule 1: Compare models under the same condition
Valid:
- `Kimi-B` vs `Qwen-B`
- `Kimi-F` vs `Qwen-F`

Invalid:
- `Kimi-F` vs `Qwen-B`
- `Qwen raw probe` vs `Kimi full repair`
- `legacy Qwen-B` vs `current Kimi-F`
- `historical baseline` vs `current prompt-snapshot repair`

### Rule 2: Compare improvements within each model
The main method claim should be expressed as **delta over baseline**, not just
absolute Pass@1.

Recommended deltas:
- `B -> D`
- `B -> F`
- `C -> E`
- `C -> G`
- `F -> G`

Secondary deltas:
- `A -> B`
- `B -> C`

### Rule 3: Separate model quality from system availability
For every model/condition pair, track:
- `Return rate`: how many tasks returned a valid candidate within budget
- `Pass rate over all tasks`
- `Pass rate over returned tasks`

This is especially important for unstable models such as some `glm-*` routes.

### Rule 4: Keep EVAS-only and Spectre claims separate
The current comparison matrix should be reported as:
- **EVAS-only benchmarking**

Spectre should remain a later validation step for selected conclusions, not the
primary cross-model comparison path.

## 4. What Counts As "Model-Agnostic" Optimization

The project should avoid per-model patches such as:
- "special prompt just for Qwen"
- "special timeout workaround just for GLM as the method"
- "hard-coded task/model exception tables as the main result"

The method should instead emphasize system-level, model-agnostic improvements:
- explicit checker targets
- explicit DUT/TB contract anchors
- repair-stage routing
- structured failure interpretation
- best-round preservation
- EVAS measurement-driven repair prompts

These are acceptable because they operate at the benchmark/system level rather
than being tailored to one specific frontier model.

## 5. Cross-Model Experiment Matrix

The table below summarizes which models are currently suitable for which parts
of the condition matrix.

| Model | Provider | Current API Stability | Recommended Baseline Conditions | Recommended Repair Conditions | Current Status | Notes |
|---|---|---|---|---|---|---|
| `kimi-k2.5` | Bailian / Moonshot | Stable | `A/B/C` on full benchmark | `D/E/F` on dev24 and full benchmark | Primary reference model | Best current end-to-end executor in this workspace |
| `qwen3-max-2026-01-23` | Bailian / Qwen | Stable | `A/B/C` on full benchmark | `D/F` on dev24 first, then full benchmark | Strong comparison model | Stable API, but baseline failures concentrate on missing testbench / contract issues |
| `qwen3-coder-plus` | Bailian / Qwen | Stable | `A/B/C` on full benchmark | `D/F` optional after `qwen3-max` | Secondary comparison model | Useful as a code-focused Qwen variant |
| `qwen3.5-plus` | Bailian / Qwen | Mostly stable | `A/B/C` on full benchmark | `D/F` optional after `qwen3-max` | Secondary comparison model | Has occasional infra noise but generally callable |
| `glm-4.7` | Bailian / GLM | Unstable on complex tasks | Small baseline calibration set first | Not recommended yet for `D/E/F` | Candidate only | Some complex tasks return, others timeout at 120s |
| `glm-5` | Bailian / GLM | Poor on complex tasks | Small probe only | Not recommended | Blocked for fair batch comparison | Complex Verilog-A tasks often timeout before any candidate is returned |
| `MiniMax-M2.5` | Bailian route expected | Not yet validated with current keying | Probe only | Not recommended | Blocked by credential mismatch in latest probe | Current token tested here did not authenticate against the Bailian endpoint |

## 6. Recommended Run Order

To avoid conflating model instability with method quality, use the following
execution order.

### Phase 1: Baseline Matrix
Run for all stable models:
- `A`
- `B`
- `C`

Recommended models:
- `kimi-k2.5`
- `qwen3-max-2026-01-23`
- optionally `qwen3-coder-plus`
- optionally `qwen3.5-plus`

Primary outputs:
- Pass@1 under each baseline condition
- failure taxonomy by model
- `A -> B` and `B -> C` gains

### Phase 2: Repair Matrix On Dev Set
Run on `dev24` first:
- `D`
- `E`
- `F`

Recommended models:
- `kimi-k2.5`
- `qwen3-max-2026-01-23`

Primary outputs:
- `B -> D`
- `C -> E`
- `B -> F`
- per-round success and failure transitions

### Phase 3: Promote Stable Repair Conditions To Full Benchmark
After dev24 confirms stability:
- run `D` and `F` on the full benchmark for `kimi-k2.5`
- run `D` and `F` on the full benchmark for `qwen3-max-2026-01-23`
- run `E` only if Skill is part of the paper's target comparison

Primary outputs:
- final cross-model, same-condition comparison
- same-model improvement deltas
- family-wise gains

## 7. Minimal Paper-Ready Comparison Grid

If compute budget is limited, the minimum convincing matrix is:

| Layer | Conditions | Models |
|---|---|---|
| Baseline transparency | `A`, `B`, `C` | `kimi-k2.5`, `qwen3-max-2026-01-23` |
| Single-round EVAS | `D`, `E` | `kimi-k2.5`, `qwen3-max-2026-01-23` |
| Multi-round EVAS | `F` | `kimi-k2.5`, `qwen3-max-2026-01-23` |

This matrix is enough to support:
- the value of checker transparency
- the value of Skill
- the value of EVAS repair
- whether multi-round EVAS is more robust than single-round EVAS
- whether those gains hold across at least two different model families

## 8. Operational Notes

- `run_experiment_matrix.py` now recognizes `F` as an official condition.
- For repair conditions, `B` remains the canonical no-Skill baseline that feeds
  the EVAS inner scoring stage.
- When reporting final numbers, prefer per-task `result.json` aggregation over
  any stale top-level summary if required-axis schema drift is suspected.

## 9. Recommended Claim Framing

Use wording like:

- "Our optimizations are benchmark-level and loop-level, not model-specific."
- "We compare models under the same condition and compare conditions within the same model."
- "The main method effect is measured as improvement from checker-transparent baseline to EVAS-guided repair."
- "Cross-model differences appear mainly in failure distribution, while the proposed loop improvements remain model-agnostic."
