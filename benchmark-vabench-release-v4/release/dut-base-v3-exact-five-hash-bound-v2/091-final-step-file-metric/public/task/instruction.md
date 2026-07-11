# Final Step File Metric

## Task Contract

Implement the requested Verilog-A artifact for `Final Step File Metric`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `final_step_file_metric_ref.va`

Implement `final_step_file_metric_ref.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module final_step_file_metric_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref,
    output electrical metric_out
);
```

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vth` | `0.45 V` | Rising-crossing threshold for `ref` relative to `VSS`. |
| `tedge` | `200 ps` | Rise/fall smoothing for `metric_out`. |

## Required Behavior

Write a pure voltage-domain measurement helper that counts rising reference
events during transient simulation, exposes a voltage-coded metric, and writes
the final metric at `final_step`.

Required observable behavior:

- Initialize the event count and metric to zero.
- On every rising crossing of `ref` through `vth`, increment the event count.
- Expose the normalized metric as `metric_out = V(VDD,VSS) * count / 4`.
- At `final_step`, write exactly one text metric record to the public basename
  `candidate.out` in the simulator working directory. The record format is
  `count=<integer> metric=<fixed-point>` and the metric value is the final
  normalized count divided by four, formatted to three digits after the decimal
  point.

Use voltage-coded logic referenced to `VDD` and `VSS`. Smooth only event-updated
metric state; do not feed a continuously varying branch expression directly
into `transition()`. Do not generate a Spectre testbench, waveform files,
validation artifacts, transistor-level devices, current contributions, `ddt()`, or
`idt()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named
`final_step_file_metric_ref.va`.
