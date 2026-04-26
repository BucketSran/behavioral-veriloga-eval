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
- `datasets/failure_sets/H2_ON_F_FAILURE33_V2_2026-04-26`
- `datasets/failure_sets/H2_ON_F_FAILURE33_V3_2026-04-26`
- `datasets/failure_sets/H2_ON_F_FAILURE33_V4_2026-04-26`
- `datasets/failure_sets/H2_ON_F_FAILURE33_V5_STREAMING_2026-04-26`

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

### E4: H2 v2 TB Syntax + Combined DUT/TB Repair

Additional TB/harness syntax rewrites:

- `inst n1 n2 module params` -> `inst (n1 n2) module params`.
- `vsource name (p n) vdc=x` -> `name (p n) vsource dc=x`.
- Verilog named-port instance blocks `module inst (.PORT(node)) params` -> Spectre positional instance using the DUT module port order.

Additional combined DUT transfer:

- `parameter_type_override_smoke` uses the previously validated `periodic_parameterized_pulses` DUT template plus the flat-instance TB repair.

Result on the same 33-task failure set:

| Metric | Value |
|---|---:|
| Failure-set Pass@1 | 6/33 |
| Method-counted robust rescues | 5 |
| Flaky timeout recovery | 1 |

Formal pass movements:

| Task | Counted as H2 method gain? | Repair mode |
|---|---|---|
| `flash_adc_3b_smoke` | Yes | H DUT + TB `alter` inline + instance syntax + edge budget. |
| `serializer_frame_alignment_smoke` | Yes | TB stop/window repair. |
| `nrz_prbs` | Yes | DUT PRBS/LFSR sequence template. |
| `parameter_type_override_smoke` | Yes | DUT parameterized pulse template + TB flat-instance syntax repair. |
| `timer_absolute_grid_smoke` | Yes | TB reversed-vsource + named-port instance repair. |
| `final_step_file_metric_smoke` | No | Flaky timeout recovery; original H1 artifact also passes on serial rerun. |

### E5: H2 v3 General TB Normalization Probe

Additional generated-testbench normalization was tested on the same 33-task
failure anchor, using H2 v2 artifacts as the base so previously rescued DUT/TB
pairs were preserved.

New generic TB rewrites:

- `Vx p n vsource ...` -> `Vx (p n) vsource ...`.
- `vtype=` -> `type=` and `vdc=` -> `dc=`.
- Pair-block instance syntax such as `module inst ( port node ... )` -> Spectre
  positional instance using the node column.

Result:

| Metric | H2 v2 | H2 v3 |
|---|---:|---:|
| Failure-set Pass@1 | 6/33 | 6/33 |
| Remaining formal failures | 27 | 27 |
| `tb_stimulus_or_observable` failures | 3 | 0 |
| `checker_runtime_or_complex_behavior` failures | 8 | 10 |

Interpretation:

- No new formal PASS was produced.
- The change is still diagnostically useful: `bbpd_data_edge_alignment_smoke`
  moved from `too_few_data_edges=0` to `lag_window_updn=8/0`, so the generated
  TB now exercises the phase detector enough to expose behavior-level mismatch.
- `gray_counter_one_bit_change_smoke` and `dwa_wraparound_smoke` moved from
  missing stimulus/sample signatures into `behavior_eval_timeout`, indicating
  that the remaining blocker is no longer obvious TB syntax.

### E6: Streaming-Checker Diagnostic Probe

Streaming checkers remain disabled by default in the formal scorer. A diagnostic
run enabled them only on a 7-task timeout-heavy subset to estimate how many
failures are checker-efficiency artifacts rather than circuit failures.

Result directory:

- `results/latest-system-score-condition-H2-v3-streaming-diagnostic-kimi-2026-04-26`

| Task | Diagnostic result | Note |
|---|---|---|
| `pfd_deadzone_smoke` | PASS | `streaming_checker:up_frac=0.0040 dn_frac=0.0000 up_pulses=30`; this matches older non-timeout PASS notes and is likely a checker efficiency false failure in current formal scoring. |
| `pfd_reset_race_smoke` | FAIL | `up_second=0.8000`, so this remains a real timing-window behavior failure. |
| `sar_adc_dac_weighted_8b_smoke` | FAIL | `unique_codes=1 avg_abs_err=0.1881 vout_span=0.000`; real behavior failure plus expensive CSV. |
| `digital_basics_smoke` | FAIL | `invert_match_frac=0.465`; real logic/multi-module mismatch. |
| `dwa_ptr_gen_no_overlap_smoke` | FAIL | `max_active_cells=0` in H2 v3 formal artifact; generated formal pair is not behaving like the gold-harness template pass. |
| `gray_counter_one_bit_change_smoke` | FAIL | Still uses the non-streaming checker and times out; needs a dedicated fast checker or formal TB transfer repair. |
| `dwa_wraparound_smoke` | FAIL | Still uses the non-streaming checker and times out; needs checker/runtime profiling before behavior repair. |

Decision:

- Do not promote streaming checkers globally yet.
- Treat `pfd_deadzone_smoke` as the first candidate for a validated fast-checker
  path because historical non-streaming results and streaming notes agree.

### E7: H2 v4 Template Transfer Probe

A small DUT-template probe was run on failure-set tasks with existing reusable
mechanism templates, using H2 v3 as the anchor and the benchmark gold harness
for validation.

Probe result:

| Metric | Value |
|---|---:|
| Tasks | 6 |
| Baseline PASS under gold harness | 2/6 |
| Best template PASS under gold harness | 5/6 |
| Improved tasks | 3/6 |

Gold-harness outcomes:

| Task | Best outcome | Interpretation |
|---|---|---|
| `bad_bus_output_loop` | PASS with `independent_bus_bit_outputs` | DUT template is transferable; formal generated scoring also passes. |
| `dwa_ptr_gen_smoke` | PASS with DWA pointer template | Gold-harness DUT template works, but formal artifact still lacks a generated testbench, so this is not yet a formal rescue. |
| `dwa_ptr_gen_no_overlap_smoke` | PASS with no-overlap DWA template | DUT template works under gold harness, but formal generated TB/checker transfer still fails. |
| `gray_counter_one_bit_change_smoke` | Baseline already PASS under gold harness | Formal failure is generated-TB/checker transfer, not DUT behavior. |
| `dac_therm_16b_smoke` | Baseline already PASS under gold harness | Formal failure is generated-TB/checker transfer, not DUT behavior. |
| `pfd_reset_race_smoke` | EVAS timeout for all candidates | Needs runtime/checker/harness optimization before template comparison is meaningful. |

The transferable `bad_bus_output_loop` DUT template was then copied back into a
formal H2 v4 generated tree and scored on the same 33-task failure anchor.

Formal result:

| Metric | H2 v3 | H2 v4 |
|---|---:|---:|
| Failure-set Pass@1 | 6/33 | 7/33 |
| Remaining formal failures | 27 | 26 |
| Method-counted robust rescues | 5 | 6 |

New formal rescue:

| Task | Repair mode | Formal note |
|---|---|---|
| `bad_bus_output_loop` | DUT bugfix template transfer | `mismatch_frac=0.0000 code_patterns=16 dout_patterns=16 uniform_frac=0.155 stable_rows=2181` |

### E8: H2 v5 Fast-Checker Candidate Variant

This is **not** the default formal H2 score. It is an explicit candidate variant
to test whether the current H2 ceiling is being hidden by generated-TB interface
breakage and checker timeout.

Changes relative to H2 v4:

- Copy the gold-harness-passing `dwa_rotating_pointer_no_overlap` DUT template
  into the formal `dwa_ptr_gen_no_overlap_smoke` artifact.
- Apply the generic positional-instance prefix repair:
  `prepend_missing_instance_ports=dwa_ptr_gen_no_overlap:dut:clk_i,rst_ni`.
- Enable the existing streaming checkers for this diagnostic run only.

Result:

| Metric | H2 v4 default formal | H2 v5 fast-checker candidate |
|---|---:|---:|
| Failure-set Pass@1 | 7/33 | 9/33 |
| Remaining formal failures | 26 | 24 |

New candidate rescues:

| Task | Required layers | Evidence |
|---|---|---|
| `dwa_ptr_gen_no_overlap_smoke` | DUT no-overlap template + generated-TB port-prefix repair + fast checker | `sampled_cycles=17 bad_ptr_rows=0 max_active_cells=14 overlap_count=0`. |
| `pfd_deadzone_smoke` | Fast checker only | `up_frac=0.0040 dn_frac=0.0000 up_pulses=30`; no DUT/TB rewrite was needed. |

Interpretation:

- `dwa_ptr_gen_no_overlap_smoke` demonstrates a three-layer failure: the DUT
  template alone is insufficient, the generated TB was also missing `clk_i` and
  `rst_ni` at the front of a scalarized positional instance, and the default
  Python checker times out on the large CSV.
- `pfd_deadzone_smoke` is likely not a repair-policy failure. It is a checker
  throughput failure under the latest formal scorer because older non-timeout
  results and streaming notes agree on the same PASS-level metrics.
- V5 should be treated as a method-development upper-bound candidate until the
  fast checkers are validated and promoted out of the experimental path.

## Rejected / Not Yet Formalized

| Candidate | Outcome | Decision |
|---|---|---|
| Broad stop extension for any pulse source | Wasted runtime on `dac_therm_16b_smoke` without pass | Rejected; replaced by signature-gated stop extension. |
| `parameter_type_override_smoke` DUT template alone | Gold-harness PASS but formal generated TB still FAIL | Promoted only after combined DUT+TB repair in E4. |
| `dac_therm_16b_smoke` instance rewrite | Output became active but formal still FAIL | Keep as diagnostic progress, not rescue. |
| `final_step_file_metric_smoke` PASS | Original H1 also passes on serial rerun | Mark as flaky timeout, not method gain. |

## Current Interpretation

H2 has now demonstrated real value on the failure set, but not yet enough for full92 claims:

- TB/harness repair can rescue formal failures that H1 could not transfer (`flash_adc_3b_smoke`).
- Stop/window repair can rescue at least one formal sequence task (`serializer_frame_alignment_smoke`).
- DUT mechanism templates can transfer when the generated/formal harness is compatible (`nrz_prbs`).
- DUT and TB repair sometimes must be combined; `parameter_type_override_smoke` fails if either layer is left unfixed.
- Some gold-harness successes still do not transfer because the generated TB remains wrong (`dac_therm_16b_smoke`).
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
