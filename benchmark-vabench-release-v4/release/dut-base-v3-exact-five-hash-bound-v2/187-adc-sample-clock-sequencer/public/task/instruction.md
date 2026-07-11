# ADC Sample Clock Sequencer

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: ADC timing/source sequencer.
- Target artifact: `adc_sample_clock_sequencer.va`.
- Role: periodic reset/sample/autozero/non-overlap/convert timing source.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module adc_sample_clock_sequencer(rst, s, ss, nc_az, nc, conv);
```

`rst`, `s`, `ss`, `nc_az`, `nc`, and `conv` are generated voltage-coded timing outputs. All ports are electrical outputs.

## Public Parameter Contract

No overrideable public parameters are required. Generate 0/0.9 V pulses with 20 ps transition edges on an 18 ns periodic frame.

## Required Behavior

Generate a repeating 18 ns ADC timing frame with these high windows: `rst` from 0 to 0.25 ns; `s` from 0.6 to 1.0 ns, 6.6 to 7.0 ns, and 12.6 to 13.0 ns; `ss` from 0.6 to 1.2 ns, 6.6 to 7.2 ns, and 12.6 to 13.2 ns; `nc_az` from 1.35 to 1.55 ns, 7.35 to 7.55 ns, and 13.35 to 13.55 ns; `nc` from 1.7 to 2.05 ns, 7.7 to 8.05 ns, and 13.7 to 14.05 ns; and `conv` from 2.4 to 5.4 ns, 8.4 to 11.4 ns, and 14.4 to 17.4 ns. All outputs should return low between their public windows and repeat every 18 ns.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `adc_sample_clock_sequencer.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
