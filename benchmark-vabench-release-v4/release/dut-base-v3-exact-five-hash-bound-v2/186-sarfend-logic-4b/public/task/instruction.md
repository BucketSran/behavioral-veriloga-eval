# SAR Front-End Logic 4b

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: SAR ADC control logic.
- Target artifact: `sarfend_logic_4b.va`.
- Role: 4-bit SAR front-end handshake, test override, and DAC-control publisher.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module sarfend_logic_4b(clks, dcomp, dcompb, test, dtest0, dtest1, dtest2, dtest3, clkc, dp1, dp2, dp3, dp4, dm1, dm2, dm3, dm4, dout0, dout1, dout2, dout3);
```

`clks` is the sample/reset clock, `dcomp/dcompb` are comparator outputs, `test` enables test override bits `dtest0..dtest3`, `clkc` requests comparator activity, `dp1..dp4`/`dm1..dm4` are differential DAC controls, and `dout0..dout3` publish the previous conversion word. All ports are electrical.

## Public Parameter Contract

No overrideable public parameters are required. Use 0.45 V thresholds and 0/1 V voltage-coded controls.

## Required Behavior

On each rising `clks` crossing, publish the previous cycle DAC-P word on `dout0..dout3`, reset the conversion pointer, initialize the DAC controls for a new conversion, capture the test override word, and clear `clkc`. On falling `clks`, assert `clkc` to start comparison. While `clks` is low, comparator output reset/recovery should reassert `clkc`; comparator decision activity should capture one MSB-to-LSB decision per step. With `test` low, use the live comparator decision; with `test` high, use the captured test bit for that step. Drive complementary `dp`/`dm` controls and stop requesting comparisons after four decisions.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sarfend_logic_4b.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
