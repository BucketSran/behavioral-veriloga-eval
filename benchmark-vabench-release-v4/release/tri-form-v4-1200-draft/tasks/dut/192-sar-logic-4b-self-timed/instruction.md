# 4-bit Self-Timed SAR Logic

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: SAR ADC self-timed control logic.
- Target artifact: `sar_logic_4b_self_timed.va`.
- Role: four-decision self-timed SAR controller.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module sar_logic_4b_self_timed(vdd, gnd, clkc, rst, dcmpp, dcmpn, cmpck, dout1, dout2, dout3, dout4, dbotp1, dbotp2, dbotp3, dbotn1, dbotn2, dbotn3);
```

`vdd/gnd` provide logic rails, `clkc` starts comparator activity, `rst` resets the conversion, `dcmpp/dcmpn` are comparator outputs, `cmpck` is the comparator clock request, `dout1..dout4` are code bits, and `dbotp1..dbotp3`/`dbotn1..dbotn3` are bottom-plate controls. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `t_logic_delay = 100p`. Derive logic high, low, and threshold from the `vdd` and `gnd` pins.

## Required Behavior

At initialization and on each rising `rst` transition, reset the conversion to step 4, clear `cmpck` and `dout1..dout4`, and initialize `dbotp1..dbotp3` and `dbotn1..dbotn3` high. A rising `clkc` transition schedules `cmpck` high after `t_logic_delay`.

Each rising comparator pulse on `dcmpp` or `dcmpn` schedules `cmpck` low after `t_logic_delay`. At the pulse, treat `dcmpp > dcmpn` as a positive decision and store that decision in `dout{step}` for the current MSB-to-LSB step sequence 4, 3, 2, 1. For steps above 1, a positive decision clears the positive bottom-plate control `dbotp{step-1}`, while a negative decision clears the negative bottom-plate control `dbotn{step-1}`. Step 1 only latches `dout1` and does not update a bottom-plate control. When the comparator pulse falls, decrement the step and re-enable `cmpck` after `t_logic_delay` while further decisions remain.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sar_logic_4b_self_timed.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
