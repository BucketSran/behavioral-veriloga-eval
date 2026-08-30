# vaBench Release Taxonomy

> **Historical document — not a current operating guide.**
> Use the [current documentation](README.md) for VABench r53 + EVAS 0.8.7.
> Retained earlier-release taxonomy and script input; its counts are not the current r53 denominator.

Date: 2026-05-26

This is the clean release-facing taxonomy for the current 79-entry
vaBench release. It is the benchmark coverage contract and should be read
together with the current certification and score-denominator reports.

The scored benchmark surface is L1/L2 behavioral analog/mixed-signal circuit
work. L0 EVAS/Spectre conformance cases are maintained separately because they
validate evaluator semantics rather than model capability on a circuit task.
Within L1/L2, Measurement/Testbench Instrumentation and Stimulus/Sources are
support categories: they can be certified as reusable behavioral modeling
tasks, but they are reported as a support suite and excluded from the core
analog circuit-function score denominator.

## Selection Principle

vaBench is organized around analog/mixed-signal circuit-function completeness
first. A release entry should be a recognizable behavioral model for a real IC
function, macro helper, measurement flow, source, or composed circuit flow. It
does not need to be selected only because Verilog-A is used for simulation
acceleration, but it must have independent circuit or verification value.

EVAS compatibility is the implementation boundary rather than the benchmark
motivation. Scored entries should be expressible in the supported
voltage-domain/event-driven Verilog-A subset and should be checkable from
public waveform or metric observables. Entries whose primary value is syntax,
parser, scheduling, or checker-regression coverage belong in L0 conformance,
not in the L1/L2 benchmark score.

## Level Rules

| Level | Meaning | Counted in vaBench score |
| --- | --- | --- |
| L0 conformance | Single-cause Verilog-A, simulator, event, source, or checker semantic. | No; report separately as EVAS/Spectre health. |
| L1 function | One reusable circuit function with a clear module contract and measurable behavior. | Yes for `track=core`; support rows are reported separately. |
| L2 complete circuit | A composed circuit form with multiple interacting L1 functions or a complete mixed-signal flow. | Yes for `track=core`; support rows are reported separately. |

Task form is orthogonal to level. A task may be `dut`, `tb`, `bugfix`, or
`e2e`; an `e2e` task counts as L2 only when it genuinely composes multiple
interacting functions.

## Track and Difficulty Rules

`track` is orthogonal to `level`.

| Track | Meaning | Score role |
| --- | --- | --- |
| `core` | Analog/mixed-signal circuit blocks and composed circuit flows. | Enters the main benchmark score after certification. |
| `support` | Reusable measurement, instrumentation, stimulus, and source-generation behavior. | Certified and reported separately; excluded from the core circuit score. |

`difficulty` is also orthogonal to `level`.

| Difficulty | Meaning |
| --- | --- |
| `D1` | Direct single-function behavior with a compact numeric contract. |
| `D2` | Stateful, timed, trimmed, or parameterized single-function behavior. |
| `D3` | Composed or closed-flow behavior, including all L2 tasks and the L1 pipeline ADC stage. |

## Certification Contract

Every released task must provide:

| Field | Requirement |
| --- | --- |
| Public prompt | Names behavior, ports, artifacts, and observables without leaking gold implementation. |
| Metadata | Includes release category, level, task form, source files, expected backend, and provenance. |
| Checker | Deterministic public validation contract tied to the prompt. |
| Gold assets | Gold Verilog-A and reference testbench or source artifacts. |
| Evidence | Static integrity, EVAS gold validation, and Spectre gold validation links. |

The current 79-entry package is materialized, static-certified, and
EVAS/Spectre-certified across all 271 forms with zero EVAS PASS / Spectre FAIL
mismatches. The current core score denominator is enabled for 66 core entries /
236 core forms. The 13-entry / 35-form support suite remains certified and
reported, but outside that core denominator.

## Function-Level Checker Contract

| Category | Verification angle | Minimum checker metrics |
| --- | --- | --- |
| Data Converter Models | Code, unit selection, or quantizer threshold maps to the intended analog/code output. | Representative code coverage, monotonicity, endpoint behavior, saturation/clamping, and rejection of missing MSB/unit segments. |
| Comparator and Decision Circuits | Decision block switches at the intended threshold, hysteresis window, clock phase, or delay. | Correct polarity, threshold/hysteresis transitions, bounded delay or evaluate/reset windows, and no stuck output. |
| PLL Clock and Timing Systems | Event relation produces intended phase, pulse, divider, or frequency response. | Edge counts, pulse direction and overlap bounds, phase/frequency trend, wrap behavior, and late-window behavior. |
| Calibration, DEM, and Control | Controller updates state in the correct signed direction while respecting bounds and sequence rules. | Signed movement outside deadband, hold inside deadband, clamp behavior, wrap/rotation correctness, and convergence when specified. |
| Baseband Signal Conditioning | Analog transform implements intended gain, filter, limiting, integration, or slew behavior. | Gain/slope/lag estimates, bounded output, reset behavior, limiting/slew constraints, and representative transient response. |
| Sampling and Analog Memory | Sampled value, held value, droop/leakage, or aperture/acquisition timing matches the contract. | Sample instant alignment, hold stability, droop/leakage slope, aperture/acquisition behavior, and rejection of transparent-through behavior. |
| Bias Reference and Power Management | Bias, reference, reset, and regulator macromodels produce intended supply/reference state across enable, trim, ramp, and load events. | Startup threshold, trim slope, reset/UVLO polarity, regulated output/load recovery, and no stuck or rail-only output. |
| RF and AFE Behavioral Macromodels | RF/AFE voltage-domain macromodels capture gain, compression, mixing, detection, limiting, and composed receiver behavior without transistor RF physics. | Gain/compression trend, LO polarity or I/Q schedule, envelope/RSSI monotonicity, limiting bounds, AGC convergence, and phase/quadrature separation. |
| Measurement Instrumentation Flows | Generated measurement matches the waveform quantity it claims to report. | Metric-to-waveform agreement, one-record artifact format where required, tolerance-window semantics, and no final-row artifact passing. |
| Stimulus and Source Generators | Source generates the specified waveform schedule or deterministic sequence. | Amplitude/range, timing, burst count, periodicity or deterministic variation, and reproducibility. |

## Coverage Counts

| Pool | Count | Score status |
| --- | ---: | --- |
| Current promoted L1 seeds | 22 | Included when `track=core` and certified. |
| Promoted top-level L1 additions | 40 | Materialized additions that expand the core/support coverage contract. |
| Selected L2 package targets | 17 | Complete-circuit targets after removing duplicate kernels. |
| Top-level L1/L2 package target | 79 | 62 L1 + 17 L2 rows, split into 66 core entries and 13 support entries. |
| Core content denominator | 66 entries / 236 forms | Full certified core content target. |
| Current scored denominator | 66 entries / 236 forms | Enabled for certified `track=core` rows. |
| Support suite | 13 entries / 35 forms | Report separately; excluded from the core circuit score. |
| Materialized task forms | 271 | Static-certified and EVAS/Spectre-certified with zero pending forms. |
| Difficulty split | D1=7, D2=54, D3=18 | Difficulty is orthogonal to L1/L2 and core/support. |

## Release Coverage Table

| Category | Base function | Level | Required task forms | Score surface |
| --- | --- | --- | --- | --- |
| Data Converter Models | Simple 4-bit binary-coded DAC | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Unit-element thermometer DAC | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Segmented DAC | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Thermometer-code decoder | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Clocked ADC quantizer | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Capacitive/weighted SAR feedback DAC | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | DAC mismatch/unit-weighting model | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | SAR logic | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Pipeline ADC MDAC stage | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Data Converter Models | Converter static linearity measurement flow | L2 | e2e; tb | benchmark-e2e |
| Data Converter Models | Weighted SAR ADC/DAC loop | L2 | e2e; tb | benchmark-e2e |
| Data Converter Models | Flash ADC mini-array | L2 | e2e; tb | benchmark-e2e |
| Data Converter Models | Pipeline ADC residue chain | L2 | e2e; tb | benchmark-e2e |
| Comparator and Decision Circuits | Threshold comparator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Propagation-delay comparator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Hysteresis comparator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Window comparator/detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Offset comparator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | StrongARM-style latch comparator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Comparator debounce latch | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Comparator and Decision Circuits | Single-ramp comparator offset measurement flow | L2 | e2e; tb | benchmark-e2e |
| PLL Clock and Timing Systems | VCO phase integrator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | PFD UP/DN logic | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Bang-bang phase detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Digital phase accumulator with modulo wrap | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Clock divider | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Lock detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Voltage-domain charge-pump control abstraction | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | Sampled loop-filter abstraction | L1 | dut; tb; bugfix; e2e-form | model-capability |
| PLL Clock and Timing Systems | ADPLL lock/ratio-hop/timer flow | L2 | e2e; tb | benchmark-e2e |
| PLL Clock and Timing Systems | CPPLL tracking and frequency-step reacquire flow | L2 | e2e; tb | benchmark-e2e |
| Calibration, DEM, and Control | Trim-voltage generator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | Gain trim controller | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | DWA/DEM encoder | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | Calibration deadband controller | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | Successive-approximation calibration/search FSM | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | Element shuffler | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Calibration, DEM, and Control | Complete calibration loop | L2 | e2e; tb | benchmark-e2e |
| Baseband Signal Conditioning | First-order lowpass | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Resettable integrator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Soft/hysteretic limiter | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Precision rectifier/envelope detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Higher-order filter | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Slew-rate limiter | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Programmable gain amplifier | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Baseband Signal Conditioning | Amplifier/filter chain | L2 | e2e; tb | benchmark-e2e |
| Sampling and Analog Memory | Aperture-delay track-and-hold | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Sampling and Analog Memory | Sample-and-hold with droop/leakage | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Sampling and Analog Memory | Clocked sample-and-hold | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Sampling and Analog Memory | Acquisition-limited sample-and-hold | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Sampling and Analog Memory | Converter front-end | L2 | e2e; tb | benchmark-e2e |
| Bias Reference and Power Management | Bandgap reference macro model | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | PTAT/CTAT reference generator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | Bias voltage generator with enable/trim | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | Power-on reset detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | UVLO/brownout detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | LDO regulator macro model | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Bias Reference and Power Management | Reference startup enable flow | L2 | e2e; tb | benchmark-e2e |
| Bias Reference and Power Management | LDO load-step recovery flow | L2 | e2e; tb | benchmark-e2e |
| RF and AFE Behavioral Macromodels | LNA gain-compression macro | L1 | dut; tb; bugfix; e2e-form | model-capability |
| RF and AFE Behavioral Macromodels | RF mixer downconverter macro | L1 | dut; tb; bugfix; e2e-form | model-capability |
| RF and AFE Behavioral Macromodels | PA compression macro | L1 | dut; tb; bugfix; e2e-form | model-capability |
| RF and AFE Behavioral Macromodels | Log/RSSI power detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| RF and AFE Behavioral Macromodels | Limiting amplifier frontend | L1 | dut; tb; bugfix; e2e-form | model-capability |
| RF and AFE Behavioral Macromodels | AGC receiver leveling loop | L2 | e2e; tb | benchmark-e2e |
| RF and AFE Behavioral Macromodels | I/Q downconversion chain | L2 | e2e; tb | benchmark-e2e |
| Measurement Instrumentation Flows | Crossing metric writer | L1 | tb; dut; e2e-form | model-capability |
| Measurement Instrumentation Flows | Settling response measurement helper | L1 | tb; e2e-form | model-capability |
| Measurement Instrumentation Flows | Peak detector | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Measurement Instrumentation Flows | Gain estimator | L1 | tb; e2e-form | model-capability |
| Measurement Instrumentation Flows | Edge interval timer | L1 | tb; e2e-form | model-capability |
| Measurement Instrumentation Flows | Measurement flow | L2 | e2e; tb | benchmark-e2e |
| Measurement Instrumentation Flows | Gain extraction/convergence measurement flow | L2 | e2e; tb | benchmark-e2e |
| Stimulus and Source Generators | PRBS stimulus/dither generator | L1 | dut; tb; bugfix; e2e-form | model-capability |
| Stimulus and Source Generators | Periodic phase-ramp guard source | L1 | tb; dut; e2e-form | model-capability |
| Stimulus and Source Generators | Burst clock source | L1 | tb; dut; e2e-form | model-capability |
| Stimulus and Source Generators | Dither or noise-like deterministic source | L1 | tb; dut; e2e-form | model-capability |
| Stimulus and Source Generators | Sine/periodic voltage source | L1 | tb; dut; e2e-form | model-capability |
| Stimulus and Source Generators | Programmable stimulus sequencer | L2 | e2e; tb | benchmark-e2e |

## Rebalance Boundary

The following rows were removed from the release target because they were weak,
duplicative, or too close to support logic rather than analog/mixed-signal
behavioral circuit modeling: ADC code capture register, serializer frame
aligner, serial readout deserializer, serializer frame-alignment flow,
conversion event controller, PFD small phase-error response, XOR phase detector,
PLL timing slice, rotating DEM selector, and windowed DEM pointer.

Two stronger analog rows were added during that rebalance:
acquisition-limited sample-and-hold and programmable gain amplifier. Later
coverage work added CT07 bias/reference/power-management macromodels and CT08
RF/AFE behavioral macromodels; these core rows are now static-certified,
EVAS/Spectre-certified, and included in the 66-entry / 236-form scored core
denominator.
