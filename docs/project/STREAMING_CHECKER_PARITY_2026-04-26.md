# Streaming Checker Parity Proof

Date: 2026-04-26

## Question

Can the experimental streaming checkers be treated as formal scoring
equivalents of the existing row-based checkers?

## Proof Standard

A streaming checker can be promoted only when it satisfies both conditions:

1. On the same `tran.csv`, the default checker and streaming checker return the
   same pass/fail score whenever the default checker completes.
2. Large real-result CSVs may show default-checker timeouts, but timeout rows
   are not counted as parity evidence.

## Implementation

Added `runners/check_streaming_checker_parity.py`.

The script runs both paths in isolated child processes:

- default path: `VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS` unset
- streaming path: `VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS=1`

It writes `parity.csv`, `parity.json`, and `README.md` under the selected result
directory.

## Fixture Parity

Command:

```bash
python3 runners/check_streaming_checker_parity.py \
  --fixture-suite \
  --output-dir results/streaming-checker-parity-fixtures-2026-04-26 \
  --original-timeout-s 20 \
  --streaming-timeout-s 20
```

Result:

| Metric | Value |
|---|---:|
| Cases | 20 |
| Comparable cases | 20 |
| Matches | 20 |
| Mismatches | 0 |
| Original timeouts | 0 |

Covered checker tasks:

- `pfd_deadzone_smoke`
- `pfd_reset_race_smoke`
- `dac_binary_clk_4b_smoke`
- `sar_adc_dac_weighted_8b_smoke`
- `dwa_ptr_gen_no_overlap_smoke`
- `digital_basics_smoke`
- `gray_counter_one_bit_change_smoke`
- `dwa_wraparound_smoke`
- `gain_extraction_smoke`
- `multimod_divider_ratio_switch_smoke`

During fixture parity, an initial mismatch was found in
`gray_counter_one_bit_change_smoke`: the streaming checker sampled one row
earlier than the default checker. This was fixed by aligning the streaming
settle offset with the default `edge_idx + 8` sampling rule.

## Real-CSV Smoke Parity

Command:

```bash
python3 runners/check_streaming_checker_parity.py \
  --result-root results/h2-v3-template-probe-failure-subset-kimi-2026-04-26 \
  --result-root results/latest-system-score-condition-H2-on-F-failure33-v7-streaming-kimi-2026-04-26 \
  --output-dir results/streaming-checker-parity-smoke-2026-04-26 \
  --max-cases-per-task 3 \
  --original-timeout-s 20 \
  --streaming-timeout-s 20 \
  --task pfd_deadzone_smoke \
  --task pfd_reset_race_smoke \
  --task gray_counter_one_bit_change_smoke \
  --task gain_extraction_smoke \
  --task dwa_ptr_gen_no_overlap_smoke \
  --task dwa_wraparound_smoke \
  --task multimod_divider_ratio_switch_smoke
```

Result:

| Metric | Value |
|---|---:|
| Cases | 13 |
| Comparable cases | 2 |
| Matches | 2 |
| Mismatches | 0 |
| Original timeouts | 11 |

Interpretation:

- No mismatch was observed where the default checker completed.
- Most large real CSVs still time out on the default row-based checker, so they
  are throughput evidence, not direct parity evidence.

## H2 Impact After Parity Fix

Re-scored the H2 v7 streaming candidate after the Gray parity fix:

```bash
VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS=1 python3 runners/score.py \
  --model kimi-k2.5 \
  --generated-dir generated-condition-H2-on-F-failure33-v5-streaming-kimi-2026-04-26 \
  --output-dir results/latest-system-score-condition-H2-on-F-failure33-v7-streaming-parityfix-kimi-2026-04-26 \
  --timeout-s 160 \
  --workers 8 \
  --save-policy contract \
  --task <33 H-on-F failures>
```

Result:

| Metric | Pre-parity H2 v7 | Parity-fixed H2 v7 |
|---|---:|---:|
| Failure-set Pass@1 | 11/33 | 10/33 |
| Pass@1 rate | 0.3333 | 0.3030 |

The dropped pass is `final_step_file_metric_smoke`, which is the already-known
flaky timeout case. It now reports `behavior_eval_timeout>53s`. The core
fast-checker rescues still hold: `dwa_ptr_gen_no_overlap_smoke`,
`pfd_deadzone_smoke`, `gray_counter_one_bit_change_smoke`, and
`gain_extraction_smoke` remain PASS under the parity-fixed checker code.

## Decision

The streaming checkers are now parity-tested on synthetic fixtures and have no
observed mismatch on comparable real CSVs. The conservative paper-facing result
should use the parity-fixed H2 v7 score, not the earlier pre-parity `11/33`
number. Remaining risk is real-CSV coverage: many default checkers time out, so
large-file equivalence cannot be exhaustively proven without either stronger
sampling fixtures or a slower no-timeout audit.
