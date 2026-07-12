# Slew Rate DAC4

## Task Contract

Implement the DUT Verilog-A source file `slew_rate_dac4.va`. This is an L1
data-converter task: a four-bit DAC whose analog output is limited by a public
slew-rate parameter.

## Public Verilog-A Interface

```verilog
module slew_rate_dac4(d3, d2, d1, d0, vout);
```

All ports are electrical. `d3` is the MSB, `d0` is the LSB, and `vout` is the
analog DAC output.

## Public Parameter Contract

- `vth = 0.45 V`: input logic threshold.
- `vref = 1.0 V`: full-scale endpoint reference.
- `slewrate = 1e8 V/s`: maximum output slew rate.

## Required Behavior

Interpret the four input voltages as an unsigned binary code using `vth`.
Map code zero to 0 V and code fifteen to `vref`, with monotonic binary-weighted
steps between those endpoints. Drive `vout` with slew-rate-limited analog
motion so large code changes ramp at the configured `slewrate` instead of
jumping immediately to the final value.

## Modeling Constraints

Use voltage-domain Verilog-A and the `slew()` analog operator for the output
transition behavior. Do not hard-code example harness stimulus times, private sample
points, or private-grading-only vectors.

## Output Contract

Return only `slew_rate_dac4.va` implementing the public module. The file must
compile under the simulator-compatible Verilog-A and must not require additional
modules, include files, or example harness changes.
