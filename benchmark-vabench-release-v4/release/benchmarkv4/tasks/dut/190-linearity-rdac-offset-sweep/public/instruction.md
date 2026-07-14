# Linearity RDAC Offset Sweep

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: calibration/linearity measurement flow.
- Target artifact: `linearity_rdac_offset_sweep.va`.
- Role: RDAC-code sweep with repeated comparator-directed offset search.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module linearity_rdac_offset_sweep(ck, d, vinp, vinn, vrefp, vrefn, dc0, dc1, dc2, dc3, dc4, dc5, dc6);
```

`ck` is the sweep/search clock, `d` is the comparator decision, `vinp/vinn` are generated differential input stimulus outputs, `vrefp/vrefn` are generated reference stimulus outputs, and `dc0..dc6` expose the RDAC sweep code. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vcm = 0.6`, `vppd = 1.0`, `vdd = 1.0`, `nlvl = 17.0`, and integer `iter_num = 4`. The reference-grid LSB is `vppd / (nlvl - 1.0)`, and the initial signed differential reference is `(1.0 - nlvl / 2.0) * LSB`.

## Required Behavior

Implement the sweep on rising crossings of `ck` through `0.5 * vdd`. Treat `d < 0.5 * vdd` as the low comparator direction and `d >= 0.5 * vdd` as the high comparator direction. Represent the generated input and reference as signed differential values `vin` and `vref`; drive `vinp/vinn` and `vrefp/vrefn` as half-differential outputs around `vcm`: `p = vcm + 0.5 * value` and `n = vcm - 0.5 * value`.

Initialize `vref` to the initial reference-grid value above, initialize `vin = vref`, initialize the search step to 40 mV, and initialize the stored comparator direction to the low direction. Initialize the 7-bit sweep code to full scale `127`, with `dc0` as the LSB, `dc6` as the MSB, high bits driven to `vdd`, and low bits driven to 0 V.

For each RDAC code, run exactly `iter_num` search-update clocks. On each search-update clock, sample `d`, halve the current step before moving when the sampled direction differs from the stored direction, then move `vin` by `+step` for the low direction or `-step` for the high direction. Update the stored direction to the sampled direction after the move.

The rising clock after those `iter_num` search updates is a code-update and recenter clock, not another search update. On that clock, decrement the 7-bit sweep code by one when it is nonzero; when the code is zero, wrap it back to `127` and advance `vref` by one reference-grid LSB. Update `dc0..dc6` from the new code, reset `vin = vref`, reset the search step to 40 mV, and begin the next code's `iter_num` search-update clocks on the following rising clock. The stored comparator direction carries across the code-update clock.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `linearity_rdac_offset_sweep.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
