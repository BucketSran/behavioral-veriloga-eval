# Clocked Comparator Dual Output

## Task Contract

Implement `clocked_comparator_dual_output.va` as a clocked differential comparator with complementary voltage-coded outputs and reset-low precharge behavior.

## Public Verilog-A Interface

Use this module signature:

```verilog
module clocked_comparator_dual_output(clk, vinn, vinp, outn, outp);
```

All ports are scalar `electrical` nodes. `clk` is the comparator clock, `vinp` and `vinn` are the differential analog inputs, and `outp`/`outn` are complementary decision outputs.

## Public Parameter Contract

- `vdd`: logic high level and clock threshold reference, default `1.0`.
- `td_cmp`: output decision delay, default `100p`.

## Required Behavior

- Initialize both decision outputs low.
- Whenever `clk` falls through `vdd/2`, reset both outputs low.
- Whenever `clk` rises through `vdd/2`, latch a differential decision.
- Drive `outp` high and `outn` low for `vinp > vinn`.
- Drive `outn` high and `outp` low for `vinp < vinn`.
- Drive both outputs low for an equal-input decision.
- Hold the latched or reset state until the next clock event.

## Modeling Constraints

Use voltage contributions only. Do not modify or emit a support testbench, add checker logic, hard-code waveform sample points, add simulator side channels, use current contributions, `ddt()`, or `idt()`.

## Output Contract

Return exactly one source artifact named `clocked_comparator_dual_output.va`.
