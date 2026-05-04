# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

The structured benchmark layer for evaluating Verilog-A behavioral model generation on EVAS-compatible (voltage-domain) modules. It provides task definitions, runners, checkers, and result tracking — not simulators or LLM harnesses.

The actual simulator is `EVAS`. The coding knowledge base is `veriloga-skills`. The bridge to Spectre/Virtuoso is `virtuoso-bridge-lite`.

## Task Families

```
tasks/
  spec-to-va/       Natural-language spec → DUT .va
  bugfix/            Broken .va → corrected .va
  tb-generation/     DUT + intent → minimal valid .scs
  end-to-end/        Spec → DUT → testbench → simulation → behavioral check
```

Each task directory contains: `prompt.md`, `meta.json`, `checks.yaml`, and optional `gold/`.

New benchmark-v2 tasks go into `benchmark-v2/tasks/<task_id>/` — **never** into the original `tasks/` tree.

## Three Evaluation Axes (Primary)

Every case is judged on these executable questions, not text-only checks:

1. `dut_compile_pass` — can EVAS accept the generated DUT `.va`?
2. `tb_compile_pass` — can EVAS accept the generated `.scs` testbench?
3. `sim_correct_pass` — does simulated behavior satisfy the case checks?

Primary metric: **Pass@1-deterministic** (temperature 0, single sample).

Failure labels: `FAIL_DUT_COMPILE`, `FAIL_TB_COMPILE`, `FAIL_SIM_CORRECTNESS`, `FAIL_INFRA`.

## Key Commands

```bash
# Run full examples smoke suite (manifest-driven)
python runners/run_examples_suite.py --output-root results/examples-suite

# Run gold suite for EVAS verification evidence
python3 runners/run_gold_suite.py

# Run dual suite (EVAS + Spectre) via bridge
./scripts/run_with_bridge.sh python3 runners/run_gold_dual_suite.py ...

# Check bridge readiness before long runs
./scripts/check_bridge_ready.sh

# Sync tracked table summaries from results
./scripts/sync_tables_from_results.sh

# Single DUT/testbench EVAS execution
python runners/simulate_evas.py tasks/end-to-end/voltage/clk_div_smoke \
  examples/digital-logic/clk_div/clk_div.va \
  examples/digital-logic/clk_div/tb_clk_div.scs

# Migrate legacy eval list (only when upstream source is available)
python runners/migrate_veriloga_evals.py
```

## Maintenance Flow

When project status changes:
1. Verify run quality in local `results/`
2. Sync tracked table summaries: `scripts/sync_tables_from_results.sh`
3. Append run line to `tables/RUN_REGISTRY.md`
4. Update `docs/project/PROJECT_STATUS.md` (current snapshot + next plan)
5. Update `docs/project/WORK_TODO.md` only after tracked summaries are in sync

## Key Files

| File | Role |
|------|------|
| `schemas/task.schema.json` | Task JSON format |
| `schemas/result.schema.json` | Result JSON format |
| `examples/manifest.json` | Smoke suite manifest |
| `tables/RUN_REGISTRY.md` | Compact run history with source paths |
| `docs/project/PROJECT_STATUS.md` | Current status for onboarding |
| `docs/project/POST_RUN_PLAYBOOK.md` | Standard end-of-run checklist |

## Coding Conventions

- Python: 4-space indent, type hints, `snake_case`, small single-purpose functions
- Verilog-A modules: lowercase with underscores (e.g., `clk_div.va`)
- Prefixes: `tb_` for testbenches, `analyze_` for analysis, `validate_` for check scripts
- Task IDs and JSON keys: `snake_case`

## Scope Boundaries

- Voltage-domain Verilog-A only — `V() <+`, `@(cross())`, `transition()` style
- No current-domain checks (`I() <+`, `ddt()`, `idt()`) unless scope explicitly expands
- Do not commit generated result directories or simulator artifacts unless intentional fixtures
