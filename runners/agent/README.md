# vaEvas Agent

The unified closed-loop agent for vaBench: LLM generation → EVAS simulation →
scoring → diagnosis → targeted repair → repeat until PASS (or budget exhausted).

This subpackage supersedes the standalone `vaEvas-Agent` repo and absorbs the
features of three legacy runners (`evas_loop.py`, `run_adaptive_repair.py`,
`run_model_assisted_loop.py`), which now live in `runners/legacy/` for
reproducibility only.

## Quick start

```bash
# From the repo root (behavioral-veriloga-eval/):
python -m runners.agent doctor          # check environment
python -m runners.agent list            # discover tasks (v1 + v3)
python -m runners.agent run <task_id>   # run the closed loop on one task
python -m runners.agent config --show   # inspect / edit configuration
```

## What it does

For one task, the agent loops up to `config.loop.max_rounds` times:

1. **Round 0** — generate DUT (`*.va`) and/or testbench (`*.scs`) via the LLM,
   using a skill-bundle prior.
2. **Score** — stage the candidate and run `score.score_one_task` (the same
   pipeline used by the rest of `runners/`). Both v1 (`meta.json` + `gold/`)
   and v3 (`task.toml`/`solution/` + `test_hidden/`) task formats are handled.
3. **Round 1+** — build an EVAS-guided repair prompt (delegated to
   `runners/build_repair_prompt.py`, which carries the metric-gap / layered
   repair knowledge) and regenerate.
4. **Stop** when the task passes, or when `max_rounds` / stall / regression
   limits are hit.

## Configuration

Config lives at `runners/agent/config/default.json` (JSON, not YAML — to avoid
adding a pyyaml dependency to this repo). Override with `VAEVAS_AGENT_CONFIG`
or edit in place via `python -m runners.agent config --set-model ...`.

Key knobs in `loop`:

| Knob | Default | Meaning |
|---|---|---|
| `prompt_mode` | `guided-repair` | Which `build_repair_prompt` builder to use. See "Experiment modes" below. |
| `include_skill` | `true` | Inject circuit-category skill knowledge into the prompt. |
| `max_rounds` | `8` | Hard cap on rounds. |
| `stall_limit` | `2` | Stop after N consecutive no-progress rounds. |
| `regress_limit` | `2` | Stop after N consecutive regressing rounds. |
| `layered_repair` | `false` | Enable the 5-layer repair policy (see below). |

## Absorbed features

### From `evas_loop.py` — parallel batch + resume
- `python -m runners.agent experiment --workers N` runs presets × tasks in parallel.
- Per-round results persist as `round_N_result.json`; re-running resumes from
  the last completed round unless `--force`.

### From `run_adaptive_repair.py` — layered repair (optional)
Enable with `config.loop.layered_repair: true` or `run --layered`. Each failed
round is classified into one of five layers and the LLM is told to edit **only**
that layer:

| Layer | Trigger | What the LLM may change |
|---|---|---|
| `compile_dut` | dut_compile < 1.0 | DUT `.va` syntax/interface only |
| `compile_tb` | tb_compile < 1.0 | testbench wiring only |
| `runtime_interface` | no tran.csv / returncode=1 | coupled DUT/TB interface |
| `observable` | missing signals | harness; DUT frozen |
| `behavior` | FAIL_SIM_CORRECTNESS | DUT logic only; gold harness frozen |

For the `behavior` layer, the gold verifier harness is staged (testbench +
helper `.va`s) while the candidate's DUT is preserved, so only the candidate
DUT's semantics are judged. Progress ranking uses a generic `failure_phase_score`
(0–6) plus any `key=value` metrics found in EVAS notes — no task-specific
hardcoding (the legacy runner hardcoded DWA metrics like `overlap_count`).

### From `run_model_assisted_loop.py` — 8 experiment modes
The 8 legacy modes collapse to combinations of `prompt_mode × include_skill ×
max_rounds` (+ optional `layered_repair`). Run them as named presets:

```bash
python -m runners.agent experiment \
    --presets skill-only,raw-generic-retry,evas-guided-repair \
    --tasks <id1>,<id2>,<id3> \
    --output-dir ./output/experiments
```

Preset → config mapping:

| Preset | prompt_mode | include_skill | max_rounds |
|---|---|---|---|
| `skill-only` | skill-only | — | 1 |
| `raw-generic-retry` | generic-retry | — | 1 |
| `evas-assisted` | evas-assisted | false | 1 |
| `skill-evas-informed` | skill-evas-informed | true | 1 |
| `evas-guided-repair` | guided-repair | true | 8 |
| `evas-guided-repair-no-skill` | guided-repair | false | 8 |
| `evas-guided-repair-3round` | guided-repair | false | 3 |
| `evas-guided-repair-3round-skill` | guided-repair | true | 3 |

Output is isolated per preset under `<output-dir>/<preset>/...` and a
comparison summary is written to `<output-dir>/experiment_summary.json`.

## Output layout

```
<output-dir>/<model_slug>/<task_id>/round_<N>/sample_0/
    ├── <module>.va
    ├── tb_<name>.scs
    └── evas_output/         # from score_one_task
<output-dir>/<task_id>/
    ├── round_<N>_result.json
    └── final_result.json
```

This matches the convention `score.py` expects (`<model>/<task>/sample_<idx>/`).

## LLM providers

Four modes (richer than `runners/generate.py`, which had no retry):

| Provider | Use for |
|---|---|
| `anthropic` | Native Anthropic (Claude) |
| `anthropic-compatible` | DashScope/Bailian (qwen, glm, kimi, minimax) via base_url; DeepSeek; proxies |
| `openai` | Native OpenAI (GPT/o-series) |
| `openai-compatible` | Azure, vLLM, ollama, local |

All calls retry up to 3 times with exponential backoff.

## Relationship to the rest of `runners/`

The agent **consumes** these sibling modules and does not duplicate them:

- `runners/score.py` → `score_one_task` (scoring, both v1+v3)
- `runners/build_repair_prompt.py` → all repair-prompt builders
- `runners/generate.py` → referenced for the canonical prompt conventions
- `runners/simulate_evas.py` → `run_case`, invoked transitively via `score_one_task`

The agent **replaces** (for new work) the three closed-loop runners now in
`runners/legacy/`. Those files are kept for reproducing prior results; their
original import paths (`from evas_loop import ...`) still work via re-export
stubs in `runners/`.
