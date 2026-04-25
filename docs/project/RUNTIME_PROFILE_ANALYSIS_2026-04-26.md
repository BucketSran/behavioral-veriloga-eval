# Runtime Profile Analysis - 2026-04-26

This profile investigates why EVAS-only experiments become slow when scaling to
full92 and H-template validation.

## Important Finding: Parallel Scoring Needed Output Isolation

The first parallel scoring profile wrote multiple EVAS jobs into the same
`output_root/tran.csv`. That can corrupt CSV files or cause tasks to read another
task's waveform, producing false errors such as:

- `Error: line contains NUL`
- empty CSV fields
- unexpected `NoneType` conversion errors
- unstable pass/fail compared with serial scoring

Fix applied:

- `runners/score.py` now calls `run_case(..., output_root=output_dir / task_id)`.
- Each parallel scoring task writes to its own `<result-root>/<task_id>/tran.csv`.

After this fix, a smoke test on `pfd_deadzone_smoke` and `dff_rst_smoke`
produced isolated per-task CSV files and cleaner behavior notes.

## Clean Profile

Command:

```bash
python3 runners/score.py \
  --model kimi-k2.5 \
  --generated-dir generated-table2-evas-guided-repair-3round-skill \
  --output-dir results/runtime-profile-G-kimi-isolated-2026-04-26 \
  --timeout-s 180 \
  --workers 8 \
  --resume
```

Result:

- Tasks: 92
- Pass@1: 49/92 = 53.3%
- Median EVAS total time: 0.6 s
- p90 EVAS total time: 24.9 s
- Max EVAS total time: 176.9 s

The profile is highly skewed: most tasks are fast, and a small number dominate
wall time.

## Slowest Tasks

| Task | EVAS total | Tran time | Steps | CSV size | Main reason |
|---|---:|---:|---:|---:|---|
| `sar_adc_dac_weighted_8b_smoke` | 176.9 s | 134.3 s | 1,466,234 | 265.7 MB | Very large transient plus checker timeout |
| `pfd_reset_race_smoke` | 90.2 s | 71.2 s | 1,186,876 | 81.5 MB | Very fine maxstep plus checker timeout |
| `inl_dnl_probe` | 72.1 s | 53.3 s | 956,315 | 101.2 MB | Large CSV despite no sim_correct behavior check |
| `pfd_deadzone_smoke` | 65.8 s | 48.2 s | 1,138,675 | 78.2 MB | Very fine maxstep plus checker timeout |
| `digital_basics_smoke` | 50.7 s | 35.4 s | 325,300 | 58.6 MB | Multi-module save set plus checker timeout |
| `noise_gen_smoke` | 43.7 s | 27.3 s | 1,000,000 | 68.7 MB | Million-sample noise statistics |
| `dac_binary_clk_4b_smoke` | 38.5 s | 26.7 s | 552,403 | 44.8 MB | Long run plus checker timeout |
| `dwa_ptr_gen_no_overlap_smoke` | 36.7 s | 11.3 s | 217,408 | 95.8 MB | Many saved signals plus checker timeout |

## Root Causes

### 1. Huge Transient Step Counts

Several testbenches force very fine `maxstep` over long windows:

- `pfd_reset_race_smoke`: `tran stop=300n maxstep=10p`
- `pfd_deadzone_smoke`: `tran stop=300n maxstep=5p`
- `dac_binary_clk_4b_smoke`: `tran stop=660n maxstep=200p`
- `inl_dnl_probe`: `tran stop=68n maxstep=20p`

These settings can create hundreds of thousands to more than a million accepted
steps. EVAS is fast, but a million-step CSV still costs time to write and parse.

### 2. Checker Timeout on Large CSVs

Many slow failures now report:

- `behavior_eval_timeout>60s`

This means EVAS completed and wrote `tran.csv`, but Python-side behavior checking
did not finish within the watchdog. The main candidates for optimization are
streaming checkers and early-exit logic.

### 3. Too Many Saved Signals

Examples:

- `dwa_ptr_gen_no_overlap_smoke` saves 34 signals and creates a 95.8 MB CSV.
- `digital_basics_smoke` saves many multi-module signals and creates a 58.6 MB CSV.

For speed-focused validation, we should save only checker-observable signals.

### 4. Tasks With No Behavior Check Still Write Large CSVs

`inl_dnl_probe` passes with `sim_correct not required by scoring`, but still
spends 72.1 s and writes a 101.2 MB CSV. This is a strong candidate for a
preflight/compile-only fast path if its scoring contract does not require
behavior simulation.

## Recommended Fix Order

1. Keep output isolation for all parallel scoring. This is required for correctness.
2. Add a compile/preflight-only fast path for tasks where `sim_correct` is not required.
3. Add streaming or early-exit checkers for timeout-heavy tasks:
   `sar_adc_dac_weighted_8b_smoke`, PFD tasks, DWA no-overlap, digital basics,
   DAC binary clock.
4. Audit save lists and expose only checker-required observables where possible.
5. Only after these changes consider changing `tran/maxstep`; that has higher
   benchmark-contract risk.
