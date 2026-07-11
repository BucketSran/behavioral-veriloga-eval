# Pipeline ADC Chain 4b

## Task Contract

Implement the requested Verilog-A artifact for `Pipeline ADC Chain 4b`.
- Form: `dut`
- Level: `L2`
- Category: `data_converter_models`
- Target artifact(s): `pipeline_adc_chain_4b.va`

Implement one Verilog-A source file named `pipeline_adc_chain_4b.va`.

## Public Verilog-A Interface

```verilog
module pipeline_adc_chain_4b(VDD, VSS, VIN, CLK, RES1, RES2, S1B1, S1B0, S2B1, S2B0, DOUT3, DOUT2, DOUT1, DOUT0);
```

All ports are electrical. `VDD` and `VSS` are the supply rails, `VIN` is the
sampled analog input, `CLK` is the conversion strobe, `RES1` and `RES2` expose
the first-stage and second-stage residue voltages, `S1B1/S1B0` and
`S2B1/S2B0` expose the two stage decisions, and `DOUT3..DOUT0` expose the final
4-bit code with `DOUT3` as MSB.

## Public Parameter Contract

- `vrefp = 0.9 V`: positive conversion reference.
- `vrefn = 0.0 V`: negative conversion reference.
- `vth = 0.45 V`: threshold for voltage-coded clock and output-bit logic.
- `tedge = 100p`: transition smoothing time for residue and bit outputs.

## Required Behavior

This is an L2 pipeline-ADC residue-chain component. On each rising crossing of
`CLK`, clip `VIN` to the `vrefn`-to-`vrefp` range and perform a two-stage
2-bit/stage conversion.

Stage 1 makes a 2-bit coarse decision from the clipped input. It should output
that decision on `S1B1/S1B0`, compute the center of the selected quarter-scale
bin, amplify the input error from that center by four, and drive the clipped
first residue on `RES1`.

Stage 2 quantizes `RES1` with the same 2-bit quarter-scale rule. It should
output the backend decision on `S2B1/S2B0`, compute the second residue with the
same gain-of-four residue rule, and drive the clipped backend residue on
`RES2`.

The final output word is the stage-1 decision concatenated with the stage-2
decision: `DOUT3/DOUT2` are the stage-1 bits and `DOUT1/DOUT0` are the stage-2
bits. High logic outputs should be near `VDD`; low logic outputs should be near
`VSS`.

**Public Verification Context**

The public transient scenario drives representative points across all 16 final
4-bit code bins, alternates lower-half and upper-half points inside adjacent
bins, and observes `vin`, `clk`, `res1`, `res2`, the stage bits, and the final
code bits. Treat that scenario as observable verification context, not as values
to hard-code into the DUT.

## Modeling Constraints

Use voltage-domain event-driven Verilog-A only. Do not emit a Spectre
testbench, validation logic, specific waveform sample points, current
contributions, transistor-level devices, AC/noise analysis, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `pipeline_adc_chain_4b.va`. Do not include explanatory prose outside the source artifact contents.
