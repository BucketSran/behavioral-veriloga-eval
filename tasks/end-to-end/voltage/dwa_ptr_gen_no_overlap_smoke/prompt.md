Write a Verilog-A module named `dwa_ptr_gen_no_overlap`.

# Task: dwa_ptr_gen_no_overlap_smoke

## Objective

Create a DWA (Data Weighted Averaging) pointer generator behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench. The module ensures consecutive activation windows do not overlap.

## Specification

- **Module name**: `dwa_ptr_gen_no_overlap`
- **Ports** (all `electrical`, exactly as named):
  - Inputs: `clk`, `rst_n`, `code_3`, `code_2`, `code_1`, `code_0`
  - Outputs: `cell_en_15`..`cell_en_0`, `ptr_15`..`ptr_0`
- **Parameters**: `vdd`, `vth`, `ptr_init`
- **Behavior**:
  - Sample 4-bit input code on rising clock edge.
  - Maintain a rotating pointer across 16 cells.
  - Produce `cell_en_*` outputs that activate cells according to the sampled code.
  - Consecutive cycles must not reuse the same enabled cell set.
  - `rst_n` is active-low reset.
  - Output HIGH = V(vdd), LOW = 0 - read dynamically.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `dwa_ptr_gen_no_overlap.va` via `ahdl_include`
- Provides vdd=0.9V
- Generates 100MHz clock (period=10ns)
- Provides active-low reset (rst_n deasserted after ~5ns)
- Sweeps 4-bit code values
- Saves signals: `clk`, `rst_n`, `cell_en_*`, `ptr_*`
- Runs transient for ~175ns

## Deliverable

Two files:
1. `dwa_ptr_gen_no_overlap.va` - the Verilog-A behavioral model
2. `tb_dwa_ptr_gen_no_overlap.scs` - the Spectre testbench

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
