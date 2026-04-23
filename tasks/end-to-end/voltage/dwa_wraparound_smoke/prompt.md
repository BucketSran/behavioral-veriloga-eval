Write a Verilog-A module named `dwa_wraparound_ref`.

# Task: dwa_wraparound_smoke

Write a pure voltage-domain Verilog-A DWA pointer generator that rotates a
16-cell thermometer selection window by the input 4-bit code on every rising
clock edge.

The smoke test must stress pointer wraparound. Starting from pointer index 13,
the first non-reset update must wrap through cell 15 back to cell 0, and later
updates must include at least one more wraparound. The pointer output must be
one-hot after reset, and the active cell count must match the requested code on
each sampled cycle.

Constraints:

- Use only voltage-domain `electrical` ports.
- .., +1))` for clocked updates.
- 
- Do not use current contributions, `ddt()`, or `idt()`.

Return a DUT and minimal Spectre-compatible testbench that EVAS can run.

Ports:
- `clk_i`: input electrical
- `rst_ni`: input electrical
- `code_i[3:0]`: input electrical
- `cell_en_o[15:0]`: output electrical
- `ptr_o[15:0]`: output electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `input  electrical [3:0]  code_i`: electrical (electrical)
- `output electrical [15:0] cell_en_o`: electrical (electrical)
- `output electrical [15:0] ptr_o`: unknown (electrical)
