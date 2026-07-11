# Settling Time Measurement

## Task Contract

Implement the requested Verilog-A artifact for `Settling Time Measurement`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `settling_time_measurement_tb.va`

Implement `settling_time_measurement_tb.va` in Verilog-A. Despite the
historical filename suffix, this artifact is the DUT measurement macro, not a
Spectre testbench.

## Public Verilog-A Interface

```verilog
module settling_time_measurement_tb(step, vout, done);
```

Inputs:

- `step`: electrical input step stimulus.

Outputs:

- `vout`: electrical settling-response output.
- `done`: electrical completion flag.

## Public Parameter Contract

Expose `parameter real tr = 300p;` as the output transition smoothing time for
`vout` and `done`. Testbenches may override `tr` with a nonnegative value.

## Required Behavior

This is a measurement-helper DUT task, not a Spectre testbench-generation task.
Return only the Verilog-A source file `settling_time_measurement_tb.va`.

Use a 1 ns timer update to model a first-order settling response:

```text
y += 0.04 * (V(step) - y)
```

Drive `vout` from the internal state `y` using `tr` for transition smoothing.
Drive `done` low before the settling
boundary and high only after the simulation time is beyond 120 ns and the
settled state is above 0.75 V. The validation applies a step input, runs past
the 120 ns boundary, and saves `step`, `vout`, and `done`.

Use voltage-coded logic with a 0.45 V threshold where applicable. Drive high
logic outputs near 0.9 V and low outputs near 0 V. Keep the model pure
behavioral Verilog-A.

Do not generate a Spectre `.scs` file despite the historical `_tb` filename.
Do not use transistor-level devices,
AC/noise analysis, current contributions, waveform files, validation artifacts, or
simulator side channels.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named
`settling_time_measurement_tb.va`. Do not include explanatory prose outside the
source artifact contents.
