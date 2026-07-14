# Weighted Decoder 7b5

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter weighted decoder.
- Target artifact: `weighted_decoder_7b5.va`.
- Role: redundant SAR decoder with 7-bit, 7.5-bit, and 8-bit outputs.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module weighted_decoder_7b5(d0, d1, d2, d3, d4, d5, d6, d7, d8, aout7b, aout7b5, aout8b);
```

`d0..d8` are voltage-coded input bits. `aout7b`, `aout7b5`, and `aout8b` are analog decoded outputs. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vth = 0.5`. Interpret high input bits as `+1` and low input bits as `-1` for signed weighted decoding. The shared upper ladder for `d1..d8` uses weights `1, 2, 4, 8, 8, 16, 32, 64`; the repeated 8-unit element is intentional. `d0` is the half-weight sub-bit used by the 7.5-bit and 8-bit paths.

## Required Behavior

Produce three related decoded analog outputs using a shared normalization denominator of `272.0`, corresponding to twice the public redundant SAR array basis including the fixed reference basis rather than only the switchable weights. Let `b0..b8` be the signed input decisions, where a high input is `+1` and a low input is `-1`. `aout7b` decodes the shared ladder from `d1..d8` as `(b1 + 2*b2 + 4*b3 + 8*b4 + 8*b5 + 16*b6 + 32*b7 + 64*b8) / 272.0`. `aout8b` adds the half-weight `d0` contribution as `(0.5*b0 + b1 + 2*b2 + 4*b3 + 8*b4 + 8*b5 + 16*b6 + 32*b7 + 64*b8) / 272.0`. For `aout7b5`, use `d0` and `d1` as a three-level subrange pair: both high selects `+1`, both low selects `-1`, and mixed decisions select `0`; then decode `(sublevel + 2*b2 + 4*b3 + 8*b4 + 8*b5 + 16*b6 + 32*b7 + 64*b8) / 272.0`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `weighted_decoder_7b5.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
