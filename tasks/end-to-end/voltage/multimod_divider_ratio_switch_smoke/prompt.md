Write a pure voltage-domain Verilog-A dual-modulus divider.

Requirements:

1. Ports: `clk_in`, `ratio_ctrl`, `div_out`
2. `ratio_ctrl < 4.5V` means divide-by-4, otherwise divide-by-5
3. The target ratio is re-sampled on every input clock edge
4. Output should emit one pulse per completed divide interval
5. Use only EVAS-compatible voltage-domain constructs
