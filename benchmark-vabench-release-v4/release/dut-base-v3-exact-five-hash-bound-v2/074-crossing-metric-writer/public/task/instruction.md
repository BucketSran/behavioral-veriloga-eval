# Crossing Metric Writer

## Task Contract

Implement the requested Verilog-A artifact for `Crossing Metric Writer`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `file_metric_writer.va`

Implement `file_metric_writer.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module file_metric_writer(vin, done);
```

Inputs:

- `vin`: electrical input being monitored.

Outputs:

- `done`: electrical completion flag.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `filename` | `"metric.out"` | Relative metric-file basename opened by the model at startup in the runner-provided writable working directory. Do not require or emit absolute paths or directory traversal. |
| `vth` | `0.45 V` | Rising-crossing threshold for `vin`. |
| `tr` | `300 ps` | Rise/fall smoothing for `done`. |

## Required Behavior

Write a pure voltage-domain measurement helper that records the first rising
threshold crossing of `vin`.

Required observable behavior:

- Open the relative basename `filename` on `initial_step`.
- On the first rising crossing of `vin` through `vth`, write the crossing time
  to the metric file and latch completion.
- The file content must be exactly one text record of the form `cross <time_seconds>` followed by a newline.
- Keep `done` low before the first crossing and high after completion.
- Ignore later crossings after the first recorded event.

Use voltage contributions only. Smooth the `done` output with `transition()`.
Do not generate a the simulator example harness, waveform files, validation artifacts,
transistor-level devices, current contributions, `ddt()`, or `idt()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named `file_metric_writer.va`.
