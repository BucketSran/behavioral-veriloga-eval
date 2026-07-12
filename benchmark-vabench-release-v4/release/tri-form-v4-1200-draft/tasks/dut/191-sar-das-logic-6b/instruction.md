# 6-bit SAR DAS Logic

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: SAR ADC differential control logic.
- Target artifact: `sar_das_logic_6b.va`.
- Role: 6-bit SAR differential analog-switch control sequencer.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module sar_das_logic_6b(clk_sampling, clk_sar, vcomp, d1, d2, d3, d4, d5, d6, db1, db2, db3, db4, db5, db6, co, cob);
```

`clk_sampling` frames conversion reset/preset, `clk_sar` advances decisions, `vcomp` is the comparator decision input, `d1..d6`/`db1..db6` are differential bit controls, and `co/cob` are one-cycle decision pulses. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `tde = 50p`, `tdc = 50p`, `vdd = 1.1`, and `vcm = 0.55`. Use `vcm` as the threshold for clock and comparator decisions.

## Required Behavior

On a rising `clk_sampling` transition through `vcm`, clear all bit controls and decision pulses and reset the decision index to the start of a conversion. On a falling `clk_sampling` transition through `vcm`, preset all `d1..d6` and `db1..db6` controls high while keeping `co/cob` low. The first subsequent `clk_sar` rising decision uses decision index 7, then the index decrements after each `clk_sar` rising decision.

On each rising `clk_sar` transition through `vcm`, compare `vcomp` against `vcm`. If `vcomp > vcm`, drive `co` high and `cob` low; if the decision index is 7, set or keep `d6` high, and for later indices 6, 5, 4, 3, and 2 clear `db5`, `db4`, `db3`, `db2`, and `db1` respectively. If `vcomp <= vcm`, drive `cob` high and `co` low; if the decision index is 7, set or keep `db6` high, and for later indices 6, 5, 4, 3, and 2 clear `d5`, `d4`, `d3`, `d2`, and `d1` respectively. Bit controls not listed for the current decision retain their previous states. On each falling `clk_sar` transition through `vcm`, clear `co/cob` back low.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sar_das_logic_6b.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
