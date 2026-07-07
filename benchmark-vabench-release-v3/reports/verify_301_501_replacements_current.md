# v3 Staged Promotion Gold Probe

Date: 2026-07-07

## Summary

- `gold_total`: 54
- `gold_pass`: 54
- `gold_fail`: 0
- `expectation_fail`: 0
- `skipped_staged_tasks`: 0
- `gold_wall_s_total`: 686.5652
- `gold_wall_s_max`: 41.117872
- `slow_gold_threshold_s`: 20.0
- `slow_gold_count`: 10
- `wall_s`: 1031.688211

## Slow Gold Cases

| Task | Status | Wall s |
| --- | --- | ---: |
| `418-enable-saturating-ready-counter` | `PASS` | 41.117872 |
| `394-deterministic-energy-accumulator` | `PASS` | 30.786098 |
| `395-bounded-tail-dither-shaper` | `PASS` | 29.313202 |
| `406-lane-mask-replication-driver` | `PASS` | 28.551621 |
| `417-async-reset-event-counter` | `PASS` | 26.873785 |
| `375-windowed-event-rate-monitor` | `PASS` | 24.774626 |
| `376-reset-release-sequencer` | `PASS` | 22.463264 |
| `348-phase-mismatch-qualifier` | `PASS` | 22.093166 |
| `346-reset-polarity-qualifier` | `PASS` | 21.468551 |
| `344-power-mode-clamped-mux` | `PASS` | 20.998829 |

## Gold Timing Top 20

| Task | Status | Wall s |
| --- | --- | ---: |
| `418-enable-saturating-ready-counter` | `PASS` | 41.117872 |
| `394-deterministic-energy-accumulator` | `PASS` | 30.786098 |
| `395-bounded-tail-dither-shaper` | `PASS` | 29.313202 |
| `406-lane-mask-replication-driver` | `PASS` | 28.551621 |
| `417-async-reset-event-counter` | `PASS` | 26.873785 |
| `375-windowed-event-rate-monitor` | `PASS` | 24.774626 |
| `376-reset-release-sequencer` | `PASS` | 22.463264 |
| `348-phase-mismatch-qualifier` | `PASS` | 22.093166 |
| `346-reset-polarity-qualifier` | `PASS` | 21.468551 |
| `344-power-mode-clamped-mux` | `PASS` | 20.998829 |
| `347-multi-condition-enable-combiner` | `PASS` | 19.746336 |
| `345-bias-trim-affine-mapper` | `PASS` | 18.676882 |
| `403-calibration-bit-select-flag` | `PASS` | 18.526254 |
| `416-ready-reduction-fault-monitor` | `PASS` | 17.510636 |
| `415-explicit-sar-slice-router` | `PASS` | 17.206268 |
| `374-sampled-error-update-monitor` | `PASS` | 17.0229 |
| `377-adaptive-threshold-tracker` | `PASS` | 16.234055 |
| `458-iterative-decay-estimator` | `PASS` | 13.687681 |
| `459-bounded-window-accumulator` | `PASS` | 13.247482 |
| `342-weighted-balance-summer` | `PASS` | 12.98404 |

## Rows

| Task | Status | First behavior note |
| --- | --- | --- |
| `341-rail-referenced-gain-buffer` | `PASS` |  |
| `341-rail-referenced-gain-buffer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `341-rail-referenced-gain-buffer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6238 |
| `341-rail-referenced-gain-buffer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `341-rail-referenced-gain-buffer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `341-rail-referenced-gain-buffer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `342-weighted-balance-summer` | `PASS` |  |
| `342-weighted-balance-summer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `342-weighted-balance-summer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `342-weighted-balance-summer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `342-weighted-balance-summer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `342-weighted-balance-summer` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `343-supply-qualified-window-flag` | `PASS` |  |
| `343-supply-qualified-window-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `343-supply-qualified-window-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `343-supply-qualified-window-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `343-supply-qualified-window-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `343-supply-qualified-window-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `344-power-mode-clamped-mux` | `PASS` |  |
| `344-power-mode-clamped-mux` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `344-power-mode-clamped-mux` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `344-power-mode-clamped-mux` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `344-power-mode-clamped-mux` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `344-power-mode-clamped-mux` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `345-bias-trim-affine-mapper` | `PASS` |  |
| `345-bias-trim-affine-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `345-bias-trim-affine-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6238 |
| `345-bias-trim-affine-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `345-bias-trim-affine-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `345-bias-trim-affine-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `346-reset-polarity-qualifier` | `PASS` |  |
| `346-reset-polarity-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `346-reset-polarity-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `346-reset-polarity-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `346-reset-polarity-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `346-reset-polarity-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `347-multi-condition-enable-combiner` | `PASS` |  |
| `347-multi-condition-enable-combiner` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `347-multi-condition-enable-combiner` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `347-multi-condition-enable-combiner` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3038 |
| `347-multi-condition-enable-combiner` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `347-multi-condition-enable-combiner` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `348-phase-mismatch-qualifier` | `PASS` |  |
| `348-phase-mismatch-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `348-phase-mismatch-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `348-phase-mismatch-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.4050 |
| `348-phase-mismatch-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `348-phase-mismatch-qualifier` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `349-priority-fault-code-driver` | `PASS` |  |
| `349-priority-fault-code-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `349-priority-fault-code-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `349-priority-fault-code-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `349-priority-fault-code-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `349-priority-fault-code-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `350-lane-validity-reduction-monitor` | `PASS` |  |
| `350-lane-validity-reduction-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `350-lane-validity-reduction-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `350-lane-validity-reduction-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3038 |
| `350-lane-validity-reduction-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `350-lane-validity-reduction-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `351-comparator-decision-capture` | `PASS` |  |
| `351-comparator-decision-capture` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `351-comparator-decision-capture` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `351-comparator-decision-capture` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `351-comparator-decision-capture` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `351-comparator-decision-capture` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `352-falling-edge-calibration-sampler` | `PASS` |  |
| `352-falling-edge-calibration-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `352-falling-edge-calibration-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `352-falling-edge-calibration-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `352-falling-edge-calibration-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `352-falling-edge-calibration-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `353-resettable-phase-toggle-monitor` | `PASS` |  |
| `353-resettable-phase-toggle-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `353-resettable-phase-toggle-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `353-resettable-phase-toggle-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `353-resettable-phase-toggle-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `353-resettable-phase-toggle-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `354-settling-progress-counter` | `PASS` |  |
| `354-settling-progress-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `354-settling-progress-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `354-settling-progress-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `354-settling-progress-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `354-settling-progress-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `355-enable-qualified-bias-hold` | `PASS` |  |
| `355-enable-qualified-bias-hold` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `355-enable-qualified-bias-hold` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4428 |
| `355-enable-qualified-bias-hold` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2653 |
| `355-enable-qualified-bias-hold` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `355-enable-qualified-bias-hold` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `356-dynamic-supply-enable-driver` | `PASS` |  |
| `356-dynamic-supply-enable-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `356-dynamic-supply-enable-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `356-dynamic-supply-enable-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3517 |
| `356-dynamic-supply-enable-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.4048 |
| `356-dynamic-supply-enable-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `357-local-domain-buffer-translator` | `PASS` |  |
| `357-local-domain-buffer-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `357-local-domain-buffer-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `357-local-domain-buffer-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3517 |
| `357-local-domain-buffer-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.4048 |
| `357-local-domain-buffer-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `358-bias-window-threshold-bridge` | `PASS` |  |
| `358-bias-window-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `358-bias-window-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `358-bias-window-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `358-bias-window-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `358-bias-window-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `359-clocked-power-ready-sampler` | `PASS` |  |
| `359-clocked-power-ready-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `359-clocked-power-ready-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `359-clocked-power-ready-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `359-clocked-power-ready-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `359-clocked-power-ready-sampler` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `360-mode-selected-bias-driver` | `PASS` |  |
| `360-mode-selected-bias-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `360-mode-selected-bias-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `360-mode-selected-bias-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `360-mode-selected-bias-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `360-mode-selected-bias-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `373-saturation-recovery-limiter` | `PASS` |  |
| `373-saturation-recovery-limiter` | `FAIL_SIM_CORRECTNESS` | saturation_limiter_error=0.9000 |
| `373-saturation-recovery-limiter` | `FAIL_SIM_CORRECTNESS` | saturation_limiter_error=0.9000 |
| `373-saturation-recovery-limiter` | `FAIL_SIM_CORRECTNESS` | saturation_limiter_error=0.9000 |
| `373-saturation-recovery-limiter` | `FAIL_SIM_CORRECTNESS` | saturation_limiter_error=0.9000 |
| `373-saturation-recovery-limiter` | `FAIL_SIM_CORRECTNESS` | saturation_limiter_error=0.5727 |
| `374-sampled-error-update-monitor` | `PASS` |  |
| `374-sampled-error-update-monitor` | `FAIL_SIM_CORRECTNESS` | sampled_error_update_error=0.1860 |
| `374-sampled-error-update-monitor` | `FAIL_SIM_CORRECTNESS` | sampled_error_update_error=0.9000 |
| `374-sampled-error-update-monitor` | `FAIL_SIM_CORRECTNESS` | sampled_error_update_error=0.9000 |
| `374-sampled-error-update-monitor` | `FAIL_SIM_CORRECTNESS` | sampled_error_update_error=0.9000 |
| `374-sampled-error-update-monitor` | `FAIL_SIM_CORRECTNESS` | sampled_error_update_error=0.9000 |
| `375-windowed-event-rate-monitor` | `PASS` |  |
| `375-windowed-event-rate-monitor` | `FAIL_SIM_CORRECTNESS` | event_rate_monitor_error=0.9000 |
| `375-windowed-event-rate-monitor` | `FAIL_SIM_CORRECTNESS` | event_rate_monitor_error=0.5400 |
| `375-windowed-event-rate-monitor` | `FAIL_SIM_CORRECTNESS` | event_rate_monitor_error=0.6000 |
| `375-windowed-event-rate-monitor` | `FAIL_SIM_CORRECTNESS` | event_rate_monitor_error=2.1600 |
| `375-windowed-event-rate-monitor` | `FAIL_SIM_CORRECTNESS` | event_rate_monitor_error=0.7200 |
| `376-reset-release-sequencer` | `PASS` |  |
| `376-reset-release-sequencer` | `FAIL_SIM_CORRECTNESS` | reset_release_error=0.9000 |
| `376-reset-release-sequencer` | `FAIL_SIM_CORRECTNESS` | reset_release_error=0.9000 |
| `376-reset-release-sequencer` | `FAIL_SIM_CORRECTNESS` | reset_release_error=0.9000 |
| `376-reset-release-sequencer` | `FAIL_SIM_CORRECTNESS` | reset_release_error=0.9000 |
| `376-reset-release-sequencer` | `FAIL_SIM_CORRECTNESS` | reset_release_error=0.3000 |
| `377-adaptive-threshold-tracker` | `PASS` |  |
| `377-adaptive-threshold-tracker` | `FAIL_SIM_CORRECTNESS` | adaptive_threshold_error=0.5000 |
| `377-adaptive-threshold-tracker` | `FAIL_SIM_CORRECTNESS` | adaptive_threshold_error=0.9000 |
| `377-adaptive-threshold-tracker` | `FAIL_SIM_CORRECTNESS` | adaptive_threshold_error=0.9000 |
| `377-adaptive-threshold-tracker` | `FAIL_SIM_CORRECTNESS` | adaptive_threshold_error=0.9000 |
| `377-adaptive-threshold-tracker` | `FAIL_SIM_CORRECTNESS` | adaptive_threshold_error=0.6049 |
| `378-rail-normalized-metric-mapper` | `PASS` |  |
| `378-rail-normalized-metric-mapper` | `FAIL_SIM_CORRECTNESS` | rail_normalized_metric_error=0.1019 |
| `378-rail-normalized-metric-mapper` | `FAIL_SIM_CORRECTNESS` | rail_normalized_metric_error=0.2229 |
| `378-rail-normalized-metric-mapper` | `FAIL_SIM_CORRECTNESS` | rail_normalized_metric_error=0.3098 |
| `378-rail-normalized-metric-mapper` | `FAIL_SIM_CORRECTNESS` | rail_normalized_metric_error=0.1770 |
| `378-rail-normalized-metric-mapper` | `FAIL_SIM_CORRECTNESS` | rail_normalized_metric_error=0.9000 |
| `394-deterministic-energy-accumulator` | `PASS` |  |
| `394-deterministic-energy-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `394-deterministic-energy-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4865 |
| `394-deterministic-energy-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2874 |
| `394-deterministic-energy-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `394-deterministic-energy-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `395-bounded-tail-dither-shaper` | `PASS` |  |
| `395-bounded-tail-dither-shaper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `395-bounded-tail-dither-shaper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4865 |
| `395-bounded-tail-dither-shaper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2874 |
| `395-bounded-tail-dither-shaper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `395-bounded-tail-dither-shaper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `403-calibration-bit-select-flag` | `PASS` |  |
| `403-calibration-bit-select-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `403-calibration-bit-select-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `403-calibration-bit-select-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `403-calibration-bit-select-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `403-calibration-bit-select-flag` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `406-lane-mask-replication-driver` | `PASS` |  |
| `406-lane-mask-replication-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `406-lane-mask-replication-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `406-lane-mask-replication-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3038 |
| `406-lane-mask-replication-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `406-lane-mask-replication-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `415-explicit-sar-slice-router` | `PASS` |  |
| `415-explicit-sar-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `415-explicit-sar-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `415-explicit-sar-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `415-explicit-sar-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `415-explicit-sar-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `416-ready-reduction-fault-monitor` | `PASS` |  |
| `416-ready-reduction-fault-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `416-ready-reduction-fault-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `416-ready-reduction-fault-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3038 |
| `416-ready-reduction-fault-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `416-ready-reduction-fault-monitor` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `417-async-reset-event-counter` | `PASS` |  |
| `417-async-reset-event-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `417-async-reset-event-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `417-async-reset-event-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `417-async-reset-event-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `417-async-reset-event-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `418-enable-saturating-ready-counter` | `PASS` |  |
| `418-enable-saturating-ready-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `418-enable-saturating-ready-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `418-enable-saturating-ready-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `418-enable-saturating-ready-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `418-enable-saturating-ready-counter` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `419-rail-aware-threshold-bridge` | `PASS` |  |
| `419-rail-aware-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `419-rail-aware-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `419-rail-aware-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `419-rail-aware-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `419-rail-aware-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `420-mode-latch-calibration-gate` | `PASS` |  |
| `420-mode-latch-calibration-gate` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `420-mode-latch-calibration-gate` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4428 |
| `420-mode-latch-calibration-gate` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2653 |
| `420-mode-latch-calibration-gate` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `420-mode-latch-calibration-gate` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `421-calibration-affine-transform` | `PASS` |  |
| `421-calibration-affine-transform` | `FAIL_SIM_CORRECTNESS` | calibration_affine_error=0.3600 |
| `421-calibration-affine-transform` | `FAIL_SIM_CORRECTNESS` | calibration_affine_error=0.6000 |
| `421-calibration-affine-transform` | `FAIL_SIM_CORRECTNESS` | calibration_affine_error=0.9000 |
| `421-calibration-affine-transform` | `FAIL_SIM_CORRECTNESS` | calibration_affine_error=0.1020 |
| `421-calibration-affine-transform` | `FAIL_SIM_CORRECTNESS` | calibration_affine_error=0.8760 |
| `433-configurable-startup-policy` | `PASS` |  |
| `433-configurable-startup-policy` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `433-configurable-startup-policy` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `433-configurable-startup-policy` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `433-configurable-startup-policy` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `433-configurable-startup-policy` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `449-explicit-replicated-stage-chain` | `PASS` |  |
| `449-explicit-replicated-stage-chain` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `449-explicit-replicated-stage-chain` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `449-explicit-replicated-stage-chain` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `449-explicit-replicated-stage-chain` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `449-explicit-replicated-stage-chain` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `451-electrical-threshold-bridge` | `PASS` |  |
| `451-electrical-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `451-electrical-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `451-electrical-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3223 |
| `451-electrical-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `451-electrical-threshold-bridge` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `452-local-rail-domain-translator` | `PASS` |  |
| `452-local-rail-domain-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `452-local-rail-domain-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `452-local-rail-domain-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3517 |
| `452-local-rail-domain-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.4048 |
| `452-local-rail-domain-translator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `453-edge-delay-qualified-driver` | `PASS` |  |
| `453-edge-delay-qualified-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `453-edge-delay-qualified-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `453-edge-delay-qualified-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4050 |
| `453-edge-delay-qualified-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4776 |
| `453-edge-delay-qualified-driver` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `454-calibration-quadrant-mapper` | `PASS` |  |
| `454-calibration-quadrant-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `454-calibration-quadrant-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `454-calibration-quadrant-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `454-calibration-quadrant-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `454-calibration-quadrant-mapper` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `455-explicit-bus-slice-router` | `PASS` |  |
| `455-explicit-bus-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `455-explicit-bus-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `455-explicit-bus-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.3234 |
| `455-explicit-bus-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.6065 |
| `455-explicit-bus-slice-router` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_error=0.9000 |
| `458-iterative-decay-estimator` | `PASS` |  |
| `458-iterative-decay-estimator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `458-iterative-decay-estimator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4865 |
| `458-iterative-decay-estimator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2874 |
| `458-iterative-decay-estimator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `458-iterative-decay-estimator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `459-bounded-window-accumulator` | `PASS` |  |
| `459-bounded-window-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `459-bounded-window-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.4865 |
| `459-bounded-window-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.2874 |
| `459-bounded-window-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `459-bounded-window-accumulator` | `FAIL_SIM_CORRECTNESS` | issue109_remaining_clock_error=0.9000 |
| `490-event-reacquire-lock-detector` | `PASS` |  |
| `490-event-reacquire-lock-detector` | `FAIL_SIM_CORRECTNESS` | event_reacquire_lock_error=0.9000 |
| `490-event-reacquire-lock-detector` | `FAIL_SIM_CORRECTNESS` | event_reacquire_lock_error=0.9000 |
| `490-event-reacquire-lock-detector` | `FAIL_SIM_CORRECTNESS` | event_reacquire_lock_error=0.9000 |
| `490-event-reacquire-lock-detector` | `FAIL_SIM_CORRECTNESS` | event_reacquire_lock_error=0.9000 |
| `490-event-reacquire-lock-detector` | `FAIL_SIM_CORRECTNESS` | event_reacquire_lock_error=0.9000 |
| `495-supply-bias-validity-gate` | `PASS` |  |
| `495-supply-bias-validity-gate` | `FAIL_SIM_CORRECTNESS` | validity_gate_error=0.9000 |
| `495-supply-bias-validity-gate` | `FAIL_SIM_CORRECTNESS` | validity_gate_error=0.9000 |
| `495-supply-bias-validity-gate` | `FAIL_SIM_CORRECTNESS` | validity_gate_error=0.9000 |
| `495-supply-bias-validity-gate` | `FAIL_SIM_CORRECTNESS` | validity_gate_error=0.9000 |
| `495-supply-bias-validity-gate` | `FAIL_SIM_CORRECTNESS` | validity_gate_error=0.9000 |
| `496-reference-settling-window-monitor` | `PASS` |  |
| `496-reference-settling-window-monitor` | `FAIL_SIM_CORRECTNESS` | reference_settling_error=0.9000 |
| `496-reference-settling-window-monitor` | `FAIL_SIM_CORRECTNESS` | reference_settling_error=0.9000 |
| `496-reference-settling-window-monitor` | `FAIL_SIM_CORRECTNESS` | reference_settling_error=0.9000 |
| `496-reference-settling-window-monitor` | `FAIL_SIM_CORRECTNESS` | reference_settling_error=0.9000 |
| `496-reference-settling-window-monitor` | `FAIL_SIM_CORRECTNESS` | reference_settling_error=0.9000 |
| `497-power-enable-turnon-delay-gate` | `PASS` |  |
| `497-power-enable-turnon-delay-gate` | `FAIL_SIM_CORRECTNESS` | turnon_delay_gate_error=0.9000 |
| `497-power-enable-turnon-delay-gate` | `FAIL_SIM_CORRECTNESS` | turnon_delay_gate_error=0.9000 |
| `497-power-enable-turnon-delay-gate` | `FAIL_SIM_CORRECTNESS` | turnon_delay_gate_error=0.9000 |
| `497-power-enable-turnon-delay-gate` | `FAIL_SIM_CORRECTNESS` | turnon_delay_gate_error=0.9000 |
| `497-power-enable-turnon-delay-gate` | `FAIL_SIM_CORRECTNESS` | turnon_delay_gate_error=0.9000 |
| `498-power-mode-supply-current-metric` | `PASS` |  |
| `498-power-mode-supply-current-metric` | `FAIL_SIM_CORRECTNESS` | supply_metric_error=0.3533 |
| `498-power-mode-supply-current-metric` | `FAIL_SIM_CORRECTNESS` | supply_metric_error=0.1133 |
| `498-power-mode-supply-current-metric` | `FAIL_SIM_CORRECTNESS` | supply_metric_error=0.3153 |
| `498-power-mode-supply-current-metric` | `FAIL_SIM_CORRECTNESS` | supply_metric_error=0.0800 |
| `498-power-mode-supply-current-metric` | `FAIL_SIM_CORRECTNESS` | supply_metric_error=0.2667 |
| `499-dynamic-supply-level-driver` | `PASS` |  |
| `499-dynamic-supply-level-driver` | `FAIL_SIM_CORRECTNESS` | dynamic_supply_driver_error=0.8500 |
| `499-dynamic-supply-level-driver` | `FAIL_SIM_CORRECTNESS` | dynamic_supply_driver_error=0.6500 |
| `499-dynamic-supply-level-driver` | `FAIL_SIM_CORRECTNESS` | dynamic_supply_driver_error=0.4900 |
| `499-dynamic-supply-level-driver` | `FAIL_SIM_CORRECTNESS` | dynamic_supply_driver_error=0.4300 |
| `499-dynamic-supply-level-driver` | `FAIL_SIM_CORRECTNESS` | dynamic_supply_driver_error=0.9500 |
| `500-rail-ramp-rate-startup-monitor` | `PASS` |  |
| `500-rail-ramp-rate-startup-monitor` | `FAIL_SIM_CORRECTNESS` | rail_startup_error=0.9000 |
| `500-rail-ramp-rate-startup-monitor` | `FAIL_SIM_CORRECTNESS` | rail_startup_error=0.9000 |
| `500-rail-ramp-rate-startup-monitor` | `FAIL_SIM_CORRECTNESS` | rail_startup_error=0.9000 |
| `500-rail-ramp-rate-startup-monitor` | `FAIL_SIM_CORRECTNESS` | rail_startup_error=0.9000 |
| `500-rail-ramp-rate-startup-monitor` | `FAIL_SIM_CORRECTNESS` | rail_startup_error=0.9000 |
| `501-differential-common-mode-window-monitor` | `PASS` |  |
| `501-differential-common-mode-window-monitor` | `FAIL_SIM_CORRECTNESS` | diff_cm_monitor_error=0.9000 |
| `501-differential-common-mode-window-monitor` | `FAIL_SIM_CORRECTNESS` | diff_cm_monitor_error=0.9000 |
| `501-differential-common-mode-window-monitor` | `FAIL_SIM_CORRECTNESS` | diff_cm_monitor_error=1.1250 |
| `501-differential-common-mode-window-monitor` | `FAIL_SIM_CORRECTNESS` | diff_cm_monitor_error=0.9000 |
| `501-differential-common-mode-window-monitor` | `FAIL_SIM_CORRECTNESS` | diff_cm_monitor_error=0.7875 |
