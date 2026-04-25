# Experiment Speedup Plan

This note records speedups that preserve benchmark semantics. The goal is to
make EVAS-only validation fast enough for iterative repair-policy development.

## Priority Order

| Priority | Lever | Why it helps | Scoring risk |
|---|---|---|---|
| P0 | Parallel EVAS scoring | Full-matrix scoring was serial; task-level EVAS runs are mostly independent. | Low, each task keeps the same timeout/checker. |
| P0 | Early stop template search on first PASS | Once a candidate passes the checker, extra candidates do not change Pass@1. | Low for pass-rate experiments; disable when collecting ablation details. |
| P0 | Fingerprint-checked resume/cache | Avoid re-scoring unchanged G anchors and already-tested template candidates after interruption. | Low, reuse requires matching input/checker hashes. |
| P1 | Failure-first subsets | Template design should run on G-failed or signature-eligible tasks before full92. | Low if final claims still use full92. |
| P1 | Runtime telemetry | Record EVAS elapsed time and accepted step count to identify slow tasks. | Low, result metadata only. |
| P2 | Timeout profiles | Use short timeout for fast template probes and full timeout for final matrix. | Medium; short timeouts can turn slow valid cases into false failures. |
| P2 | CSV/checker fast paths | Stream large CSVs and stop behavior checks once decisive evidence is found. | Medium; must be checker-specific and validated against gold. |
| P3 | Transient/maxstep relaxation | Can speed pathological tasks. | High if it changes the public validation contract; use only for exploration unless standardized. |

## Implemented

- `runners/score.py` now supports `--workers N` for task-level parallel EVAS scoring.
- `runners/score.py` isolates each parallel task's EVAS output under
  `<result-root>/<task_id>/`, preventing concurrent jobs from corrupting a
  shared `tran.csv`.
- `runners/run_experiment_matrix.py` now supports `--score-workers N` and passes it to scoring.
- `runners/signature_guided_h.py` now supports `--workers N`.
- `runners/signature_guided_h.py` defaults to early stop when a template candidate reaches PASS.
- Use `--no-early-stop-pass` only when we need complete candidate ablation logs.
- `runners/score.py` now supports `--resume`, which reuses per-task `result.json` only when generated files, gold files, `score.py`, `simulate_evas.py`, and scoring config match.
- `runners/run_experiment_matrix.py` now supports `--resume-score` and passes fingerprint-checked resume to scoring.
- `runners/signature_guided_h.py` now supports `--resume` with fingerprint-checked per-task `summary.json` reuse.
- `runners/simulate_evas.py` now records EVAS `tran_elapsed_s`, `total_elapsed_s`, and `accepted_tran_steps` when available.
- `runners/score.py` now stores that timing metadata as `evas_timing` in each task result.

## Recommended Defaults

For local interactive probes:

```bash
python3 runners/signature_guided_h.py \
  --workers 4 \
  --timeout-s 120 \
  --tasks clk_divider multimod_divider flash_adc_3b_smoke
```

For full EVAS-only matrix scoring:

```bash
python3 runners/run_experiment_matrix.py \
  --model kimi-k2.5 \
  --split full86 \
  --condition G \
  --stage all \
  --gen-workers 4 \
  --score-workers 4 \
  --resume-score \
  --timeout-s 180
```

If the machine is idle and provider/API limits are not involved, try
`--score-workers 8` for EVAS scoring. Do not raise LLM `--gen-workers` blindly:
generation is limited by provider rate limits, network stability, and API cost.

## Validation Log

- `python3 -m py_compile runners/score.py runners/run_experiment_matrix.py runners/signature_guided_h.py`
- Parallel scoring smoke:
  `results/smoke-parallel-score-2026-04-26/model_results.json`
- Parallel scoring resume smoke:
  `results/smoke-parallel-score-resume-2026-04-26/model_results.json`
  showed a first real run followed by cached per-task reuse.
- Parallel H resume smoke:
  `results/smoke-signature-H-resume-2026-04-26/summary.json`
  showed a first real run followed by cached per-task reuse.
- Timing metadata smoke:
  `results/smoke-score-timing-2026-04-26/clk_divider/result.json`
  recorded `evas_timing` including elapsed time and accepted transient steps.
- Runtime profile analysis:
  `docs/project/RUNTIME_PROFILE_ANALYSIS_2026-04-26.md` records the clean
  full92 G-artifact timing profile and the discovered parallel-output isolation
  issue.
- Parallel H smoke:
  `results/smoke-signature-H-parallel-2026-04-26/summary.json`
  produced `tasks=3`, `eligible=3`, `rescued=3`, `best_pass=3`.

## Next Speedups

1. Add `--only-failed-from <result-root>` and `--only-signature-eligible` convenience filters.
2. Add a small report script to rank tasks by `evas_timing.total_elapsed_s` and timeout frequency.
3. Build checker-specific early-exit readers for high-row-count CSVs after comparing against gold.
4. Consider a two-pass timeout profile: short exploratory timeout for template discovery, full timeout for final reported matrix.
