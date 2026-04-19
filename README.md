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

As of 2026-04-19:

1. `end-to-end`: 39 tasks closed
2. `spec-to-va`: 18 tasks closed
3. `bugfix`: 8 tasks closed
4. `tb-generation`: 11 tasks closed for EVAS scoring, with EVAS+Spectre execution evidence recorded for 7 of them
5. benchmark / closed-loop rows: 30 `dual-validated`
6. benchmark / closed-loop rows: 1 passed PLL row with a residual
   waveform-alignment audit item

There are currently no open benchmark rows with `verification_status != passed`.
There is one special tracked waveform-alignment row,
`cppll_freq_step_reacquire_smoke`. The older `292.5ns` gap was caused by an
asymmetric comparator anchor, and the canonical
`results/gold-dual-suite-cppll-initial-step-fix-v2/` rerun now closes the
task-aware PLL parity metrics. A residual late-`lock` pulse tail difference is
kept as an EVAS/Virtuoso waveform-perfect alignment audit item rather than a
benchmark blocker.

The latest expansion passes added:

1. on 2026-04-18:
   `inverted_comparator_logic_bug`, `swapped_pfd_outputs_bug`,
   `wrong_edge_sample_hold_bug`, `gain_step_tb`, `sample_hold_step_tb`, and
   `xor_phase_tb`, with clean EVAS+Spectre rerun results under
   `results/gold-dual-suite-expansion-clean-2026-04-18/`
2. on 2026-04-19:
   `comparator_hysteresis_smoke` and `pfd_deadzone_smoke`, with dual-suite
   results under `results/gold-dual-suite-expansion-2026-04-19/`
3. later on 2026-04-19:
   `cppll_freq_step_reacquire_smoke`, with canonical dual-suite results under
   `results/gold-dual-suite-cppll-initial-step-fix-v2/`; the larger `292.5ns`
   gap was traced to an asymmetric comparator anchor and the task-aware PLL
   parity metrics now close, while late `lock` pulse tail alignment remains
   tracked separately for EVAS/Virtuoso audit work
4. also on 2026-04-19:
   `adpll_ratio_hop_smoke`, `pfd_reset_race_smoke`, `dco_gain_step_tb`, and
   `sample_hold_aperture_tb`, with EVAS gold-suite results under
   `results/gold-suite-adpll-ratio-hop-2026-04-19/`,
   `results/gold-suite-pfd-reset-race-2026-04-19/`, and
   `results/gold-suite-tb-expansion-2026-04-19/`; these P0 expansion cases are
   now benchmark rows, while bridge-backed dual validation remains deferred by
   the current no-bridge execution rules
5. later on 2026-04-19:
   `strongarm_reset_priority_bug`, `gray_counter_one_bit_change_smoke`,
   `multimod_divider_ratio_switch_smoke`, `segmented_dac_glitch_tb`, and
   `comparator_offset_search_smoke`, with EVAS gold-suite results under
   `results/gold-suite-p1-bugfix-2026-04-19/`,
   `results/gold-suite-p1-e2e-2026-04-19/`, and
   `results/gold-suite-p1-tb-2026-04-19/`; `xor_pd_smoke` and
   `clk_burst_gen_smoke` were also rechecked under EVAS and their task metadata
   was brought back in sync with the already-closed benchmark table facts
6. later on 2026-04-19:
   `dwa_wraparound_smoke`, with EVAS gold-suite results under
   `results/gold-suite-p2-dwa-wraparound-2026-04-19/`, covering DWA pointer
   wraparound and split thermometer selection at the 15 -> 0 boundary
7. later on 2026-04-19:
   `sample_hold_droop_smoke`, `bbpd_data_edge_alignment_smoke`,
   `nrz_prbs_jitter_tb`, and `serializer_frame_alignment_smoke`, with EVAS
   gold-suite results under `results/gold-suite-p2-2026-04-19/`, completing the
   planned P2 queue for sample/hold droop, near-edge BBPD alignment, comms
   jitter/burst testbench generation, and serializer frame-boundary checks

The 2026-04-19 pass also hardened the PFD behavior check in
`runners/simulate_evas.py` so near-deadzone short pulses use time-weighted duty
instead of adaptive-step sample density.

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
