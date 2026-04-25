# Condition-A Failure Repair Analysis

Date: `2026-04-25`

Model: `kimi-k2.5`

Scope: all `56` tasks that failed the full92 condition-A raw-prompt run.

Baseline root:

- `results/evas-scoring-condition-A-kimi-k2.5-full86-2026-04-25-overnight-kimi`

Repair result roots:

- `results/a-failed-hard16-kimi-v10policy-2026-04-25`
- `results/a-failed-heldout20-kimi-layered-v10policy-2026-04-25`
- `results/a-failed-remaining21-kimi-layered-v10policy-2026-04-25`

## Summary

| Split | Repair setting | PASS | Notes |
|---|---|---:|---|
| `A failed ∩ Hard16` | v10 candidate reuse plus adaptive repair | `12/15` | In-domain rescue check; do not use as held-out generalization evidence. |
| `A failed - Hard16` heldout20 | generic adaptive layered repair | `6/20` | No Hard16 candidate memory. |
| `A failed - Hard16` remaining21 | generic adaptive layered repair | `10/21` | No Hard16 candidate memory. |
| All condition-A failures | combined above | `28/56` | `33/56` tasks improved by failure layer. |

Final status distribution:

| Final status | Count |
|---|---:|
| `PASS` | `28` |
| `FAIL_SIM_CORRECTNESS` | `26` |
| `FAIL_DUT_COMPILE` | `2` |

Failure-layer transitions:

| Initial A status | Final status | Count |
|---|---|---:|
| `FAIL_DUT_COMPILE` | `FAIL_DUT_COMPILE` | `2` |
| `FAIL_DUT_COMPILE` | `FAIL_SIM_CORRECTNESS` | `4` |
| `FAIL_DUT_COMPILE` | `PASS` | `14` |
| `FAIL_INFRA` | `FAIL_SIM_CORRECTNESS` | `1` |
| `FAIL_INFRA` | `PASS` | `2` |
| `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | `21` |
| `FAIL_SIM_CORRECTNESS` | `PASS` | `11` |
| `FAIL_TB_COMPILE` | `PASS` | `1` |

## Remaining Error Categories

| Category | Count | Interpretation |
|---|---:|---|
| PLL feedback/lock/timing behavior | `6` | Generated model runs, but feedback edges, frequency ratio, or lock timing are wrong. |
| Event crossing or transition timing behavior | `5` | Output timing/window semantics do not match checker expectations. |
| Digital sequence or encoding behavior | `4` | Sequence toggling, encoding, or complement behavior is wrong. |
| Checker timeout or pathological CSV | `3` | Simulation returns CSV, but Python-side behavior evaluation times out. |
| Phase-detector pulse timing behavior | `2` | UP/DN pulses are missing or insufficient. |
| Spectre compile or unsupported syntax | `2` | Repair still emits Spectre-unfriendly constructs or uncompilable DUT. |
| Divider ratio dynamic behavior | `2` | Divider toggles, but ratio/switching dynamics are wrong. |
| Runtime or observable CSV missing | `2` | Simulation exits with missing `tran.csv`. |
| Multi-module ADC code-path behavior | `1` | ADC/DAC path runs but output code coverage is stuck. |
| Calibration behavior | `1` | Calibration output does not move or settle as expected. |

## Remaining Failures

| Task | A status | Final status | Category | Key evidence |
|---|---|---|---|---|
| `adpll_timer_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `ref=250`, `fb=0` |
| `pfd_reset_race_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Phase-detector pulse timing behavior | `up_first=0`, `dn_first=0`, `up_pulses_first=0` |
| `sar_adc_dac_weighted_8b_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Multi-module ADC code-path behavior | `unique_codes=1`, `vout_span=0` |
| `adpll_lock_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `ref=250`, `fb=0` |
| `adpll_ratio_hop_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `num=0`, `den=200` |
| `bbpd_data_edge_alignment_smoke` | `FAIL_INFRA` | `FAIL_SIM_CORRECTNESS` | Phase-detector pulse timing behavior | `too_few_updn_pulses=2` |
| `cppll_freq_step_reacquire_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `pre_lock_edges=0`, `post_lock_edges=0` |
| `cross_hysteresis_window_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Event crossing or transition timing behavior | window levels wrong |
| `cross_interval_163p333_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Event crossing or transition timing behavior | `seen_out_never_high=0` |
| `cross_sine_precision_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Event crossing or transition timing behavior | crossing count too low |
| `dff_rst_smoke` | `FAIL_DUT_COMPILE` | `FAIL_SIM_CORRECTNESS` | Checker timeout or pathological CSV | `behavior_eval_timeout>20s` |
| `multimod_divider_ratio_switch_smoke` | `FAIL_DUT_COMPILE` | `FAIL_DUT_COMPILE` | Spectre compile or unsupported syntax | `conditional_transition` |
| `d2b_4bit` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Digital sequence or encoding behavior | dynamic monotonic code check failed |
| `bg_cal` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Calibration behavior | `code_span=0`, `settled_high=False` |
| `clk_divider` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Divider ratio dynamic behavior | `ratio_code=5`, `out_edges=13`, `period_match=0` |
| `multimod_divider` | `FAIL_DUT_COMPILE` | `FAIL_SIM_CORRECTNESS` | Divider ratio dynamic behavior | `base=4`, `pre_count=6`, `post_count=5` |
| `bad_bus_output_loop` | `FAIL_DUT_COMPILE` | `FAIL_SIM_CORRECTNESS` | Checker timeout or pathological CSV | `behavior_eval_timeout>20s` |
| `digital_basics_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Digital sequence or encoding behavior | `invert_match_frac=0` |
| `final_step_file_metric_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Runtime or observable CSV missing | `returncode=1`, `tran.csv missing` |
| `lfsr_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Digital sequence or encoding behavior | `transitions=0`, `hi_frac=0` |
| `phase_accumulator_timer_wrap_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Event crossing or transition timing behavior | phase wrap behavior still wrong |
| `sample_hold_smoke` | `FAIL_DUT_COMPILE` | `FAIL_SIM_CORRECTNESS` | Checker timeout or pathological CSV | `behavior_eval_timeout>20s` |
| `simultaneous_event_order_smoke` | `FAIL_DUT_COMPILE` | `FAIL_DUT_COMPILE` | Spectre compile or unsupported syntax | `dut_not_compiled`, `tran.csv missing` |
| `transition_branch_target_smoke` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Event crossing or transition timing behavior | all checked means remain `0` |
| `adpll_timer` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `late_edge_ratio=0.76`, `lock_time=nan` |
| `cppll_timer` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | PLL feedback/lock/timing behavior | `freq_ratio=0.375`, `lock_time=nan` |
| `multitone` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Runtime or observable CSV missing | `returncode=1`, `tran.csv missing` |
| `nrz_prbs` | `FAIL_SIM_CORRECTNESS` | `FAIL_SIM_CORRECTNESS` | Digital sequence or encoding behavior | `transitions=0`, `complement_err=0.9` |

## Takeaway

The adaptive EVAS loop is already effective at repairing condition-A raw-prompt failures: it rescues
half of the failed tasks and moves many compile/infra failures into behavior-level evidence. The
remaining bottleneck is no longer mostly CSV observability. It is dominated by behavior-policy gaps:
PLL feedback/lock structure, event-crossing timing windows, phase-detector pulse generation, divider
ratio dynamics, and stable digital sequence generation.

The next optimization should focus on conservative behavior-only repair that preserves a compilable
candidate, plus targeted skeletons for PLL feedback loops, crossing windows, and sequence/divider
state machines.

## Follow-Up: High-Level Template v11

After this analysis, a high-level conservative behavior-only and metric-to-mechanism prompt layer was
tested on the `28` remaining failures:

- Result root: `results/a-failed-remaining28-kimi-high-template-v11-2026-04-25`
- New PASS: `bbpd_data_edge_alignment_smoke`
- Net remaining failures changed from `28` to `27`
- Generated round-1 regressions were observed before best-so-far rejection:
  `bad_bus_output_loop`, `cppll_timer`, `clk_divider`, `pfd_reset_race_smoke`,
  and `cross_sine_precision_smoke`

Interpretation: the metric-to-mechanism template can help when the EVAS metric maps cleanly to a
repairable mechanism, such as `too_few_updn_pulses` to BBPD/PFD pulse generation. However, prompt-only
conservative wording does not reliably prevent the model from breaking compile/interface layers during
hard behavior repair. The next policy improvement should move anti-regression from text guidance into
runner behavior: reject or auto-repair any behavior-layer candidate whose compile/TB/runtime layer gets
worse, and retry with a narrower patch-style prompt that preserves the previous candidate structure.

## Follow-Up: Observation Policy v13

A circuit-name-agnostic observation policy was added in `runners/observation_repair_policy.py`. It
classifies EVAS notes and metrics into generic failure patterns rather than task-specific circuit
families.

Probe result:

- Result root: `results/observation-policy5-kimi-v13-2026-04-25`
- Tasks: `lfsr_smoke`, `clk_divider`, `pfd_reset_race_smoke`,
  `sar_adc_dac_weighted_8b_smoke`, `final_step_file_metric_smoke`
- Final PASS: `0/5`
- Prompt classification examples:
  `lfsr_smoke -> stuck_or_wrong_digital_sequence`,
  `clk_divider -> wrong_event_cadence_or_edge_count`,
  `pfd_reset_race_smoke -> missing_or_wrong_pulse_window`,
  `sar_adc_dac_weighted_8b_smoke -> low_code_coverage_or_stuck_code_path`
- New candidate regressions still appeared for `pfd_reset_race_smoke` and `clk_divider`

Interpretation: observation-driven classification is the right abstraction for generality, but it is
still only a prompt-level intervention. It did not solve the core failure mode: free-form repair can
still rewrite too much and break compile/interface layers. The next method should use the observation
policy to select a constrained patch region, then mechanically preserve the rest of the candidate.
