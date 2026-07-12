# SAR Comparator Reset High

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: comparator primitive.
- Target artifact: `sar_comparator_reset_high.va`.
- Role: clocked differential SAR comparator with precharged-high outputs.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module sar_comparator_reset_high(cmpck, vinn, vinp, dcmpn, dcmpp);
```

`cmpck` is the comparator clock, `vinp/vinn` are differential analog inputs, and `dcmpp/dcmpn` are voltage-coded decision outputs. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vdd = 0.9` and `td_cmp = 20p`. Use `vdd/2` as the clock threshold and 0/`vdd` as output levels.

## Required Behavior

Initialize both decision outputs high. Whenever `cmpck` falls through `vdd/2`, reset both outputs high. Whenever `cmpck` rises through `vdd/2`, latch a differential decision: `dcmpp` high for `vinp > vinn`, `dcmpn` high for `vinp < vinn`, and both outputs low for equal inputs. Hold the latched or reset state until the next clock event.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sar_comparator_reset_high.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
