# H2 Layered Repair Experiments: Failure-Set Anchor

Date: 2026-04-26

## Goal

Test H2 on the current `H-on-F-stable` failure set only, without running full92.
H2 is defined as layered repair after failure classification:

1. classify the failure layer;
2. apply only the matching repair executor;
3. re-score with EVAS formal scoring;
4. keep successful executors, record rejected/flaky outcomes explicitly.

Source failure dataset:

- `datasets/failure_sets/H_ON_F_STABLE_2026-04-26`
- 33 Pass@1 failures from `results/latest-system-score-condition-H-on-F-kimi-2026-04-26-stable`

Output failure datasets:

- `datasets/failure_sets/H2_ON_F_FAILURE33_2026-04-26`
- `datasets/failure_sets/H2_ON_F_FAILURE33_PLUS_DUTPROBE_2026-04-26`

## Implemented Executors

### TB stimulus / harness executor

Implemented in `runners/materialize_condition_h.py` behind explicit options.

Safe rewrites:

- Inline simple generated-testbench `alter SRC type=pwl|pulse ...` statements into the original `vsource` line.
- Rewrite simple Verilog-style instances `module inst (...)` into Spectre style `inst (...) module` only when `module` appears in an `ahdl_include`.
- Extend `tran stop` only when the base failure notes contain edge/sample-budget signatures such as `too_few_edges`, `not_enough_clk_edges`, `too_few_data_edges`, `insufficient_post_reset_samples`, or `clk_edges=`.

Guardrail:

- Stop-time extension is no longer applied to every pulse source. The first broad version extended `dac_therm_16b_smoke` from `2us` to `50us`; this was rejected as too broad and replaced with signature-gated extension.

### DUT template probe

Exploratory only. Existing bounded mechanism templates were tested on a small DUT-only subset with gold/reference harness first, then transferred back to formal generated artifacts when promising.

## Experiments

### E1: H2 TB/Harness Repair On Failure33

Command family:

```bash
python3 runners/materialize_condition_h.py \
  --model kimi-k2.5 \
  --base-generated-root generated-table2-evas-guided-repair-3round \
  --base-score-root results/latest-system-score-condition-F-bestround-kimi-2026-04-26-stable \
  --h-summary-root results/signature-guided-H-Gfailed-eligible4-fixed-checker-2026-04-26 \
  --output-generated-root generated-condition-H2-on-F-failure33-kimi-2026-04-26 \
  --tb-repair-scope all \
  --task <33 H-on-F failures>

python3 runners/score.py \
  --model kimi-k2.5 \
  --generated-dir generated-condition-H2-on-F-failure33-kimi-2026-04-26 \
  --output-dir results/latest-system-score-condition-H2-on-F-failure33-kimi-2026-04-26 \
  --workers 4 \
  --save-policy contract \
  --timeout-s 160 \
  --task <33 H-on-F failures>
```

Result:

| Metric | Value |
|---|---:|
| Failure-set tasks | 33 |
| H-applied DUT replacements | 1 |
| Effective TB repairs | 5 |
| Pass@1 on failure set | 2/33 |

Rescued tasks:

| Task | Repair path | Why it passed |
|---|---|---|
| `flash_adc_3b_smoke` | H DUT replacement + TB stimulus/instance repair | `alter` sources were inlined, Verilog-style instance was rewritten, stop time was extended; formal note became `codes=8/8 reversals=0`. |
| `serializer_frame_alignment_smoke` | TB stop-window repair | Existing generated DUT/TB became formally observable after `tran stop` extension; formal note became `mismatch_total=0`. |

Progress but not pass:

| Task | Movement | Interpretation |
|---|---|---|
| `dac_therm_16b_smoke` | `max_vout=0.000` -> `max_vout=16.000` | Instance syntax repair connected the DUT, but generated TB stimulus still differs from the reference harness; not a formal rescue. |

### E2: DUT Mechanism Template Probe

Gold/reference-harness probe on a small DUT-only subset:

```bash
python3 runners/template_guided_smallset.py \
  --anchor-root generated-condition-H2-on-F-failure33-kimi-2026-04-26/kimi-k2.5 \
  --generated-root generated-h2-dut-template-probe-failure33-kimi-2026-04-26 \
  --output-root results/h2-dut-template-probe-failure33-kimi-2026-04-26 \
  --timeout-s 160 \
  --tasks dac_therm_16b_smoke nrz_prbs parameter_type_override_smoke serializer_frame_alignment_smoke
```

Probe result:

| Task | Gold-harness best | Transfer status |
|---|---|---|
| `nrz_prbs` | PASS with `timer_lfsr_differential_prbs` | Formal PASS after DUT replacement. |
| `parameter_type_override_smoke` | PASS with `periodic_parameterized_pulses` | Formal FAIL; generated TB still produces `pulses=0 peak=0.000`. |
| `dac_therm_16b_smoke` | Baseline PASS under gold harness | Formal generated TB still FAIL; classify as formal-transfer/TB mismatch, not DUT rescue. |
| `serializer_frame_alignment_smoke` | Baseline already PASS after H2 TB repair | Already counted in E1. |

### E3: H2 Failure33 Plus Transferable DUT Probe

Formal scoring after adding the transferable `nrz_prbs` DUT template to E1 artifacts:

```bash
python3 runners/score.py \
  --model kimi-k2.5 \
  --generated-dir generated-condition-H2-on-F-failure33-plus-dutprobe-kimi-2026-04-26 \
  --output-dir results/latest-system-score-condition-H2-on-F-failure33-plus-dutprobe-kimi-2026-04-26 \
  --workers 4 \
  --save-policy contract \
  --timeout-s 160 \
  --task <33 H-on-F failures>
```

Result:

| Metric | Value |
|---|---:|
| Failure-set Pass@1 | 4/33 |
| Method-counted robust rescues | 3 |
| Flaky timeout recovery | 1 |

Formal pass movements:

| Task | Counted as H2 method gain? | Reason |
|---|---|---|
| `flash_adc_3b_smoke` | Yes | H DUT + TB stimulus/instance repair. |
| `serializer_frame_alignment_smoke` | Yes | TB stop-window repair. |
| `nrz_prbs` | Yes | DUT sequence/LFSR template transfers to formal score. |
| `final_step_file_metric_smoke` | No | No H2 repair was applied; original H1 artifact also passes when re-scored serially, so this is a checker-timeout/flakiness recovery. |

## Rejected / Not Yet Formalized

| Candidate | Outcome | Decision |
|---|---|---|
| Broad stop extension for any pulse source | Wasted runtime on `dac_therm_16b_smoke` without pass | Rejected; replaced by signature-gated stop extension. |
| `parameter_type_override_smoke` DUT template | Gold-harness PASS but formal generated TB still FAIL | Not counted; needs TB/formal-transfer repair. |
| `dac_therm_16b_smoke` instance rewrite | Output became active but formal still FAIL | Keep as diagnostic progress, not rescue. |
| `final_step_file_metric_smoke` PASS | Original H1 also passes on serial rerun | Mark as flaky timeout, not method gain. |

## Current Interpretation

H2 has now demonstrated real value on the failure set, but not yet enough for full92 claims:

- TB/harness repair can rescue formal failures that H1 could not transfer (`flash_adc_3b_smoke`).
- Stop/window repair can rescue at least one formal sequence task (`serializer_frame_alignment_smoke`).
- DUT mechanism templates can transfer when the generated/formal harness is compatible (`nrz_prbs`).
- Some gold-harness successes do not transfer because the generated TB remains wrong (`parameter_type_override_smoke`, `dac_therm_16b_smoke`).
- Timeout failures must be treated carefully because some recover on rerun without any repair.

## 2x2 Isolation Probe

Implemented `runners/layered_isolation_probe.py` to automate:

1. generated DUT + generated TB;
2. generated DUT + gold TB;
3. gold DUT + generated TB.

Probe command:

```bash
python3 runners/layered_isolation_probe.py \
  --model kimi-k2.5 \
  --generated-dir generated-condition-H2-on-F-failure33-plus-dutprobe-kimi-2026-04-26 \
  --output-dir results/h2-layered-isolation-probe-2026-04-26 \
  --timeout-s 120 \
  --workers 2 \
  --task flash_adc_3b_smoke \
  --task parameter_type_override_smoke \
  --task dac_therm_16b_smoke \
  --task nrz_prbs \
  --task serializer_frame_alignment_smoke \
  --task timer_absolute_grid_smoke
```

Layer counts:

| Layer | Count |
|---|---:|
| `already_pass` | 2 |
| `tb_or_harness` | 3 |
| `dut_confirmed_with_gold_harness` | 1 |

Key isolation conclusions:

| Task | Isolation result | Meaning |
|---|---|---|
| `flash_adc_3b_smoke` | generated/generated PASS; generated/gold PASS; gold/generated PASS | H2 repaired both the H1 DUT-transfer gap and generated TB enough for formal pass. |
| `serializer_frame_alignment_smoke` | generated/generated PASS; generated/gold PASS; gold/generated FAIL | The repaired generated pair is internally valid, but generated TB is not a universal harness for the gold DUT. |
| `nrz_prbs` | spec-to-va generated DUT + gold TB PASS | DUT template repair is confirmed under the benchmark harness. |
| `parameter_type_override_smoke` | generated DUT + gold TB PASS; gold DUT + generated TB FAIL | Remaining failure is generated TB/harness, not DUT. |
| `dac_therm_16b_smoke` | generated DUT + gold TB PASS; gold DUT + generated TB FAIL | Remaining failure is generated TB/formal-transfer, not DUT. |
| `timer_absolute_grid_smoke` | generated DUT + gold TB PASS; gold DUT + generated TB FAIL | Remaining failure is generated TB/harness. |

Next recommended step:

1. Use the 2x2 isolation result to route `parameter_type_override_smoke`, `dac_therm_16b_smoke`, and `timer_absolute_grid_smoke` into TB/harness repair instead of DUT repair.
2. Promote only repair executors that rescue more than one task or have a clear mechanistic transfer story.
3. Keep full92 disabled until H2 reaches a stronger failure-set result with low flakiness.
