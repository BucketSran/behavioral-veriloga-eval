# Gain Estimator

## Task Contract

Implement the requested Verilog-A artifact for `Gain Estimator`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `gain_estimator.va`

Implement `gain_estimator.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module gain_estimator(VDD, VSS, vinp, vinn, voutp, voutn, gain_out, valid);
```

Ports:

- `VDD`, `VSS`: electrical supply/reference rails.
- `vinp`, `vinn`: electrical differential input being measured.
- `voutp`, `voutn`: electrical differential output being measured.
- `gain_out`: electrical voltage-coded gain metric.
- `valid`: electrical completion flag using the `VDD/VSS` logic range.

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real sample_period = 1n from (0:inf);` in `gain_estimator.va`.
- `parameter real start_time = 20n;` in `gain_estimator.va`.
- `parameter real gain_scale = 10.0 from (0:inf);` in `gain_estimator.va`.
- `parameter real min_input_span = 0.02 from (0:inf);` in `gain_estimator.va`.
- `parameter real tedge = 200p from (0:inf);` in `gain_estimator.va`.

## Required Behavior

Write a pure voltage-domain gain measurement helper. After a configurable start
time, sample the input and output differential spans on a periodic timer. Once
the observed input span is large enough, report the span ratio as a normalized
voltage metric and assert `valid`.

Public parameters:

- `sample_period = 1 ns`: timer interval for span updates.
- `start_time = 20 ns`: time before samples begin contributing to the spans.
- `gain_scale = 10.0`: gain value represented by a full-scale `gain_out`.
- `min_input_span = 0.02 V`: minimum observed input span before the metric is
  considered valid.
- `tedge = 200 ps`: rise/fall smoothing for `gain_out` and `valid`.

Required observable behavior:

- Track minimum and maximum values of `V(vinp,vinn)` and `V(voutp,voutn)` after
  `start_time`.
- Compute input and output spans from those extrema.
- When input span exceeds `min_input_span`, set `gain = output_span/input_span`
  and assert `valid`.
- Drive `gain_out` as `V(VDD,VSS) * gain / gain_scale`.
- Drive `valid` low before the metric is valid and high afterwards.

Use event-updated real state for the measured gain and validity flag. Smooth
only discrete metric targets with `transition()`. Do not generate a Spectre
testbench, waveform files, validation artifacts, transistor-level devices, current
contributions, `ddt()`, or `idt()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named `gain_estimator.va`.
