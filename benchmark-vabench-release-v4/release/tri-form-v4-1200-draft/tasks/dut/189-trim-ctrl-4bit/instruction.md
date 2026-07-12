# Trim Ctrl 4bit

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: calibration/trim decoder.
- Target artifact: `trim_ctrl_4bit.va`.
- Role: analog code to four-bit trim-control decoder.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module trim_ctrl_4bit(ain, dout0, dout1, dout2, dout3);
```

`ain` is an analog code-level input. `dout0..dout3` are voltage-coded trim bits ordered from LSB to MSB. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Drive active bits near 0.9 V and inactive bits near 0 V with smooth transitions.

## Required Behavior

Round `ain` to the nearest integer code level and emit the low four bits on `dout0..dout3`. Update deterministically as `ain` changes and keep the output voltage-coded rather than current-domain.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `trim_ctrl_4bit.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
