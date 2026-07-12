# VA DAC 6b Single-Ended

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter weighted DAC.
- Target artifact: `va_dac_6b_se.va`.
- Role: ready-triggered single-ended 6-bit weighted DAC with fixed reference basis.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module va_dac_6b_se(din0, din1, din2, din3, din4, din5, rdy, aout);
```

`din0..din5` are voltage-coded DAC input bits, `rdy` is the update event, and `aout` is the analog output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vdd = 1.0` and `vth = 0.5`. Use `vth` for input-bit and ready-edge decisions.

## Required Behavior

On each rising `rdy` crossing, sample `din0..din5` with switched weights `0.5, 1, 2, 4, 8, 16` from `din0` through `din5`. Map the sampled weighted code to a bipolar single-ended output scaled by `vdd` using this public normalization:

```text
weighted_code = 16*din5 + 8*din4 + 4*din3 + 2*din2 + 1*din1 + 0.5*din0
aout = (weighted_code / 47.5) * 2.0 * vdd - vdd
```

Each `din*` term is `1` when the corresponding voltage is above `vth` and `0` otherwise. The denominator `47.5` is the fixed source normalization basis including the non-switching reference contribution.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `va_dac_6b_se.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
