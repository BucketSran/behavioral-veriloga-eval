# behavioral-va-eval

Benchmark design package for evaluating the pure voltage-domain portion of the
`veriloga` skill stack on EVAS-compatible modules.

This benchmark is modeled after the strengths of VerilogEval v2:

- task cases stored as plain files/directories
- generation separated from execution/scoring
- deterministic `Pass@1` as the primary metric
- executable evidence instead of text-only rubric matching

## Scope

This benchmark is intentionally **EVAS-first**.

It only covers **pure voltage-domain Verilog-A modules** that can be verified by
EVAS. Current-domain and mixed-domain modules are out of scope for this
benchmark, and the benchmark score itself is still driven by EVAS-oriented task
checks. When bridge access is available, supported gold-backed tasks may also
record Spectre parity evidence for engineering closure and regression tracking.

## Current Status

As of 2026-04-18:

1. `end-to-end`: 24 tasks closed
2. `spec-to-va`: 18 tasks closed
3. `bugfix`: 7 tasks closed
4. `tb-generation`: 7 tasks closed for EVAS scoring, with EVAS+Spectre execution evidence recorded
5. benchmark / closed-loop rows: 24 `dual-validated`

There are currently no open benchmark rows with `verification_status != passed`.
The remaining project work is now mostly about provenance backfill, workflow
hardening, warning cleanup, and future benchmark expansion rather than missing
benchmark functionality.

The latest expansion pass on 2026-04-18 added
`inverted_comparator_logic_bug`, `swapped_pfd_outputs_bug`,
`wrong_edge_sample_hold_bug`, `gain_step_tb`, `sample_hold_step_tb`, and
`xor_phase_tb`. A clean EVAS+Spectre rerun for all 6 new tasks now lives under
`results/gold-dual-suite-expansion-clean-2026-04-18/`.

It is split into four task families:

1. `spec-to-va`
   Natural-language specification -> DUT `.va`
2. `bugfix`
   Broken voltage-domain `.va` -> corrected DUT `.va`
3. `tb-generation`
   DUT + behavior intent -> minimal valid `.scs`
4. `end-to-end`
   Spec -> DUT -> testbench -> simulation -> minimum behavioral check

## Primary evaluation axes

Every meaningful case should be judged on these three executable questions:

1. `dut_compile_pass`
   Can EVAS accept the generated DUT `.va`?
2. `tb_compile_pass`
   Can EVAS accept the generated `.scs` testbench?
3. `sim_correct_pass`
   Does the simulated behavior satisfy the minimum case checks?

These are the real benchmark signals. Text-only prechecks are not benchmark
results.

## Primary metrics

- `Pass@1-deterministic`
  Temperature 0 / single sample
- Optional per-axis rates:
  - DUT compile rate
  - testbench compile rate
  - simulation correctness rate

Primary reporting should remain deterministic `Pass@1`.

## Failure labels

Use explicit failure attribution instead of a single generic failure bucket:

- `FAIL_DUT_COMPILE`
- `FAIL_TB_COMPILE`
- `FAIL_SIM_CORRECTNESS`
- `FAIL_INFRA`

## Layout

```text
behavioral-va-eval/
  README.md
  schemas/
    task.schema.json
    result.schema.json
  tasks/
    spec-to-va/
    bugfix/
    tb-generation/
    end-to-end/
  examples/
    manifest.json
  runners/
    README.md
```

Each benchmark case is a directory containing:

- `prompt.md`
- `meta.json`
- `checks.yaml`
- optional `gold/`

The self-contained executable assets used by the first benchmark wave live under
`examples/`. The default 14-group smoke suite is driven from
`examples/manifest.json`.

For end-to-end tasks that already include checked-in `gold/` DUT and testbench
assets, use `python3 runners/run_gold_suite.py` to generate reusable EVAS
verification evidence under `results/gold-suite/`.

When Spectre parity is needed, use `./scripts/run_with_bridge.sh python3
runners/run_gold_dual_suite.py ...` so the SSH tunnel lifetime is tied to the
command being executed. This wrapper runs `runners/bridge_preflight.py` first,
starts a temporary local tunnel, and then emits EVAS + Spectre reports under
`results/gold-dual-suite*/`.

If you want a quick environment check before a longer run, use
`./scripts/check_bridge_ready.sh` from the repo root. The standalone
`start_bridge_tunnel.sh` helper still exists for manual debugging, but the
wrapper is the recommended reproducible workflow in this repo.

## Maintenance Flow

When project status changes, update docs in this order:

1. update `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`
2. run `python coordination/scripts/sync_task_assignment.py`
3. run `python coordination/scripts/sync_task_assignment.py --check`
4. update `WORK_TODO.md` only after the result table and derived summary are in sync

Use the files this way:

1. `WORK_TODO.md`: next-stage roadmap and prioritized backlog
2. `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`: row-level benchmark facts
3. `coordination/docs/project/TASK_ASSIGNMENT.md`: auto-generated summary view

## Initial benchmark strategy

Start small and stable:

- 8 to 12 `spec-to-va` cases
- 4 to 6 `bugfix` cases
- 4 to 6 `tb-generation` cases
- 4 to 6 `end-to-end` cases

The first end-to-end set should prefer stable voltage-domain modules such as:

- `clk_div`
- `comparator`
- `ramp_gen`
- `d2b_4b`
- `dac_binary_clk_4b`
- `lfsr`

## Relationship to existing evals

Existing files:

- `veriloga/evals/evals.json`
- `evas-sim/evals/evals.json`
- `openvaf/evals/evals.json`

should be treated as seed prompts and expectations, not as the final benchmark
format. `behavioral-va-eval/` is the structured benchmark layer intended to sit
above those skill-local eval lists.
