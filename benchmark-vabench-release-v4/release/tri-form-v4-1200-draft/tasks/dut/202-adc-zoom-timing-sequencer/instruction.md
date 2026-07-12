# ADC Zoom Timing Sequencer

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: ADC timing/source sequencer.
- Target artifact: `adc_zoom_timing_sequencer.va`.
- Role: compact ADC timing source with SAR and zoom phases.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module adc_zoom_timing_sequencer(rst, s, sar, res, intg, clk_sar, zoom, clk_zoom, rst_zoom);
```

`rst`, `s`, `sar`, `res`, `intg`, `clk_sar`, `zoom`, `clk_zoom`, and `rst_zoom` are generated voltage-coded timing outputs. All ports are electrical outputs.

## Public Parameter Contract

No overrideable public parameters are required. Generate 0/1.1 V pulses with 20 ps transition edges on a 32 ns periodic frame.

## Required Behavior

Generate a repeating 32 ns compact ADC timing frame with these high windows: `rst` from 0.5 to 0.8 ns; `s` from 1.5 to 2.5 ns; `sar` from 3.0 to 5.4 ns; `clk_sar` from 3.0 to 3.25 ns, 3.6 to 3.85 ns, and 4.2 to 4.45 ns; `res` from 6.0 to 6.6 ns; `intg` from 8.0 to 8.7 ns; `zoom` from 9.2 to 10.8 ns; `clk_zoom` from 9.2 to 9.45 ns and 9.8 to 10.05 ns; and `rst_zoom` from 11.0 to 11.5 ns. All outputs should return low between their public windows and repeat every 32 ns.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `adc_zoom_timing_sequencer.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
