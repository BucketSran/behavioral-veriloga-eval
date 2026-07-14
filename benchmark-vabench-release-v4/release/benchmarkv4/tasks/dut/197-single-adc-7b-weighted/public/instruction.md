# Single ADC 7b Weighted

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter weighted decoder.
- Target artifact: `single_adc_7b_weighted.va`.
- Role: single-ended 7-bit weighted ADC code-to-voltage decoder.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module single_adc_7b_weighted(din0, din1, din2, din3, din4, din5, din6, dout);
```

`din0..din6` are voltage-coded input bits and `dout` is the analog weighted output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vth = 0.45`. The public weights from `din0` through `din6` are `0.25, 0.5, 1, 2, 4, 8, 16`.

## Required Behavior

Treat each input as high when above `vth`. Sum the selected weights and drive the normalized single-ended ADC output according to the public weight basis. The output should be monotonic with the weighted code and held as a smooth voltage contribution.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `single_adc_7b_weighted.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
