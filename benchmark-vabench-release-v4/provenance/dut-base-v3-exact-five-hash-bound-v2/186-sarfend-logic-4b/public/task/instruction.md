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

On each rising `clks` crossing, publish the previous cycle DAC-P word,
reset the conversion pointer, initialize the DAC controls for a new conversion,
capture the test override word, and clear `clkc`.

- Publish the previous P-side state as `dout3=dp4`, `dout2=dp3`,
  `dout1=dp2`, and `dout0=dp1` before reinitializing the DAC controls.
- Initialize the new conversion to `dp4=dm4=0` and to
  `dp3=dm3=dp2=dm2=dp1=dm1=1`. These equal-valued pairs are intentional
  undecided/trial states; only an accepted decision makes that pair
  complementary.
- On falling `clks`, assert `clkc` to start comparison. While `clks` is low,
  comparator reset/recovery with both comparator outputs low reasserts `clkc`.
- Accept decisions in the order `dp4/dm4`, `dp3/dm3`, `dp2/dm2`, then
  `dp1/dm1`. A `dcomp`-high/`dcompb`-low decision produces P/M=`1/0`;
  `dcomp`-low/`dcompb`-high produces P/M=`0/1`.
- With `test` low, use the live comparator decision. With `test` high, use
  captured `dtest3`, `dtest2`, `dtest1`, then `dtest0` for the four decisions.
- Clear `clkc` when a decision is accepted and stop requesting comparisons
  after four decisions.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not force every P/M pair to be complementary during the documented undecided/trial initialization state. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sarfend_logic_4b.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
