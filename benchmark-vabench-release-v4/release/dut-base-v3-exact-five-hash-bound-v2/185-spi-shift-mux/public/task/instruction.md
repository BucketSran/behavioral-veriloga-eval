# SPI Shift Mux

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: AMS serial configuration/control support.
- Target artifact: `spi_shift_mux.va`.
- Role: voltage-domain serial configuration shift register.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module spi_shift_mux(scki, sdi, rst, out0, out1, out2, out3, out4, out5, out6, out7, sdo, scko);
```

`scki` is the serial clock, `sdi` is serial data in, `rst` is active-high reset, `out0..out7` expose the configuration word, `sdo` is serial data out, and `scko` mirrors the clock state. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Use 0/0.9 V logic with a 0.45 V threshold.

## Required Behavior

Initialize and reset the 8-bit configuration word to `10110010`, with the leftmost bit exposed on `out7` and `sdo` and the rightmost bit on `out0`. While `rst` is high, reload that word and block serial shifting. On each `scki` threshold crossing while reset is inactive, shift the word toward `out7`; sampled `sdi` enters `out0`. Drive `sdo` from the current `out7` bit and drive `scko` from the current `scki` logic state.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `spi_shift_mux.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
