# v3 Extension SOP Audit

Date: 2026-07-07

## Summary

- Audited extension tasks: **205**
- SOP-ready tasks: **151**
- Tasks with executable visible+hidden SCS evidence: **205**
- Tasks with behavior checker evidence: **151**
- Tasks with complete manifest behavior contracts: **205**
- Tasks with aligned negative case indexes: **195**
- Tasks with task-specific negative descriptions: **151**
- Tasks with distinct visible/hidden SCS stimuli: **205**
- Tasks with identical visible/hidden SCS stimuli: **0**
- SOP-ready tasks with identical visible/hidden SCS stimuli: **0**
- Staged tasks with identical visible/hidden SCS stimuli: **0**

## Issue Counts

- `negative_cases_index_mismatch`: 10
- `negative_descriptions_not_task_specific`: 54

## Warning Counts

- `candidate_tier_not_score_ready`: 204

## Range Summary

| Range | Description | Tasks | Ready | Executable Tests | Behavior Eval | Contracts | Neg Index | Neg Desc | Distinct V/H | Top Issues |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `301-340` | language-semantics voltage-domain candidates | 40 | 40 | 40 | 40 | 40 | 40 | 40 | 40 |  |
| `341-360` | AMS mixed-signal candidates | 20 | 0 | 20 | 0 | 20 | 20 | 0 | 20 | `negative_descriptions_not_task_specific`: 20 |
| `361-372` | noise and analysis candidates | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |  |
| `373-434` | task/file/table/random/hierarchy syntax candidates | 62 | 44 | 62 | 44 | 62 | 55 | 44 | 62 | `negative_descriptions_not_task_specific`: 18<br>`negative_cases_index_mismatch`: 7 |
| `435-458` | manual syntax-completion candidates | 24 | 17 | 24 | 17 | 24 | 24 | 17 | 24 | `negative_descriptions_not_task_specific`: 7 |
| `459-470` | course-material gap-fill candidates | 12 | 11 | 12 | 11 | 12 | 12 | 11 | 12 | `negative_descriptions_not_task_specific`: 1 |
| `471-501` | LRM KCL/continuous-time and Cadence data-converter gap-fill candidates | 31 | 23 | 31 | 23 | 31 | 28 | 23 | 31 | `negative_descriptions_not_task_specific`: 8<br>`negative_cases_index_mismatch`: 3 |
| `502-505` | post-501 PLL/control extension additions | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |  |

## Highest Severity Finding

Tasks 301-505 are staging-layer benchmark tasks outside the original full-300 denominator. Under the SOP they must retain concrete public behavior prompts, executable visible and hidden tests, repository behavior checkers, and five behavior-rejected negative variants.

## Per-Task Rows

| Task | Tier | Ready | Issues |
| --- | --- | --- | --- |
| `301-function-clamp-window` | `syntax-extension-candidate` | True | - |
| `302-function-deadband-map` | `syntax-extension-candidate` | True | - |
| `303-function-piecewise-gain` | `syntax-extension-candidate` | True | - |
| `304-function-code-normalizer` | `syntax-extension-candidate` | True | - |
| `305-function-soft-threshold` | `syntax-extension-candidate` | True | - |
| `306-case-mode-gain-selector` | `syntax-extension-candidate` | True | - |
| `307-case-priority-status-decoder` | `syntax-extension-candidate` | True | - |
| `308-case-quantized-output-level` | `syntax-extension-candidate` | True | - |
| `309-case-clocked-range-bucket` | `syntax-extension-candidate` | True | - |
| `310-case-resettable-state-decoder` | `syntax-extension-candidate` | True | - |
| `311-for-loop-running-average` | `syntax-extension-candidate` | True | - |
| `312-for-loop-thermometer-count` | `syntax-extension-candidate` | True | - |
| `313-for-loop-weighted-accumulator` | `syntax-extension-candidate` | True | - |
| `314-for-loop-windowed-peak` | `syntax-extension-candidate` | True | - |
| `315-for-loop-code-popcount` | `syntax-extension-candidate` | True | - |
| `316-final-step-edge-counter-file` | `syntax-extension-candidate` | True | - |
| `317-final-step-average-metric-file` | `syntax-extension-candidate` | True | - |
| `318-final-step-max-observer-file` | `syntax-extension-candidate` | True | - |
| `319-display-strobe-event-logger` | `syntax-extension-candidate` | True | - |
| `320-file-io-sampled-metric-writer` | `syntax-extension-candidate` | True | - |
| `321-slew-limited-voltage-follower` | `syntax-extension-candidate` | True | - |
| `322-slew-limited-mode-stepper` | `syntax-extension-candidate` | True | - |
| `323-slew-output-reset-recovery` | `syntax-extension-candidate` | True | - |
| `324-slew-limited-envelope` | `syntax-extension-candidate` | True | - |
| `325-slew-asymmetric-rise-fall` | `syntax-extension-candidate` | True | - |
| `326-idtmod-phase-accumulator` | `syntax-extension-candidate` | True | - |
| `327-idtmod-wrapped-ramp-source` | `syntax-extension-candidate` | True | - |
| `328-idtmod-frequency-control` | `syntax-extension-candidate` | True | - |
| `329-idtmod-modulo-phase-marker` | `syntax-extension-candidate` | True | - |
| `330-idtmod-clock-phase-meter` | `syntax-extension-candidate` | True | - |
| `331-above-threshold-latch` | `syntax-extension-candidate` | True | - |
| `332-above-window-qualifier` | `syntax-extension-candidate` | True | - |
| `333-last-crossing-period-meter` | `syntax-extension-candidate` | True | - |
| `334-last-crossing-edge-age` | `syntax-extension-candidate` | True | - |
| `335-above-resettable-peak-marker` | `syntax-extension-candidate` | True | - |
| `336-directive-configurable-threshold` | `syntax-extension-candidate` | True | - |
| `337-parameter-range-limited-gain` | `syntax-extension-candidate` | True | - |
| `338-math-trig-envelope-detector` | `syntax-extension-candidate` | True | - |
| `339-random-seeded-dither-source` | `syntax-extension-candidate` | True | - |
| `340-bound-step-clock-guard` | `syntax-extension-candidate` | True | - |
| `341-rail-referenced-gain-buffer` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `342-weighted-balance-summer` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `343-supply-qualified-window-flag` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `344-power-mode-clamped-mux` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `345-bias-trim-affine-mapper` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `346-reset-polarity-qualifier` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `347-multi-condition-enable-combiner` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `348-phase-mismatch-qualifier` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `349-priority-fault-code-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `350-lane-validity-reduction-monitor` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `351-comparator-decision-capture` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `352-falling-edge-calibration-sampler` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `353-resettable-phase-toggle-monitor` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `354-settling-progress-counter` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `355-enable-qualified-bias-hold` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `356-dynamic-supply-enable-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `357-local-domain-buffer-translator` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `358-bias-window-threshold-bridge` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `359-clocked-power-ready-sampler` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `360-mode-selected-bias-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `361-white-noise-voltage-source` | `noise-analysis-candidate` | True | - |
| `362-white-noise-gated-source` | `noise-analysis-candidate` | True | - |
| `363-flicker-noise-voltage-source` | `noise-analysis-candidate` | True | - |
| `364-flicker-noise-corner-selector` | `noise-analysis-candidate` | True | - |
| `365-noise-table-voltage-shaper` | `noise-analysis-candidate` | True | - |
| `366-noise-table-gated-shaper` | `noise-analysis-candidate` | True | - |
| `367-analysis-dependent-dc-tran-mode` | `noise-analysis-candidate` | True | - |
| `368-analysis-dependent-noise-enable` | `noise-analysis-candidate` | True | - |
| `369-ac-stim-small-signal-source` | `noise-analysis-candidate` | True | - |
| `370-ac-stim-phase-selector` | `noise-analysis-candidate` | True | - |
| `371-combined-white-flicker-noise` | `noise-analysis-candidate` | True | - |
| `372-analysis-aware-noise-metric` | `noise-analysis-candidate` | True | - |
| `373-saturation-recovery-limiter` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `374-sampled-error-update-monitor` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `375-windowed-event-rate-monitor` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `376-reset-release-sequencer` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `377-adaptive-threshold-tracker` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `378-rail-normalized-metric-mapper` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `379-file-fgets-config-loader` | `syntax-extension-candidate` | True | - |
| `380-file-feof-line-counter` | `syntax-extension-candidate` | True | - |
| `381-file-fseek-offset-reader` | `syntax-extension-candidate` | True | - |
| `382-file-ftell-position-meter` | `syntax-extension-candidate` | True | - |
| `383-file-rewind-second-pass` | `syntax-extension-candidate` | True | - |
| `384-file-fopen-mode-selector` | `syntax-extension-candidate` | True | - |
| `385-table-model-linear-gain` | `syntax-extension-candidate` | True | - |
| `386-table-model-clamped-transfer` | `syntax-extension-candidate` | True | - |
| `387-table-model-threshold-map` | `syntax-extension-candidate` | True | - |
| `388-table-model-dac-code-map` | `syntax-extension-candidate` | True | - |
| `389-table-model-temperature-profile` | `syntax-extension-candidate` | True | - |
| `390-table-model-piecewise-calibrator` | `syntax-extension-candidate` | True | - |
| `391-rdist-exponential-jitter` | `syntax-extension-candidate` | True | - |
| `392-rdist-poisson-count-noise` | `syntax-extension-candidate` | True | - |
| `393-rdist-normal-offset-dither` | `syntax-extension-candidate` | True | - |
| `394-deterministic-energy-accumulator` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `395-bounded-tail-dither-shaper` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `396-rdist-erlang-latency` | `syntax-extension-candidate` | True | - |
| `397-hierarchy-gain-child` | `syntax-extension-candidate` | True | - |
| `398-hierarchy-two-stage-chain` | `syntax-extension-candidate` | True | - |
| `399-hierarchy-parameter-override` | `syntax-extension-candidate` | True | - |
| `400-hierarchy-named-port-map` | `syntax-extension-candidate` | True | - |
| `401-hierarchy-ordered-port-map` | `syntax-extension-candidate` | True | - |
| `402-hierarchy-shared-threshold-child` | `syntax-extension-candidate` | True | - |
| `403-calibration-bit-select-flag` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `404-vector-part-select-window` | `behavioral-control-candidate` | True | - |
| `405-vector-concat-code-build` | `behavioral-control-candidate` | True | - |
| `406-lane-mask-replication-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `407-vector-reduction-parity` | `syntax-extension-candidate` | True | - |
| `408-vector-shift-and-mask-decoder` | `syntax-extension-candidate` | True | - |
| `409-macro-functionlike-clamp` | `syntax-extension-candidate` | True | - |
| `410-macro-ifdef-gain-select` | `syntax-extension-candidate` | True | - |
| `411-escaped-identifier-state` | `syntax-extension-candidate` | True | - |
| `412-initial-final-step-lifecycle` | `syntax-extension-candidate` | True | - |
| `413-while-loop-array-sum` | `syntax-extension-candidate` | True | - |
| `414-parameter-range-real-control` | `syntax-extension-candidate` | True | - |
| `415-explicit-sar-slice-router` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `416-ready-reduction-fault-monitor` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `417-async-reset-event-counter` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `418-enable-saturating-ready-counter` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `419-rail-aware-threshold-bridge` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `420-mode-latch-calibration-gate` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `421-calibration-affine-transform` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `422-file-fscanf-table-stimulus` | `syntax-extension-candidate` | True | - |
| `423-file-profile-replay-controller` | `syntax-extension-candidate` | True | - |
| `424-file-fscanf-multi-column-profile` | `syntax-extension-candidate` | True | - |
| `425-string-swrite-label-builder` | `syntax-extension-candidate` | True | - |
| `426-string-sformat-mode-tag` | `syntax-extension-candidate` | True | - |
| `427-string-formatted-metric-line` | `syntax-extension-candidate` | True | - |
| `428-string-mode-tagged-log` | `syntax-extension-candidate` | True | - |
| `429-string-config-label-select` | `syntax-extension-candidate` | True | - |
| `430-rdist-seed-reproducibility` | `syntax-extension-candidate` | True | - |
| `431-hierarchy-support-artifact-staging` | `syntax-extension-candidate` | True | - |
| `432-hierarchy-nested-parameter-chain` | `syntax-extension-candidate` | True | - |
| `433-configurable-startup-policy` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `434-repeat-loop-accumulator` | `syntax-extension-candidate` | True | - |
| `435-ddt-voltage-derivative-source` | `behavioral-continuous-time-candidate` | True | - |
| `436-idt-voltage-integrator-source` | `behavioral-continuous-time-candidate` | True | - |
| `437-laplace-nd-lowpass-filter` | `behavioral-continuous-time-candidate` | True | - |
| `438-laplace-np-pole-filter` | `behavioral-continuous-time-candidate` | True | - |
| `439-laplace-zd-zero-den-filter` | `behavioral-continuous-time-candidate` | True | - |
| `440-laplace-zp-zero-pole-filter` | `behavioral-continuous-time-candidate` | True | - |
| `441-zi-nd-discrete-filter` | `behavioral-continuous-time-candidate` | True | - |
| `442-zi-np-discrete-filter` | `behavioral-continuous-time-candidate` | True | - |
| `443-zi-zd-discrete-filter` | `behavioral-continuous-time-candidate` | True | - |
| `444-zi-zp-discrete-filter` | `behavioral-continuous-time-candidate` | True | - |
| `445-limexp-soft-exponential` | `syntax-extension-candidate` | True | - |
| `446-fstrobe-file-line-writer` | `syntax-extension-candidate` | True | - |
| `447-display-warning-debug-log` | `syntax-extension-candidate` | True | - |
| `448-rdist-uniform-seeded-dither` | `syntax-extension-candidate` | True | - |
| `449-explicit-replicated-stage-chain` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `450-custom-nature-discipline-voltage` | `syntax-extension-candidate` | True | - |
| `451-electrical-threshold-bridge` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `452-local-rail-domain-translator` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `453-edge-delay-qualified-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `454-calibration-quadrant-mapper` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `455-explicit-bus-slice-router` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `456-event-or-cross-timer` | `syntax-extension-candidate` | True | - |
| `457-nested-function-pipeline` | `syntax-extension-candidate` | True | - |
| `458-iterative-decay-estimator` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `459-bounded-window-accumulator` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `460-analog-initial-block-state` | `syntax-extension-candidate` | True | - |
| `461-vt-thermal-voltage-source` | `syntax-extension-candidate` | True | - |
| `462-vt-temperature-argument` | `syntax-extension-candidate` | True | - |
| `463-discontinuity-event-announcement` | `syntax-extension-candidate` | True | - |
| `464-param-given-gain-select` | `syntax-extension-candidate` | True | - |
| `465-port-connected-output-enable` | `syntax-extension-candidate` | True | - |
| `466-temperature-environment-metric` | `syntax-extension-candidate` | True | - |
| `467-simparam-query-tnom` | `syntax-extension-candidate` | True | - |
| `468-branch-declaration-voltage-probe` | `syntax-extension-candidate` | True | - |
| `469-current-contribution-conductance` | `kcl-syntax-candidate` | True | - |
| `470-branch-current-probe-contribution` | `kcl-syntax-candidate` | True | - |
| `471-indirect-branch-null-balance` | `behavioral-continuous-time-candidate` | True | - |
| `472-indirect-branch-ddt-balance` | `behavioral-continuous-time-candidate` | True | - |
| `473-attribute-potential-abstol-probe` | `syntax-extension-candidate` | True | - |
| `474-generic-potential-access-function` | `syntax-extension-candidate` | True | - |
| `475-generic-potential-contribution` | `syntax-extension-candidate` | True | - |
| `476-oomr-string-voltage-probe` | `syntax-extension-candidate` | True | - |
| `477-analog-node-alias-initial` | `syntax-extension-candidate` | True | - |
| `478-inherited-port-attribute-supply` | `syntax-extension-candidate` | True | - |
| `479-inherited-mfactor-parameter` | `syntax-extension-candidate` | True | - |
| `480-mfactor-system-function-gain` | `syntax-extension-candidate` | True | - |
| `481-analog-primitive-resistor-instance` | `kcl-syntax-candidate` | True | - |
| `482-analog-primitive-isource-instance` | `kcl-syntax-candidate` | True | - |
| `483-cds-violation-threshold-assert` | `cadence-simulator-function-candidate` | True | - |
| `484-rtoi-conversion-quantizer` | `syntax-extension-candidate` | True | - |
| `485-mc-trial-number-metric` | `cadence-simulator-function-candidate` | True | - |
| `486-rf-source-info-registration` | `cadence-simulator-function-candidate` | True | - |
| `487-table-model-2d-array-surface` | `syntax-extension-candidate` | True | - |
| `488-table-model-string-param-source` | `syntax-extension-candidate` | True | - |
| `489-event-nested-or-expression` | `syntax-extension-candidate` | True | - |
| `490-event-reacquire-lock-detector` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `491-kcl-capacitor-ddt-current` | `kcl-syntax-candidate` | True | - |
| `492-kcl-inductor-idt-voltage` | `conservative-current/KCL-behavior-certified` | True | - |
| `493-continuous-laplace-nd-filter` | `behavioral-continuous-time-candidate` | True | - |
| `494-continuous-zi-nd-filter` | `behavioral-continuous-time-candidate` | True | - |
| `495-supply-bias-validity-gate` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `496-reference-settling-window-monitor` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `497-power-enable-turnon-delay-gate` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `498-power-mode-supply-current-metric` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `499-dynamic-supply-level-driver` | `behavior-extension-candidate` | False | `negative_descriptions_not_task_specific` |
| `500-rail-ramp-rate-startup-monitor` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `501-differential-common-mode-window-monitor` | `behavior-extension-candidate` | False | `negative_cases_index_mismatch`<br>`negative_descriptions_not_task_specific` |
| `502-sine-vco-idtmod-bound-step` | `behavior-extension-candidate` | True | - |
| `503-differential-vco-clip-idtmod` | `behavior-extension-candidate` | True | - |
| `504-charge-pump-pfd-state-machine` | `behavior-extension-candidate` | True | - |
| `505-fractional-n-divider-accumulator-flow` | `behavior-extension-candidate` | True | - |
