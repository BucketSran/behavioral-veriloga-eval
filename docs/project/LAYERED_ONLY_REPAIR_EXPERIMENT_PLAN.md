# Layered Only-Repair Experiment Plan

Date: 2026-04-25

## Goal

Evaluate whether a layered EVAS repair policy improves closed-loop repair beyond fixed-round,
generic repair prompts.

Core policy:

- Compile/interface failure: repair the compile/interface layer only.
- Observable/stimulus failure: preserve DUT Verilog-A and repair only TB/harness observability.
- Behavior failure: freeze verifier harness and repair only DUT behavior.
- Use fast EVAS quick-check inside the loop.
- Run strict EVAS only after a candidate passes or clearly improves.

## Current Implementation

Runner:

- `runners/run_adaptive_repair.py`

New option:

- `--layered-only-repair`

Routing logic:

- `compile_dut`: `dut_compile < 1`
- `compile_tb`: `tb_compile < 1`
- `observable`: notes contain missing CSV, `tran.csv missing`, insufficient post-reset samples, or too few edges
- `behavior`: compile passes and EVAS reports behavior metrics
- `infra`: unclassified failure

Layer actions:

- `observable`: copy Verilog-A DUT files from the anchor candidate into the repaired candidate, so only TB/harness changes are evaluated.
- `behavior`: copy benchmark verifier harness from `tasks/**/gold`, but do not copy the gold DUT file.
- `compile_*`: do not freeze harness; prompt constrains the model to compile/interface edits.

## Pilot Validation

Command:

```bash
python3 runners/run_adaptive_repair.py \
  --task dwa_wraparound_smoke \
  --task dwa_ptr_gen_no_overlap_smoke \
  --max-rounds 1 \
  --patience 1 \
  --timeout-s 60 \
  --quick-maxstep 1n \
  --layered-only-repair \
  --initial-result-root results/tmp-observable-contract-dwa-check-2026-04-24 \
  --output-root results/adaptive-layered-only-dwa-pilot-2026-04-25 \
  --generated-root generated-adaptive-layered-only-dwa-pilot
```

Result:

- `dwa_ptr_gen_no_overlap_smoke`: `FAIL_SIM_CORRECTNESS -> PASS`
- `dwa_wraparound_smoke`: `FAIL_SIM_CORRECTNESS -> PASS`

## Next Test Set

Use the recent hard34 G result as the seed failure set:

- `results/evas-scoring-condition-G-kimi-k2.5-p9-compile-closure-hard34-allfamilies-2026-04-24`

### Observable-Layer Cases

These test whether TB/harness-only repair can expose readable and meaningful CSV behavior without
changing DUT logic.

| Task | Family | Category | Current note |
| --- | --- | --- | --- |
| `comparator_hysteresis_smoke` | end-to-end | comparator | `tran.csv missing` |
| `dwa_ptr_gen_smoke` | end-to-end | calibration | `tran.csv missing` |
| `flash_adc_3b_smoke` | end-to-end | data-converter | `too_few_edges=0` |
| `gain_extraction_smoke` | end-to-end | measurement | `tran.csv missing` |
| `sample_hold_droop_smoke` | end-to-end | sample-hold | `too_few_clock_edges=2` |
| `sar_adc_dac_weighted_8b_smoke` | end-to-end | data-converter | `tran.csv missing` |

### Behavior-Layer Cases

These test whether frozen verifier harness + DUT-only repair generalizes beyond DWA.

| Task | Family | Category | Current note |
| --- | --- | --- | --- |
| `adc_dac_ideal_4b_smoke` | end-to-end | data-converter | `unique_codes=1 vout_span=0.000` |
| `dac_binary_clk_4b_smoke` | end-to-end | data-converter | `levels=1 aout_span=0.000` |
| `gray_counter_4b_smoke` | end-to-end | digital-logic | `gray_property_violated bad_transitions=3` |
| `mux_4to1_smoke` | end-to-end | digital-logic | `sel*_err` |
| `pfd_reset_race_smoke` | end-to-end | phase-detector | incorrect UP/DN pulse timing |
| `serializer_8b_smoke` | end-to-end | comms | `bit_mismatch` |
| `adpll_timer_smoke` | end-to-end | pll-clock | `late_edge_ratio=0.500` |
| `cppll_tracking_smoke` | end-to-end | pll-clock | `freq_ratio=1.2500` |

### Control Cases

Keep the two DWA cases as positive controls:

- `dwa_ptr_gen_no_overlap_smoke`
- `dwa_wraparound_smoke`

## Execution Phases

### Phase 1: Small Matrix

Run 6 observable cases + 8 behavior cases + 2 DWA controls with Kimi only.

Recommended command shape:

```bash
python3 runners/run_adaptive_repair.py \
  --task <task1> --task <task2> ... \
  --max-rounds 2 \
  --patience 1 \
  --timeout-s 60 \
  --quick-maxstep 1n \
  --layered-only-repair \
  --source-generated-dir generated-table2-evas-guided-repair-3round-skill \
  --initial-result-root results/evas-scoring-condition-G-kimi-k2.5-p9-compile-closure-hard34-allfamilies-2026-04-24 \
  --output-root results/adaptive-layered-only-smallmatrix-kimi-2026-04-25 \
  --generated-root generated-adaptive-layered-only-smallmatrix-kimi
```

### Phase 2: Strict Confirmation

Strictly re-score only tasks that quick-check passes or improves.

Recommended command shape:

```bash
python3 runners/score.py \
  --model kimi-k2.5 \
  --generated-dir generated-adaptive-layered-only-smallmatrix-kimi \
  --output-dir results/adaptive-layered-only-smallmatrix-kimi-strict-2026-04-25 \
  --task <improved_or_passed_task> \
  --timeout-s 240
```

### Phase 3: Cross-Model Probe

After Kimi small matrix finishes, repeat the same task list with Qwen only if:

- Kimi small matrix improves at least 4 non-DWA tasks, or
- Kimi exposes clear layer-specific failure modes that should be compared across models.

Do not run Qwen first; the current goal is method validation, not model ranking.

## Success Metrics

Primary:

- `PASS` count after strict re-score.
- Number of non-DWA tasks that improve from `0.6667` to `1.0` or expose a narrower next-layer failure.

Secondary:

- Layer transition quality:
  - observable -> behavior is progress,
  - behavior -> PASS is success,
  - behavior -> observable is regression,
  - compile/TB regression is failure.
- Runtime:
  - quick-check wall time per task,
  - strict re-score wall time per improved task.

Stop conditions:

- Stop a task after one non-improving repair round.
- Stop the matrix if three consecutive tasks regress from behavior/observable into compile failure.
- Do not spend strict EVAS time on unchanged failures.

## Expected Conclusions

This experiment should answer:

- Whether layered only-repair generalizes beyond DWA.
- Whether observable-only repair reliably turns missing/too-few-sample failures into behavior metrics.
- Which categories benefit most from frozen verifier harness.
- Which categories need richer checker-to-repair diagnosis before repair can work.
