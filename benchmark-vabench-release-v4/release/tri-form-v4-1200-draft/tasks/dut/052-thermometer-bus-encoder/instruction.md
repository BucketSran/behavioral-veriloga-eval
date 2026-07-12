# Thermometer Bus Encoder

## Task Contract

Implement the DUT Verilog-A source file `thermometer_bus_encoder.va`. This is
an L1 data-converter task: an analog-input thermometer bus encoder with ordered
voltage-coded segment outputs.

## Public Verilog-A Interface

```verilog
module thermometer_bus_encoder(vin, t0, t1, t2, t3, t4, t5, t6, t7,
                               t8, t9, t10, t11, t12, t13, t14, t15);
```

All ports are electrical. `vin` is a normalized analog input. `t0..t15` are
voltage-coded thermometer outputs ordered from the lowest segment to the
highest segment.

## Public Parameter Contract

- `vref = 1.0 V`: input full-scale reference.
- `vh = 0.9 V`: output logic-high level.
- `tr = 20p`: output transition smoothing time.

## Required Behavior

Convert `vin` into a 16-segment thermometer code. Clip the input to the
0-to-`vref` range, choose the number of active segments from the clipped input
level, and drive a prefix thermometer word: `t0` is the first segment to turn
on, then `t1`, and so on up to `t15`. The output must remain monotonic with
the input and must not emit a binary-coded word.

## Modeling Constraints

Use voltage-domain Verilog-A with smooth output transitions. Do not hard-code
example harness stimulus times, private sample points, or private-grading-only vectors.

## Output Contract

Return only `thermometer_bus_encoder.va` implementing the public module. The
file must compile under the simulator-compatible Verilog-A and must not require
additional modules, include files, or example harness changes.
