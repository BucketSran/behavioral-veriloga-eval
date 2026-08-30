# vaBench Top-Level Positioning

> **Historical document — not a current operating guide.**
> Use the [current documentation](README.md) for VABench r53 + EVAS 0.8.7.
> Retained earlier paper/release wording; current scope follows the r53 manifest and agent contract.

Date: 2026-05-15

This is the current top-level wording for vaBench after reviewing duplicate
function risk, analog/mixed-signal IC terminology, historical examples, and
EVAS/Spectre validation needs.

## One-Sentence Positioning

vaBench is a Verilog-A behavioral benchmark for analog/mixed-signal IC modeling,
organized by circuit function and certified with EVAS/Spectre evidence; EVAS is
the fast debug evaluator, while Spectre remains the reference simulator for
gold promotion and paper-facing claims.

Reference simulator should be read as a Spectre-equivalence target, not a demand
for EVAS to exceed Spectre numerical precision. `spectre/classic` is the
conservative non-X reference path, while `spectre/ax` is the fast official
baseline for speed comparisons; EVAS should match the task behavior and remain
within the practical AX/classic waveform tolerance envelope.

## Benchmark Selection Principle

The benchmark is selected for circuit-function completeness first. Verilog-A
simulation acceleration is an important motivation for behavioral modeling, but
it is not the only reason an entry belongs in vaBench. A task can be valuable
when it covers a common analog/mixed-signal function, macro helper,
measurement/testbench behavior, source model, or composed circuit flow that
designers would plausibly use in system-level IC modeling.

EVAS compatibility is the certification and execution boundary: scored entries
must stay within the supported voltage-domain/event-driven subset and expose
observable behavior that deterministic checkers can validate. Pure evaluator
feature tests remain L0 conformance rather than L1/L2 benchmark content.

## Scoring Surface

| Surface | What it contains | Counted in vaBench score | Paper role |
| --- | --- | --- | --- |
| L1 core circuit functions | Reusable behavioral IC blocks such as DACs, ADC quantizers, comparators, VCO/PFD/dividers, calibration/DEM, filters, limiters, and sample/hold blocks. | Yes | Main model-capability score. |
| L2 core circuit flows | Multi-block or closed-loop flows such as converter chains, PLL slices, calibration loops, analog signal chains, and converter front-end flows. | Yes | Higher-level composition score. |
| Support measurement/stimulus functions | Measurement and stimulus models when they have a real reusable circuit/testbench contract. | No for the core circuit score; report as a separate support suite. | Shows benchmark can evaluate testbench and instrumentation tasks without letting them inflate core circuit coverage. |
| L0 conformance | Syntax legality, source parsing, event scheduling, sampling, and checker semantics. | No | EVAS/Spectre health and regression evidence. |
| Historical evidence | main120, benchmark-v2, benchmark-balanced, smoke tasks, examples. | No, unless materialized into a certified task. | Discovery source and provenance. |

Paper-facing coverage should keep two denominators visible: core circuit
coverage for analog/mixed-signal blocks and flows, and support coverage for
measurement/stimulus entries. The support suite tests whether a model can write
reusable measurement artifacts and source/schedule behavior, but it must not be
used to inflate the count of core signal-path or decision-circuit functions.

## Current Count Vocabulary

| Pool | Count | Meaning |
| --- | ---: | --- |
| Current promoted L1 seed functions | 22 | Countable current-seed functions retained in the release package after duplicate/removal policy. |
| Promoted top-level L1 additions | 40 | Additional L1 functions selected into the release coverage contract. |
| Selected L2 complete-circuit targets | 17 | System/flow tasks selected into the release coverage contract because they compose multiple L1 functions after duplicate kernels were removed. |
| Top-level L1/L2 coverage target | 79 | 66 core circuit entries plus 13 measurement/stimulus support entries, before task-form multiplication. |
| Core score denominator | 66 entries / 236 forms | Certified `track=core` rows currently counted by `score_denominator_manifest.json`. |
| Support suite | 13 entries / 35 forms | Measurement/stimulus rows reported separately from the main circuit-function score. |
| Removed weak/duplicate entries in the rebalance | 10 | Readout/control/PLL/DEM duplicates were removed from the core release set. |

The release score counts only materialized and certified `track=core` tasks.
Support tasks are still certified benchmark assets, but remain outside the main
analog circuit-function denominator.

## Ten Top-Level Categories

| Category | Role in benchmark | Review decision |
| --- | --- | --- |
| Data Converter Models | DAC, ADC, decoder, SAR, and converter-loop behavior. | Core. This should be one of the largest categories. |
| Comparator and Decision Circuits | Threshold, offset, clocked, StrongARM-style, hysteresis, delay, and window-decision behavior. | Core. Keep detector tasks here when output is a binary decision. |
| PLL Clock and Timing Systems | VCO, PFD, divider, lock detector, phase accumulator, voltage-domain charge-pump abstraction, sampled loop-filter abstraction, and PLL flows. | Core. Important for event scheduling and mixed-signal timing behavior. |
| Calibration, DEM, and Control | Trim controllers, DEM/DWA, pointer selection, element shuffling, gain calibration, and calibration loops. | Core. Must aggressively deduplicate pointer variants. |
| Measurement Instrumentation Flows | Crossing metrics, settling time, gain estimation, peak detection, and artifact-generating measurement flows. | Support suite. Valid benchmark content, but excluded from main circuit-function score claims. |
| Stimulus and Source Generators | Ramp, burst clock, deterministic noise, dither, and source-driven flows. | Support suite. Count only reusable source models, not source syntax/conformance cases; exclude from main circuit-function score. |
| Baseband Signal Conditioning | Lowpass, integrator, rectifier, clamp, slew limiter, gain amplifier, soft limiter, and signal chains. | Core. Avoid duplicate limiter/clamp variants unless transfer behavior differs. |
| Sampling and Analog Memory | Track/hold, aperture, droop/leakage, resettable hold, and converter front-end sampling. | Core. Important converter-front-end primitive. |
| Bias Reference and Power Management | Bandgap/PTAT/CTAT references, bias generators, LDO behavior, UVLO, POR, and startup/load-step flows. | Core. Important system-level analog support blocks; keep them as behavioral macromodels rather than transistor-level design tasks. |
| RF and AFE Behavioral Macromodels | LNA/mixer/limiter/RSSI/PA macromodels plus I/Q and AGC receiver flows. | Core. Capture voltage-domain RF/AFE behavior without claiming transistor RF physics or S-parameter accuracy. |

## Duplicate and Naming Policy

| Risk | Policy |
| --- | --- |
| Binary DAC versus thermometer DAC | Use "simple 4-bit binary-coded DAC" for the current mathematical code-to-voltage model. Use "unit-element thermometer DAC" only when thermometer-coded unit cells are modeled. |
| Decoder versus DAC | A thermometer-code decoder is digital/code-format logic for converter control. It is distinct from a DAC only when no analog reconstruction is claimed. |
| StrongARM-style latch comparator | Keep the latch-style comparator as the clocked comparator coverage point; avoid a separate generic clocked comparator unless it adds independently checked behavior beyond reset/evaluate timing. |
| DEM pointer variants | Count separate tasks only when the selection rule differs: rotating pointer, windowed pointer, no-overlap DWA, or full thermo-DWA encoder. Pure wraparound edge cases are L0/checker cases. |
| Clamp versus limiter | `voltage_clamp` covers hard saturation. Add a new limiter only if it is soft, hysteretic, or otherwise behaviorally distinct. |
| Sample/hold droop versus leaky hold | Treat as one function unless reset, aperture, or noise behavior is central and separately checked. |
| Measurement helper versus checker schema | Metric writers and estimators can be tasks; checker schema validation is L0 conformance, not L1 circuit function. |
| Source model versus source syntax | Ramp/burst/noise/dither generators can be tasks; PWL continuation and breakpoint semantics are L0 conformance. |

## Recommended Paper Wording

Use this wording:

> vaBench organizes behavioral Verilog-A tasks by analog/mixed-signal IC circuit
> function. Scored tasks are L1 reusable circuit functions or L2 composed
> circuit flows, with reusable measurement and stimulus entries reported as a
> separate support slice. A separate L0 conformance suite isolates EVAS/Spectre
> syntax, source, event, sampling, and checker semantics. Historical task trees
> and examples provide source traces and provenance, but a task enters the
> release score only after prompt, metadata, checker, gold assets, and
> EVAS/Spectre certification are reviewed.

Avoid this wording:

> vaBench has 28 functions.

Reason: the current-seed count and the full 79-entry release target are
different quantities and should be reported separately.

Also avoid:

> vaBench is based on examples/main120/benchmark-v2.

Reason: those are construction and provenance sources, not the benchmark
definition.

## Next Experimental Direction

1. Keep the current 79-entry package aligned with the score denominator,
   certification reports, and model-baseline protocol.
2. Run model baselines on the 66-entry / 236-form scored core denominator, with
   pinned strict EVAS as the formal judge and support rows excluded from the
   main score.
3. Run same-slice speed timing for every scored form before making a
   release-wide EVAS speedup claim.
4. Keep L0 conformance growth parallel but separate from benchmark scoring.
