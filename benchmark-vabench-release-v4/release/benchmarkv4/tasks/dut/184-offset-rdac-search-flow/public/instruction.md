# Offset RDAC Search Flow

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: calibration/trim control flow.
- Target artifact: `offset_rdac_search_flow.va`.
- Role: combined RDAC refinement and comparator-offset search flow.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module offset_rdac_search_flow(ck, d, vinp, vinn, vrefp, vrefn, dc0, dc1, dc2, dc3, dc4, dc5, dc6);
```

`ck` is the flow clock, `d` is the comparator decision, `vinp/vinn` are generated differential input stimulus outputs, `vrefp/vrefn` are generated reference stimulus outputs, and `dc0..dc6` expose the RDAC code. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Use 0/1 V logic, a 0.5 V decision threshold, a 0.6 V output common mode, 17 reference levels over a 1.0 V differential span, and a 40 mV initial offset-search step. The reference-grid LSB is `1.0 / 16.0`, and the initial signed differential reference and input values are both `-17.0 / 2.0` LSBs.

## Required Behavior

Implement a deterministic two-phase foreground flow on rising crossings of `ck` through 0.5 V. Treat `d < 0.5 V` as the low comparator direction and `d >= 0.5 V` as the high comparator direction. Represent the generated input and reference as signed differential values `vin` and `vref`; drive `vinp/vinn` and `vrefp/vrefn` as half-differential outputs around the 0.6 V common mode: `p = 0.6 + 0.5 * value` and `n = 0.6 - 0.5 * value`.

Initialize `vref` and `vin` to the initial reference-grid value above. Initialize the RDAC code to `1000000` with `dc6` as the MSB, `dc0` as the LSB, high bits driven to 1 V, and low bits driven to 0 V.

The RDAC refinement phase contains six decision clocks. On those clocks, resolve the current trial bit and assert the next lower trial bit in this order: `(dc6, dc5)`, `(dc5, dc4)`, `(dc4, dc3)`, `(dc3, dc2)`, `(dc2, dc1)`, `(dc1, dc0)`. For each pair, keep the current bit high when `d < 0.5 V`; clear the current bit when `d >= 0.5 V`; in both cases set the next lower bit high. The clock immediately after the sixth RDAC decision is a phase handoff and does not perform another bit decision.

The offset-search phase then contains eight search-update clocks. Start each search window with a 40 mV step, compare each sampled comparator direction with the immediately previous sampled direction from the foreground flow, halve the current step before moving when the direction changes, then move `vin` by `+step` for `d < 0.5 V` or `-step` for `d >= 0.5 V`. After the eighth search-update clock, advance `vref` by one reference-grid LSB, reset `vin` to the new `vref`, reset the RDAC code to `1000000`, and keep the outputs recentered on that new reference. The next rising clock is a restart boundary; the following rising clock begins the next six-clock RDAC refinement sequence.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `offset_rdac_search_flow.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
