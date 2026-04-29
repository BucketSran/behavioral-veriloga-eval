# LEGO-Style Skill-Based RAG for vaEvas

This note defines the vaEvas version of a LEGO-style mechanism platform.

The goal is not to retrieve arbitrary text. The goal is to retrieve typed,
construction-ready Verilog-A mechanism skills that can guide EVAS repair and
later pass real Spectre validation.

## Why This Exists

Earlier H/I experiments showed that generic EVAS feedback helps with
compile/interface issues, but behavior repair often needs mechanism knowledge.
The closed-set R26/92PASS lineage, gold artifacts, and benchmark-v2
perturbations contain useful experience, but it must be represented as
type-level skills rather than task-specific answers.

## Skill Schema

Each LEGO skill contains:

1. `skill_id`: stable skill identifier.
2. `mechanism_family`: type-level mechanism label.
3. `concepts`: functional behavior concepts used for retrieval.
4. `slot_schema`: public ports/signals/parameters the skill needs.
5. `implementation_skeleton`: mechanism-level construction steps.
6. `code_shape`: compact Verilog-A skeleton, not a full task answer.
7. `checker_expectations`: what EVAS/checker is likely to verify.
8. `spectre_constraints`: Cadence Spectre-compatible coding constraints.
9. `anti_patterns`: common wrong repairs to avoid.
10. `source`: R26/92PASS/gold-derived or contract-card provenance.

The materialized library can be generated with:

```bash
python3 runners/lego_skill_library.py --dump-library docs/LEGO_MECHANISM_SKILLS.json
```

## Retrieval

Default retrieval is prompt-functional:

```bash
python3 runners/lego_skill_library.py \
  --prompt-file benchmark-v2/tasks/v2_dwa_keywordless_cursor_wrap/prompt.md
```

By default it does **not** use:

1. task id;
2. manifest `mechanism_family`;
3. gold code;
4. R26 same-task artifact paths.

It extracts functional concepts such as:

1. `sample_event`
2. `held_state`
3. `rotating_window`
4. `pulse_window`
5. `mutual_exclusion`
6. `divider_ratio`
7. `not_continuous_follower`
8. `bounded_transition_glitch`

Then it binds public interface names to skill slots, for example:

```text
clock -> cadence / advance / capture_strobe
code_outputs -> dec0..dec4 / dout_0..dout_7
cell_outputs -> cell0..cell7
up/dn -> raise_pulse/lower_pulse
```

If a task author wants stronger slot binding from public meta/checker specs,
use:

```bash
python3 runners/lego_skill_library.py \
  --prompt-file benchmark-v2/tasks/<task_id>/prompt.md \
  --meta-file benchmark-v2/tasks/<task_id>/meta.json \
  --use-meta-slots
```

`--use-meta-family` is intentionally off by default because it is an oracle
for retrieval experiments.

## EVAS and Spectre Flow

Use LEGO skills as an optional layer in adaptive EVAS repair:

```bash
VAEVAS_ENABLE_LEGO_SKILLS=1 \
VAEVAS_LEGO_SKILL_TOP_K=3 \
python3 runners/run_adaptive_repair.py \
  --model <model> \
  --task <task_id> \
  --max-rounds 3 \
  <existing F/G/I runner options>
```

Expected loop:

1. Initial model output is checked by EVAS.
2. If EVAS fails, the repair prompt receives EVAS notes plus LEGO mechanism
   skills.
3. The loop keeps syntax/interface/runtime issues gated before behavior repair.
4. EVAS-passing final candidates are sent to real Spectre/Virtuoso validation.

The Spectre step remains final acceptance. LEGO retrieval cannot by itself
claim pass.

## Benchmark-v2 Generalization Audit

Run the prompt-only retrieval audit:

```bash
python3 runners/run_lego_skill_audit.py \
  --manifest benchmark-v2/manifests/v2-small.json \
  --output-dir results/lego-skill-audit-v2-small-2026-04-29-r6
```

This checks whether the 30 validated benchmark-v2 perturbation prompts retrieve
the intended type-level skill set without using task ids or manifest mechanism
labels. Composition prompts require all expected LEGO blocks in Top-3/Top-k,
not merely one matching block.

Current prompt-only audit result:

```text
Top-1 primary skill: 28/30
Top-3 full skill-set recall: 30/30
Use task id / manifest family for routing: False
Use meta checker spec for slot binding: False
Result root: results/lego-skill-audit-v2-small-2026-04-29-r6
```

The two Top-1 misses are composition prompts where the secondary block is
ranked first, but the required full skill set is still retrieved in Top-3.

A miss should be handled by adding a functional concept rule or improving the
benchmark prompt. It should not be fixed by hard-coding a task id.

## Relationship to Existing Assets

| Existing asset | LEGO role |
|---|---|
| `CIRCUIT_MECHANISM_SKELETONS.json` | source of implementation skeletons and code shapes |
| `CLOSEDSET92_COMPLETION_LEDGER.json` | evidence that closed-set skills came from successful repair lineage |
| `CLOSEDSET_CIRCUIT_TEMPLATES.json` | teacher artifacts and provenance, not cold-start evidence |
| `benchmark-v2/` | perturbation split to test functional generalization |
| `run_adaptive_repair.py` | EVAS multi-round repair loop |
| `spectre_validate_baseline.py` | final real-Spectre acceptance |

## Claim Boundary

Allowed claim:

> We built a LEGO-style, typed mechanism-skill layer that retrieves
> construction-ready Verilog-A skills from prompt-level functional semantics and
> can be injected into EVAS repair loops.

Not allowed without additional model runs:

> LEGO skills improve cold-start full92 pass rate.

That requires a full A/D/F/G/I-style experiment with EVAS and final Spectre
validation.
