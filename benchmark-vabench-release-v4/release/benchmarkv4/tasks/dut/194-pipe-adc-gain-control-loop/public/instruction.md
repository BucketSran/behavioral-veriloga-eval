# Pipe ADC Gain Control Loop

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: pipeline ADC calibration/control flow.
- Target artifact: `pipe_adc_gain_control_loop.va`.
- Role: backend-code driven gain-control adaptation loop.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module pipe_adc_gain_control_loop(din20, din21, din22, din23, din24, din25, din26, clks, dout10, dout11, dout12, dout13, gainctrl0, gainctrl1, gainctrl2, gainctrl3, gainctrl4, gainctrl5, gainctrl6, ddiff, dop, dom, gctrlcode);
```

`din20..din26` are backend ADC bits, `clks` is the sampling clock, `dout10..dout13` are alternating test-DAC controls, `gainctrl0..gainctrl6` expose the gain-control code, and `ddiff`, `dop`, `dom`, and `gctrlcode` are scalar monitor outputs. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vlo = 0.0`, `vhi = 0.9`, `vth = 0.45`, and integer `gaincodeinit = 90`.

## Required Behavior

Initialize the gain-control code to `gaincodeinit`. Initialize the test-DAC controls to the minus phase with `dout13..dout10 = 1000`, initialize the phase so the first sampled backend code is stored as the minus-phase code, and initialize the scalar monitor codes to `dop = 96`, `dom = 32`, and `ddiff = 0` before scaling.

On each rising `clks` crossing, read `din20..din26` as a 7-bit unsigned code. Alternate between minus and plus test-DAC phases: after a minus-phase sample, drive the next plus phase with `dout13..dout10 = 0111`; after a plus-phase sample, return to the minus phase with `dout13..dout10 = 1000`. Store the minus-phase and plus-phase ADC codes, compute the plus-minus code difference, and compare it against a target difference of 64 codes. If the difference is too large, reduce the gain-control code by the absolute error; if too small, increase it by the absolute error. Clamp the gain-control code to `0..127`, emit its bits, and expose the scalar monitor values scaled by `1/100`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `pipe_adc_gain_control_loop.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
