# Clocked ADC Quantizer

## Task Contract

Implement the single-DUT Verilog-A artifact `flash_adc_3b.va` for a clocked
three-bit flash-style ADC quantizer. The model should be a reusable
voltage-domain data-converter primitive, not a testbench or validation wrapper.

## Public Verilog-A Interface

The file `flash_adc_3b.va` must define:

```verilog
module flash_adc_3b(VDD, VSS, VIN, CLK, DOUT2, DOUT1, DOUT0);
```

All ports are electrical. `VDD` and `VSS` provide the output logic rails,
`VIN` is the analog input, `CLK` is the sampling clock, and `DOUT2`,
`DOUT1`, and `DOUT0` are voltage-coded output bits from MSB to LSB.

## Public Parameter Contract

- `vrefp = 0.9 V`: upper endpoint of the conversion range.
- `vrefn = 0.0 V`: lower endpoint of the conversion range.
- `vth = 0.45 V`: rising-clock threshold.
- `tedge = 100p`: output transition smoothing time.

These parameters may be overridden by the validation harness.

## Required Behavior

On each rising crossing of `CLK` through `vth`, quantize `VIN` into one of
eight uniform bins spanning `vrefn` to `vrefp`. Clamp the sampled code to the
inclusive range 0 through 7 and hold that code until the next rising clock
event.

Drive `DOUT2`, `DOUT1`, and `DOUT0` as the binary representation of the held
code, using `VDD` for logic 1 and `VSS` for logic 0. The output bits must remain
stable between sampling events.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A with event-driven sampling and smoothed
output transitions. Do not emit a testbench, validation logic, waveform
post-processing code, current contributions, transistor-level devices, `ddt()`,
`idt()`, or testbench-specific timing constants inside the DUT.

## Output Contract

Return exactly one complete Verilog-A source artifact named `flash_adc_3b.va`.
Do not include explanatory prose outside the source artifact contents.
