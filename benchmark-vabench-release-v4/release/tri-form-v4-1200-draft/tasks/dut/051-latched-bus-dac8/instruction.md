# Latched Bus DAC8

## Task Contract

Implement the DUT Verilog-A source file `latched_bus_dac8.va`. This is an L1
data-converter task: an eight-bit bus DAC with clocked update and hold behavior.

## Public Verilog-A Interface

```verilog
Declare module `latched_bus_dac8` with the positional ports listed below.
```

All ports are electrical. `vclk` is the update clock. `b7` is the MSB, `b0` is
the LSB, and `vout` is the analog DAC output.

## Public Parameter Contract

- `vth = 0.45 V`: threshold for the clock and input bits.
- `vref = 1.0 V`: full-scale endpoint reference.
- `tr = 20p`: output transition smoothing time.

## Required Behavior

On each rising crossing of `vclk` through `vth`, sample the eight input bits and
latch the unsigned binary code. Hold the previously latched code between update
edges even if the input bus changes. Map code zero to 0 V and code 255 to
`vref`, with monotonic binary-weighted steps between those endpoints.

## Modeling Constraints

Use voltage-domain event-driven Verilog-A. Do not make `vout` transparently
follow the input bus between clock edges, hard-code public example harness times,
private sample points, current contributions, `ddt()`, or `idt()`.

## Output Contract

Return only `latched_bus_dac8.va` implementing the public module. The file must
compile under the simulator-compatible Verilog-A and must not require additional
modules, include files, or example harness changes.
