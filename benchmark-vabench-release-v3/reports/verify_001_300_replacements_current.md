# v3 Staged Promotion Gold Probe

Date: 2026-07-07

## Summary

- `gold_total`: 12
- `gold_pass`: 12
- `gold_fail`: 0
- `expectation_fail`: 0
- `skipped_staged_tasks`: 0
- `gold_wall_s_total`: 78.761424
- `gold_wall_s_max`: 27.231555
- `slow_gold_threshold_s`: 20.0
- `slow_gold_count`: 1
- `wall_s`: 106.14253

## Slow Gold Cases

| Task | Status | Wall s |
| --- | --- | ---: |
| `202-comparator-delay-overdrive-meter` | `PASS` | 27.231555 |

## Gold Timing Top 20

| Task | Status | Wall s |
| --- | --- | ---: |
| `202-comparator-delay-overdrive-meter` | `PASS` | 27.231555 |
| `122-comparator-offset-calibration-loop` | `PASS` | 11.975525 |
| `057-first-order-sigma-delta-modulator` | `PASS` | 7.462689 |
| `285-dual-track-sample-hold` | `PASS` | 6.420687 |
| `124-hysteresis-trip-characterizer` | `PASS` | 5.781955 |
| `056-correlated-double-sampler` | `PASS` | 3.756904 |
| `298-voltage-match-window` | `PASS` | 3.516362 |
| `054-thermometer-bus-encoder` | `PASS` | 3.433371 |
| `075-adc-static-linearity-monitor` | `PASS` | 3.381836 |
| `052-dc-aware-adc3bit` | `PASS` | 2.30595 |
| `053-latched-bus-dac8` | `PASS` | 2.298185 |
| `055-slew-rate-dac4` | `PASS` | 1.196405 |

## Rows

| Task | Status | First behavior note |
| --- | --- | --- |
| `052-dc-aware-adc3bit` | `PASS` |  |
| `052-dc-aware-adc3bit` | `FAIL_SIM_CORRECTNESS` | adc3@3.80ns vin=0.190 code=1 obs={'d2': 0, 'd1': 0, 'd0': 0} adc3@5.80ns vin=0.380 code=3 obs={'d2': 0, 'd1': 0, 'd0': 0} adc3@7.80ns vin=0.620 code=4 obs={'d2': 0, 'd1': 0, 'd0': 0} adc3@9.80ns vin=0.870 code=6 obs={'d2': 0, 'd1': 0, 'd0': 0} adc3@11.80ns vin=1.100 code=7 obs={'d2': 0, 'd1': 0, 'd0': 0} |
| `052-dc-aware-adc3bit` | `FAIL_SIM_CORRECTNESS` | adc3@5.80ns vin=0.380 code=3 obs={'d2': 0, 'd1': 1, 'd0': 0} |
| `052-dc-aware-adc3bit` | `FAIL_SIM_CORRECTNESS` | adc3@3.80ns vin=0.190 code=1 obs={'d2': 1, 'd1': 0, 'd0': 0} adc3@5.80ns vin=0.380 code=3 obs={'d2': 1, 'd1': 1, 'd0': 0} adc3@7.80ns vin=0.620 code=4 obs={'d2': 0, 'd1': 0, 'd0': 1} adc3@9.80ns vin=0.870 code=6 obs={'d2': 0, 'd1': 1, 'd0': 1} |
| `052-dc-aware-adc3bit` | `FAIL_SIM_CORRECTNESS` | adc3@11.80ns vin=1.100 code=7 obs={'d2': 0, 'd1': 0, 'd0': 0} |
| `052-dc-aware-adc3bit` | `FAIL_SIM_CORRECTNESS` | adc3@3.80ns vin=0.190 code=1 obs={'d2': 0, 'd1': 1, 'd0': 0} adc3@7.80ns vin=0.620 code=4 obs={'d2': 1, 'd1': 0, 'd0': 1} adc3@9.80ns vin=0.870 code=6 obs={'d2': 1, 'd1': 1, 'd0': 1} |
| `053-latched-bus-dac8` | `PASS` |  |
| `053-latched-bus-dac8` | `FAIL_SIM_CORRECTNESS` | max_latched_dac_edge_err=0.9412 codes=[17, 126, 128, 45, 240] |
| `053-latched-bus-dac8` | `FAIL_SIM_CORRECTNESS` | max_latched_dac_hold_err=0.7647 codes=[17, 126, 128, 45, 240] |
| `053-latched-bus-dac8` | `FAIL_SIM_CORRECTNESS` | max_latched_dac_edge_err=0.7647 codes=[17, 126, 128, 45, 240] |
| `053-latched-bus-dac8` | `FAIL_SIM_CORRECTNESS` | max_latched_dac_edge_err=0.8824 codes=[17, 126, 128, 45, 240] |
| `053-latched-bus-dac8` | `FAIL_SIM_CORRECTNESS` | max_latched_dac_edge_err=0.9486 codes=[17, 126, 128, 45, 240] |
| `054-thermometer-bus-encoder` | `PASS` |  |
| `054-thermometer-bus-encoder` | `FAIL_SIM_CORRECTNESS` | therm@1.40ns code=1 observed=0 prefix=00000000 therm@3.40ns code=5 observed=0 prefix=00000000 therm@5.40ns code=11 observed=0 prefix=00000000 therm@7.40ns code=15 observed=0 prefix=00000000 therm@9.40ns code=16 observed=0 prefix=00000000 |
| `054-thermometer-bus-encoder` | `FAIL_SIM_CORRECTNESS` | tran.csv missing |
| `054-thermometer-bus-encoder` | `FAIL_SIM_CORRECTNESS` | tran.csv missing |
| `054-thermometer-bus-encoder` | `FAIL_SIM_CORRECTNESS` | tran.csv missing |
| `054-thermometer-bus-encoder` | `FAIL_SIM_CORRECTNESS` | therm@3.40ns code=5 observed=6 prefix=11111100 therm@5.40ns code=11 observed=12 prefix=11111111 therm@7.40ns code=15 observed=16 prefix=11111111 |
| `055-slew-rate-dac4` | `PASS` |  |
| `055-slew-rate-dac4` | `FAIL_SIM_CORRECTNESS` | max_slew_error=0.7333 |
| `055-slew-rate-dac4` | `FAIL_SIM_CORRECTNESS` | max_slew_error=0.7293 |
| `055-slew-rate-dac4` | `FAIL_SIM_CORRECTNESS` | max_endpoint_error=0.0250 |
| `055-slew-rate-dac4` | `FAIL_SIM_CORRECTNESS` | max_slew_error=0.1333 |
| `055-slew-rate-dac4` | `FAIL_SIM_CORRECTNESS` | max_slew_error=0.3658 |
| `056-correlated-double-sampler` | `PASS` |  |
| `056-correlated-double-sampler` | `FAIL_SIM_CORRECTNESS` | valid_not_asserted_after_signal=median0.0000_samples[0.0, 0.0, 0.0, 0.0] |
| `056-correlated-double-sampler` | `FAIL_SIM_CORRECTNESS` | reset_output_not_common_mode=max_err0.2900_samples[0.72, 0.18, 0.64, 0.3] |
| `056-correlated-double-sampler` | `FAIL_SIM_CORRECTNESS` | max_cds_output_err=0.9000_vcm=0.4500_vhi=0.9000_deltas=[-0.37999999999999995, 0.5800000000000001, -0.52, 0.78] |
| `056-correlated-double-sampler` | `FAIL_SIM_CORRECTNESS` | max_cds_output_err=0.2700_vcm=0.4500_vhi=0.9000_deltas=[-0.37999999999999995, 0.5800000000000001, -0.52, 0.78] |
| `056-correlated-double-sampler` | `FAIL_SIM_CORRECTNESS` | valid_not_cleared_on_reset=max0.9000 |
| `057-first-order-sigma-delta-modulator` | `PASS` |  |
| `057-first-order-sigma-delta-modulator` | `FAIL_SIM_CORRECTNESS` | edge@0.310ns bit=0 expected=1 vin=0.200 edge@3.510ns bit=0 expected=1 vin=0.200 edge@7.510ns bit=0 expected=1 vin=0.200 edge@11.510ns bit=0 expected=1 vin=0.200 edge@15.510ns bit=0 expected=1 vin=0.200 edge@18.710ns bit=0 expected=1 vin=0.600 |
| `057-first-order-sigma-delta-modulator` | `FAIL_SIM_CORRECTNESS` | edge@1.110ns bit=1 expected=0 vin=0.200 edge@1.910ns bit=1 expected=0 vin=0.200 edge@2.710ns bit=1 expected=0 vin=0.200 edge@4.310ns bit=1 expected=0 vin=0.200 edge@5.110ns bit=1 expected=0 vin=0.200 edge@5.910ns bit=1 expected=0 vin=0.200 |
| `057-first-order-sigma-delta-modulator` | `FAIL_SIM_CORRECTNESS` | edge@0.310ns bit=0 expected=1 vin=0.200 edge@3.510ns bit=0 expected=1 vin=0.200 edge@7.510ns bit=0 expected=1 vin=0.200 edge@11.510ns bit=0 expected=1 vin=0.200 edge@15.510ns bit=0 expected=1 vin=0.200 edge@18.710ns bit=0 expected=1 vin=0.600 |
| `057-first-order-sigma-delta-modulator` | `FAIL_SIM_CORRECTNESS` | edge@0.310ns bit=0 expected=1 vin=0.200 edge@1.110ns bit=1 expected=0 vin=0.200 edge@3.510ns bit=0 expected=1 vin=0.200 edge@4.310ns bit=1 expected=0 vin=0.200 edge@7.510ns bit=0 expected=1 vin=0.200 edge@8.310ns bit=1 expected=0 vin=0.200 |
| `057-first-order-sigma-delta-modulator` | `FAIL_SIM_CORRECTNESS` | edge@1.910ns bit=1 expected=0 vin=0.200 edge@5.910ns bit=1 expected=0 vin=0.200 edge@9.910ns bit=1 expected=0 vin=0.200 edge@13.910ns bit=1 expected=0 vin=0.200 edge@17.910ns bit=1 expected=0 vin=0.200 edge@19.510ns bit=1 expected=0 vin=0.600 |
| `075-adc-static-linearity-monitor` | `PASS` |  |
| `075-adc-static-linearity-monitor` | `FAIL_SIM_CORRECTNESS` | maxerr_metric_error=2.0000 metrics=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0] |
| `075-adc-static-linearity-monitor` | `FAIL_SIM_CORRECTNESS` | maxerr_not_monotonic=[0.0, 1.0, 0.0, 2.0, 0.0, 0.0] |
| `075-adc-static-linearity-monitor` | `FAIL_SIM_CORRECTNESS` | maxerr_metric_error=3.0000 metrics=[3.0, 3.0, 3.0, 5.0, 5.0, 5.0] |
| `075-adc-static-linearity-monitor` | `FAIL_SIM_CORRECTNESS` | maxerr_metric_error=1.0000 metrics=[1.0, 1.0, 1.0, 2.0, 2.0, 2.0] |
| `075-adc-static-linearity-monitor` | `FAIL_SIM_CORRECTNESS` | maxerr_metric_error=1.0000 metrics=[0.0, 0.0, 1.0, 1.0, 1.0, 1.0] |
| `122-comparator-offset-calibration-loop` | `PASS` |  |
| `122-comparator-offset-calibration-loop` | `FAIL_SIM_CORRECTNESS` | valid_never_asserted |
| `122-comparator-offset-calibration-loop` | `FAIL_SIM_CORRECTNESS` | offset_est=0.12700 ref=-0.01700 diff=0.12700 diff_err=0.00000 ref_err=0.14400 cm_err=0.00000 valid=0.900 updates=9 valid_edges=1 |
| `122-comparator-offset-calibration-loop` | `FAIL_SIM_CORRECTNESS` | offset_est=-0.06400 ref=-0.01700 diff=-0.06400 diff_err=0.00000 ref_err=0.04700 cm_err=0.00000 valid=0.900 updates=9 valid_edges=1 |
| `122-comparator-offset-calibration-loop` | `FAIL_SIM_CORRECTNESS` | valid_never_asserted |
| `122-comparator-offset-calibration-loop` | `FAIL_SIM_CORRECTNESS` | offset_est=-0.00850 ref=-0.01700 diff=-0.01700 diff_err=0.00850 ref_err=0.00850 cm_err=0.00000 valid=0.900 updates=9 valid_edges=1 |
| `124-hysteresis-trip-characterizer` | `PASS` |  |
| `124-hysteresis-trip-characterizer` | `FAIL_SIM_CORRECTNESS` | trip_rise=0.00000/0.53202 trip_fall=0.00000/0.45993 width=0.00000/0.07209 valid=0.000 events=2/2 |
| `124-hysteresis-trip-characterizer` | `FAIL_SIM_CORRECTNESS` | trip_rise=0.45993/0.53202 trip_fall=0.53202/0.45993 width=-0.07209/0.07209 valid=0.900 events=2/2 |
| `124-hysteresis-trip-characterizer` | `FAIL_SIM_CORRECTNESS` | trip_rise=0.53202/0.53202 trip_fall=0.45993/0.45993 width=-0.07209/0.07209 valid=0.900 events=2/2 |
| `124-hysteresis-trip-characterizer` | `FAIL_SIM_CORRECTNESS` | trip_rise=0.45000/0.53202 trip_fall=0.45000/0.45993 width=0.00000/0.07209 valid=0.900 events=2/2 |
| `124-hysteresis-trip-characterizer` | `FAIL_SIM_CORRECTNESS` | trip_rise=0.53202/0.53202 trip_fall=0.45993/0.45993 width=0.07209/0.07209 valid=0.000 events=2/2 |
| `202-comparator-delay-overdrive-meter` | `PASS` |  |
| `202-comparator-delay-overdrive-meter` | `FAIL_SIM_CORRECTNESS` | delay@0.968ns=0.000 expected=62.905 overdrive@0.968ns=0.000 expected=12.000 flags@0.968ns polarity=0.000/0.900 valid=0.000 delay@5.958ns=0.000 expected=53.250 overdrive@5.958ns=0.000 expected=60.000 flags@5.958ns polarity=0.000/0.000 valid=0.000 |
| `202-comparator-delay-overdrive-meter` | `FAIL_SIM_CORRECTNESS` | delay@0.968ns=0.000 expected=62.905 overdrive@0.968ns=0.000 expected=12.000 flags@0.968ns polarity=0.000/0.900 valid=0.000 delay@5.958ns=2903.250 expected=53.250 overdrive@5.958ns=12.000 expected=60.000 delay@10.976ns=2921.223 expected=71.223 |
| `202-comparator-delay-overdrive-meter` | `FAIL_SIM_CORRECTNESS` | overdrive@5.958ns=-60.000 expected=60.000 overdrive@15.964ns=-25.000 expected=25.000 |
| `202-comparator-delay-overdrive-meter` | `FAIL_SIM_CORRECTNESS` | flags@0.968ns polarity=0.000/0.900 valid=0.900 flags@5.958ns polarity=0.900/0.000 valid=0.900 flags@10.976ns polarity=0.000/0.900 valid=0.900 flags@15.964ns polarity=0.900/0.000 valid=0.900 flags@20.959ns polarity=0.000/0.900 valid=0.900 |
| `202-comparator-delay-overdrive-meter` | `FAIL_SIM_CORRECTNESS` | delay@0.968ns=31.452 expected=62.905 delay@5.958ns=26.625 expected=53.250 delay@10.976ns=35.611 expected=71.223 delay@15.964ns=29.251 expected=58.501 delay@20.959ns=27.172 expected=54.343 |
| `285-dual-track-sample-hold` | `PASS` |  |
| `285-dual-track-sample-hold` | `FAIL_SIM_CORRECTNESS` | dual_track_sample_hold mean_ref_err=0.178 max_ref_err=0.640 phase_hi=5 phase_lo=5 tracking_windows=4 hold_windows=5 hold_failures=4 |
| `285-dual-track-sample-hold` | `FAIL_SIM_CORRECTNESS` | dual_track_sample_hold mean_ref_err=0.030 max_ref_err=0.389 phase_hi=5 phase_lo=5 tracking_windows=0 hold_windows=5 hold_failures=0 |
| `285-dual-track-sample-hold` | `FAIL_SIM_CORRECTNESS` | dual_track_sample_hold mean_ref_err=0.175 max_ref_err=0.420 phase_hi=5 phase_lo=5 tracking_windows=0 hold_windows=5 hold_failures=4 |
| `285-dual-track-sample-hold` | `FAIL_SIM_CORRECTNESS` | dual_track_sample_hold mean_ref_err=0.133 max_ref_err=0.595 phase_hi=5 phase_lo=5 tracking_windows=0 hold_windows=5 hold_failures=4 |
| `285-dual-track-sample-hold` | `FAIL_SIM_CORRECTNESS` | dual_track_sample_hold mean_ref_err=0.000 max_ref_err=0.000 phase_hi=0 phase_lo=0 tracking_windows=5 hold_windows=5 hold_failures=0 |
| `298-voltage-match-window` | `PASS` |  |
| `298-voltage-match-window` | `FAIL_SIM_CORRECTNESS` | checked=369 matched=195 mismatched=174 near_boundary=294 max_err=0.9000 |
| `298-voltage-match-window` | `FAIL_SIM_CORRECTNESS` | checked=370 matched=196 mismatched=174 near_boundary=295 max_err=0.9000 |
| `298-voltage-match-window` | `FAIL_SIM_CORRECTNESS` | checked=369 matched=195 mismatched=174 near_boundary=294 max_err=0.9000 |
| `298-voltage-match-window` | `FAIL_SIM_CORRECTNESS` | checked=369 matched=195 mismatched=174 near_boundary=294 max_err=0.9000 |
| `298-voltage-match-window` | `FAIL_SIM_CORRECTNESS` | checked=369 matched=195 mismatched=174 near_boundary=294 max_err=0.5220 |
