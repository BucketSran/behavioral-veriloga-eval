Write a pure voltage-domain Verilog-A dual-modulus divider.

Module name: `multimod_divider_ratio_switch_ref`.

Requirements:

1. Ports: `clk_in`, `ratio_ctrl`, `div_out`
2. `ratio_ctrl < 4.5V` means divide-by-4, otherwise divide-by-5
3. The target ratio is re-sampled on every input clock edge
4. Output should emit one pulse per completed divide interval
5. Use only EVAS-compatible voltage-domain constructs

Expected behavior:
- When ratio_ctrl changes, output frequency should change accordingly
- New ratio should be applied within few cycles
Ports:
- `clk_in`: input electrical
- `ratio_ctrl`: input electrical
- `div_out`: output electrical
