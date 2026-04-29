# ADC System Decomposition

Date: 2026-04-27

This note records the ADC-side version of the system-contract idea that was
useful for PLL closure. The goal is not to write one contract per task name.
The goal is to describe reusable internal relations that can be matched from a
prompt, waveform saves, or available gold examples.

## Decomposition

| Subsystem | Common signals | Failure signature | Repair direction |
|---|---|---|---|
| Sample / hold | `vin`, `vin_sh`, `clk`, `clks`, `phi1`, `phi2` | No sample/update edges, wrong sampling phase, held input | Fix clock edge sense, reset release, or sample phase |
| Quantizer | `DOUT[*]`, `dout_*`, `dout_code` | Stuck code or low unique-code count | Fix thresholds, clamping, reset gating, or bit extraction |
| SAR controller | `DP_DAC[*]`, `DM_DAC[*]`, `CMPCK`, `RDY`, `EOC` | Bit trials absent, ready never asserts | Fix FSM progress, comparator-read cadence, done flag |
| DAC / CDAC reconstruction | `vout`, `aout`, `VDAC_P`, `VDAC_N` | Flat output, wrong span, large input-output error | Fix bit order, reference scale, differential polarity |
| Pipeline residue / MDAC | `vres`, `residue` | Residue flat or unbounded | Fix sub-ADC decision regions and residue equation |
| Calibration / trim | `TRIM_code`, `CAL*`, trim buses | Static trim, no settled flag | Fix accumulator/control update and exposed status |

## Implemented Graph

`docs/SYSTEM_CONTRACT_GRAPHS.json` now includes `adc_data_converter_v0`.
It checks:

- sampling/update clock liveness;
- quantizer code coverage;
- ADC-DAC reconstruction error;
- DAC/reconstruction output span;
- ready/end/settled flag assertion;
- SAR/calibration control activity;
- pipeline residue activity;
- differential DAC/CDAC output span.

The graph uses signal aliases such as `vin_sh/vin/VIN/VINP`,
`clks/clk/CLK/CLKS/phi1/phi2`, `vout/aout/VOUT/VDAC_P`, and
`rdy/RDY/eoc/EOC/SETTLED`. Missing optional subsystems are skipped rather than
failed, so a pure DAC is not punished for lacking SAR internals.

## Validation

Command:

```bash
python3 runners/system_contract_graph.py --graph-id adc_data_converter_v0 \
  --out-root results/system-contract-graph-v1-adc-final-2026-04-27 \
  --case-label adc_dac_ideal --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/adc_dac_ideal_4b_smoke/result.json \
  --case-label sar_adc_dac --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/sar_adc_dac_weighted_8b_smoke/result.json \
  --case-label flash_adc --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/flash_adc_3b_smoke/result.json \
  --case-label dac_binary --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/dac_binary_clk_4b_smoke/result.json \
  --case-label sar_logic --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/sar_logic/result.json \
  --case-label pipeline_stage --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/pipeline_stage/result.json \
  --case-label cdac_cal --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/cdac_cal/result.json \
  --case-label segmented_dac --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/segmented_dac/result.json \
  --case-label bg_cal --result-json results/latest-system-score-r26-dwa-pfd-axisfix-admission-2026-04-27/bg_cal/result.json
```

Result: `9/9 PASS`.

Important metrics:

- `adc_dac_ideal`: 16 codes, reconstruction error `0.0413`, output span `0.844`.
- `sar_adc_dac`: 255 codes, reconstruction error `0.00174`, output span `0.896`.
- `pipeline_stage`: residue span `0.54`.
- `cdac_cal`: differential span `0.9`.
- `segmented_dac`: differential span `0.512`.
- `bg_cal`: 16 trim/control codes and settled/ready evidence.

## Gold Sweep

Command:

```bash
python3 runners/gold_mechanism_sweep.py --task sar_adc_dac_weighted_8b_smoke \
  --out-root results/gold-mechanism-sweep-sar-adc-roundtrip-v2-2026-04-27 \
  --timeout-s 45
```

Result: `4/5 PASS`.

The sweep perturbs only the input sine frequency in copied gold artifacts:

| Case | Status | Unique codes | Avg reconstruction error |
|---|---:|---:|---:|
| `fin_50k` | PASS | 128 | `0.00205` |
| `fin_100k_base` | PASS | 224 | `0.00216` |
| `fin_200k` | PASS | 131 | `0.00366` |
| `fin_500k` | PASS | 57 | `0.00819` |
| `fin_1m` | ERROR/timeout | 35 partial | `0.0155` partial |

This supports a reusable repair lesson: ADC success depends on the relation
between input movement and sample/update cadence. The loop should not only ask
"did the output toggle"; it should ask whether code coverage and reconstruction
remain plausible under the intended stimulus.
