# DC Aware ADC3bit

## Task Contract

Implement the DUT Verilog-A source file `dc_aware_adc3bit.va`. This is an L1
data-converter task: a static three-bit ADC that remains valid without a
sampling clock.

## Public Verilog-A Interface

```verilog
module dc_aware_adc3bit(vin, d2, d1, d0);
```

All ports are electrical. `vin` is the analog input. `d2` is the MSB and `d0`
is the LSB of the voltage-coded output word.

## Public Parameter Contract

- `vref = 1.0 V`: input full-scale reference.
- `vh = 0.9 V`: output logic-high voltage.
- `tr = 20p`: output transition smoothing time.

## Required Behavior

Model a static, analysis-friendly three-bit ADC. Clip `vin` to the 0-to-`vref`
range, quantize the clipped value into eight uniform output codes, and drive
`d2..d0` as the binary representation of that code. The conversion is
combinational/static rather than clocked: the output word should represent the
current input level after transition smoothing, including at the beginning of a
transient run.

## Modeling Constraints

Use voltage-domain Verilog-A with smooth output transitions. Do not introduce a
clock, private state, example harness-specific sample times, private private grader vectors,
current contributions, `ddt()`, or `idt()`.

## Output Contract

Return only `dc_aware_adc3bit.va` implementing the public module. The file must
compile under the simulator-compatible Verilog-A and must not require additional
modules, include files, or example harness changes.
