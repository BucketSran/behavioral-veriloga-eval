# Repository Guidelines

## Project Structure & Module Organization
`tasks/` holds benchmark cases, organized as `tasks/<family>/voltage/<category>/<case>/` with `prompt.md`, `meta.json`, `checks.yaml`, and optional `gold/`. `examples/` contains runnable reference designs, grouped by intent such as `digital-logic/`, `data-converter/`, and `stimulus/`; each example usually includes `.va`, `tb_*.scs`, `analyze_*.py`, and `validate_*.py` files. `runners/` contains harness scripts for migration and EVAS execution. `schemas/` defines the task and result JSON formats.

## Build, Test, and Development Commands
Use Python 3 for repository tooling.

- `python runners/run_examples_suite.py --output-root results/examples-suite` - runs the manifest-driven smoke suite for the example library.
- `python runners/simulate_evas.py tasks/end-to-end/voltage/clk_div_smoke examples/digital-logic/clk_div/clk_div.va examples/digital-logic/clk_div/tb_clk_div.scs` - executes one DUT/testbench pair through EVAS.
- `python examples/digital-logic/clk_div/validate_clk_div.py` - runs a case-specific validation script when present.
- `python runners/migrate_veriloga_evals.py` - regenerates structured task directories from the legacy eval list; only use when the upstream source repo is available.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, type hints where helpful, and small single-purpose functions. Use `snake_case` for Python files, functions, task IDs, and JSON keys. Keep Verilog-A modules descriptive and lowercase with underscores, for example `clk_div.va`. Prefix Spectre testbenches with `tb_`, analysis helpers with `analyze_`, and check scripts with `validate_`. Match the current formatting in JSON and YAML files; no formatter configuration is committed here, so keep diffs minimal and consistent.

## Testing Guidelines
There is no centralized `tests/` package yet; validation is case-driven. For benchmark content changes, run the nearest `validate_*.py` script and, when applicable, the full examples smoke suite. Preserve the executable scoring axes used across the repo: `dut_compile`, `tb_compile`, and `sim_correct`. When adding a new task, ensure `meta.json` and `checks.yaml` stay aligned with `schemas/`.

## Commit & Pull Request Guidelines
History is currently minimal (`Initial commit`), so use short imperative commit subjects such as `Add SAR logic voltage task`. Keep commits focused on one task family or runner change. Pull requests should describe the affected paths, note any EVAS or validation commands you ran, and include sample output or result snippets when behavior changes. Link related issues or benchmark gaps when available.

## Environment & Safety Notes
This repository is EVAS-focused and intentionally limited to pure voltage-domain Verilog-A flows. Avoid introducing current-domain checks unless the benchmark scope changes. Do not commit generated result directories or simulator artifacts unless they are intentional fixtures.
