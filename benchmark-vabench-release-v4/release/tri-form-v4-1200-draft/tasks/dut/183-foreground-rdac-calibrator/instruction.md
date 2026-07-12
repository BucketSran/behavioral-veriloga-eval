# Foreground RDAC Calibrator

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: calibration/trim control.
- Target artifact: `foreground_rdac_calibrator.va`.
- Role: foreground 7-bit RDAC calibration controller.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module foreground_rdac_calibrator(ck, d, vrefp, vrefn, dc0, dc1, dc2, dc3, dc4, dc5, dc6, cvinp, cvinn, en, enb);
```

`ck` is the calibration clock, `d` is the comparator decision, `vrefp/vrefn` are forwarded references, `dc0..dc6` are RDAC code bits, and `en/enb` indicate calibration activity. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `vdd = 1.0`. Use `0.5*vdd` as the clock and decision threshold and 0/`vdd` as digital output levels.

## Required Behavior

Initialize calibration active with the MSB trial code set (`dc6 = vdd`, all lower RDAC bits low). On each rising `ck` crossing while calibration is active, sample `d` against the `0.5*vdd` threshold and refine the 7-bit RDAC code from MSB toward LSB. For the current trial bit, keep that bit when `d < 0.5*vdd`; clear that bit when `d >= 0.5*vdd`. In both cases, assert the next lower trial bit as the search advances. After the seven-bit capture phase completes, deassert `en` and assert `enb`. Continuously drive `cvinp` from `vrefp` and `cvinn` from `vrefn`.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `foreground_rdac_calibrator.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
