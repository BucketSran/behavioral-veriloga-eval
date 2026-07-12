# DAC Serial Accumulator

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter control/accumulation primitive.
- Target artifact: `dac_serial_accumulator.va`.
- Role: serial-bit weighted DAC accumulator.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module dac_serial_accumulator(clk_sample, clk_sarready, data, out);
```

All ports are electrical. `clk_sample` resets a conversion, `clk_sarready` advances serial bit accumulation, `data` is the serial decision bit, and `out` is the centered analog output.

## Public Parameter Contract

Provide overrideable parameters `vdd = 1.1`, `vcm = 0.55`, and integer `bit_count = 4`. Use `vcm` as the digital decision threshold.

## Required Behavior

On each falling `clk_sample` crossing, reset the accumulator and bit counter. On each falling `clk_sarready` crossing during the active bit window, add a binary-weighted contribution when `data` is high, with the first accepted bit carrying the largest weight and later bits halving successively. Drive `out` as the accumulated normalized value mapped to a bipolar span from `-vdd` to `+vdd`. Hold the output between update events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `dac_serial_accumulator.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
