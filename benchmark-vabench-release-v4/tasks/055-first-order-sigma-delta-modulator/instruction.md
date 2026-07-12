# First Order Sigma Delta Modulator

## Task Contract

Implement the DUT Verilog-A source file `first_order_sigma_delta_modulator.va`.
This is an L1 data-converter task: a clocked first-order sigma-delta modulator
with a one-bit voltage-coded output stream.

## Public Verilog-A Interface

```verilog
Declare module `first_order_sigma_delta_modulator` with the positional ports listed below.
```

All ports are electrical. `vin` is the normalized analog input, `vclk` is the
modulator clock, and `bitout` is the voltage-coded one-bit output stream.

## Public Parameter Contract

- `vth_clk = 0.45 V`: clock threshold.
- `vh = 0.9 V`: output logic-high level.
- `vref = 1.0 V`: normalized feedback reference.
- `tr = 20p`: output transition smoothing time.

## Required Behavior

Maintain a first-order accumulator. On each rising crossing of `vclk`, update
the accumulator with the current normalized input minus the previous one-bit
feedback value. Publish the next output bit high when the updated accumulator
is nonnegative and low otherwise. The output stream should therefore have a
higher pulse density for larger `vin` values while keeping the accumulator
bounded by the feedback action.

## Modeling Constraints

Use voltage-domain event-driven Verilog-A. Do not hard-code the public
example harness waveform, private sample points, or private-grading-only bit sequences.

## Output Contract

Return only `first_order_sigma_delta_modulator.va` implementing the public
module. The file must compile under the simulator-compatible Verilog-A and must not
require additional modules, include files, or example harness changes.
