Write a Verilog-A module named `dwa_ptr_gen`.

Create a voltage-domain Data Weighted Averaging (DWA) pointer rotation generator
in Verilog-A, then produce a minimal EVAS-compatible Spectre testbench and run a
smoke simulation.

Behavioral intent:

- inputs: `clk_i`, `rst_ni` (active-low), and a 4-bit input code bus `code_msb_i[3:0]`
- outputs: 16-bit cell-enable mask `cell_en_o[15:0]` and 16-bit one-hot pointer `ptr_o[15:0]`
- on each rising edge of `clk_i`, read the 4-bit MSB code (0..15) and rotate
  the circular pointer by that many positions
- `ptr_o` must be one-hot (exactly one bit asserted) after reset
- `cell_en_o` marks the activated cells spanning from the previous pointer to
  the current pointer (inclusive)

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock edge detection
- use `transition(...)` to drive all output bits
- `clk_i`, `rst_ni`, and representative `ptr_o` bits must appear in the waveform CSV
- parameter `ptr_init` sets the reset pointer position (default 0)

Minimum simulation goal:

- 100 MHz clock, reset deasserts at 5 ns, drive at least 16 input codes over 175 ns
- after reset, `ptr_o` must be one-hot on every sampled clock edge (≥ 95% of samples)
- `cell_en_o` must have at least one bit asserted after reset
- pointer must advance correctly: new_ptr = (old_ptr + cell_count) % 16

Expected behavior:
- Pointer should advance in data-weighted averaging pattern
- No overlap between consecutive pointer values
Ports:
- `clk_i`: input electrical
- `rst_ni`: input electrical
- `code_msb_i[3:0]`: input electrical
- `cell_en_o[15:0]`: output electrical
- `ptr_o[15:0]`: output electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `[3:0]  code_msb_i`: electrical
- `[15:0] cell_en_o`: electrical
- `[15:0] ptr_o`: electrical- `input  electrical [3:0]  code_msb_i`: electrical (electrical)
- `output electrical [15:0] cell_en_o`: electrical (electrical)
- `output electrical [15:0] ptr_o`: unknown (electrical)
