# v3 Staged Promotion Gold Probe

Date: 2026-07-07

## Summary

- `gold_total`: 4
- `gold_pass`: 4
- `gold_fail`: 0
- `expectation_fail`: 0
- `skipped_staged_tasks`: 0
- `gold_wall_s_total`: 21.426399
- `gold_wall_s_max`: 18.589895
- `slow_gold_threshold_s`: 20.0
- `slow_gold_count`: 0
- `wall_s`: 145.286543

## Gold Timing Top 20

| Task | Status | Wall s |
| --- | --- | ---: |
| `505-fractional-n-divider-accumulator-flow` | `PASS` | 18.589895 |
| `502-sine-vco-idtmod-bound-step` | `PASS` | 1.2335 |
| `504-charge-pump-pfd-state-machine` | `PASS` | 0.877607 |
| `503-differential-vco-clip-idtmod` | `PASS` | 0.725397 |

## Rows

| Task | Status | First behavior note |
| --- | --- | --- |
| `502-sine-vco-idtmod-bound-step` | `PASS` |  |
| `502-sine-vco-idtmod-bound-step` | `FAIL_SIM_CORRECTNESS` | out@9.38889ns=0.0000 expected=0.7659 tol=0.0800 |
| `502-sine-vco-idtmod-bound-step` | `FAIL_SIM_CORRECTNESS` | metric@9.38889ns=0.0000 expected=0.3042 tol=0.0600 |
| `502-sine-vco-idtmod-bound-step` | `FAIL_SIM_CORRECTNESS` | out@9.38889ns=-0.4727 expected=0.7659 tol=0.0800 |
| `502-sine-vco-idtmod-bound-step` | `FAIL_SIM_CORRECTNESS` | out@8ns=0.1797 expected=0.8745 tol=0.0800 |
| `502-sine-vco-idtmod-bound-step` | `FAIL_SIM_CORRECTNESS` | out@9.38889ns=0.3829 expected=0.7659 tol=0.0800 |
| `503-differential-vco-clip-idtmod` | `PASS` |  |
| `503-differential-vco-clip-idtmod` | `FAIL_SIM_CORRECTNESS` | outp@10ns=0.4500 expected=0.0696 tol=0.0800 |
| `503-differential-vco-clip-idtmod` | `FAIL_SIM_CORRECTNESS` | metric@10ns=0.0000 expected=0.7200 tol=0.0600 |
| `503-differential-vco-clip-idtmod` | `FAIL_SIM_CORRECTNESS` | outp@10ns=0.8304 expected=0.0696 tol=0.0800 |
| `503-differential-vco-clip-idtmod` | `FAIL_SIM_CORRECTNESS` | outp@10ns=0.5736 expected=0.0696 tol=0.0800 |
| `503-differential-vco-clip-idtmod` | `FAIL_SIM_CORRECTNESS` | outm@10ns=0.0696 expected=0.8304 tol=0.0800 |
| `504-charge-pump-pfd-state-machine` | `PASS` |  |
| `504-charge-pump-pfd-state-machine` | `FAIL_SIM_CORRECTNESS` | vctrl_did_not_reach_top_rail late=0.4500 |
| `504-charge-pump-pfd-state-machine` | `FAIL_SIM_CORRECTNESS` | metric_no_positive_pulses hi_frac=0.000 |
| `504-charge-pump-pfd-state-machine` | `FAIL_SIM_CORRECTNESS` | vctrl_did_not_reach_top_rail late=0.4500 |
| `504-charge-pump-pfd-state-machine` | `FAIL_SIM_CORRECTNESS` | vctrl_did_not_reach_top_rail late=0.0500 |
| `504-charge-pump-pfd-state-machine` | `FAIL_SIM_CORRECTNESS` | vctrl_out_of_clamp min=0.4500 max=6.4500 |
| `505-fractional-n-divider-accumulator-flow` | `PASS` |  |
| `505-fractional-n-divider-accumulator-flow` | `FAIL_SIM_CORRECTNESS` | not_enough_edges ref=305 fb=0 dco=0 |
| `505-fractional-n-divider-accumulator-flow` | `FAIL_SIM_CORRECTNESS` | pre_lock_edges=0 disturb_lock_low_frac=0.000 post_lock_edges=0 late_freq_ratio=1.0205 dco_counts=[16, 15, 15, 15, 16, 15, 15, 15] avg_dco_per_fb=15.250 vctrl_min=0.425 vctrl_max=0.479 vctrl_span=0.054 |
| `505-fractional-n-divider-accumulator-flow` | `FAIL_SIM_CORRECTNESS` | dco_edges_per_fb_period_out_of_range avg=17.250 counts=[17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18, 17, 17, 17, 18] |
| `505-fractional-n-divider-accumulator-flow` | `FAIL_SIM_CORRECTNESS` | pre_lock_edges=5 disturb_lock_low_frac=0.767 post_lock_edges=4 late_freq_ratio=1.0230 dco_counts=[16, 15, 15, 15, 16, 15, 15, 15] avg_dco_per_fb=15.250 vctrl_min=0.450 vctrl_max=0.450 vctrl_span=0.000 |
| `505-fractional-n-divider-accumulator-flow` | `FAIL_SIM_CORRECTNESS` | pre_lock_edges=5 disturb_lock_low_frac=0.793 post_lock_edges=4 late_freq_ratio=1.0205 dco_counts=[16, 15, 15, 15, 16, 15, 15, 15] avg_dco_per_fb=15.250 vctrl_min=2.127 vctrl_max=2.397 vctrl_span=0.270 |
