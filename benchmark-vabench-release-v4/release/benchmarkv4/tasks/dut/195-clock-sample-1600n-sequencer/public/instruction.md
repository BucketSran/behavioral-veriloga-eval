# Clock Sample 1600n Sequencer

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: ADC timing/source sequencer.
- Target artifact: `clock_sample_1600n_sequencer.va`.
- Role: periodic reset/sample/non-overlap/residue/convert timing source.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module clock_sample_1600n_sequencer(rst, s, nc, res, conv);
```

`rst`, `s`, `nc`, `res`, and `conv` are generated voltage-coded timing outputs. All ports are electrical outputs.

## Public Parameter Contract

No overrideable public parameters are required. Generate 0/1.1 V pulses with 20 ps transition edges on a 16 ns periodic frame.

## Required Behavior

Generate a repeating 16 ns ADC timing frame with these high windows: `rst` from 0 to 0.2 ns; `s` from 1.0 to 1.8 ns and 9.0 to 9.8 ns; `nc` from 2.0 to 2.25 ns and 10.0 to 10.25 ns; `res` from 3.0 to 3.25 ns, 4.5 to 4.75 ns, 6.0 to 6.25 ns, and 7.5 to 7.75 ns; and `conv` from 3.0 to 7.0 ns and 11.0 to 15.0 ns. All outputs should return low between their public windows and repeat every 16 ns.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `clock_sample_1600n_sequencer.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
