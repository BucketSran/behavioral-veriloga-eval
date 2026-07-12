# Control Word Encoder 7b

## Task Contract
Implement the Verilog-A DUT `control_word_encoder_7b.va` for a parameterized voltage-coded control-word source.

## Public Verilog-A Interface
Provide `module control_word_encoder_7b(d0, d1, d2, d3, d4, d5, d6);` with electrical outputs `d0` through `d6`.

## Public Parameter Contract
Expose integer `ctrl = 85` and real parameters `vhi = 0.9`, `vlo = 0.0`, and `tr = 20p`. Testbenches may override these parameters.

## Required Behavior
Decode `ctrl` into seven output bits, LSB first: `d0` carries bit 0 and `d6` carries bit 6. Drive each output to `vhi` when its bit is 1 and `vlo` when its bit is 0.

## Modeling Constraints
Use parameter-driven voltage-coded outputs with `transition`. Do not shift the bit order, invert the bits, use half high levels, or depend on any external input.

## Output Contract
Submit only the completed Verilog-A module in `control_word_encoder_7b.va`.
