Write a Verilog-A module named `gray_counter_4b`.

# Task: gray_counter_4b_smoke

## Objective

Create a 4-bit Gray Code Counter behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `gray_counter_4b`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `clk`, `en`, `rstb`, `g3`, `g2`, `g1`, `g0`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - On each rising `clk` edge, if `en=1` and `rstb=1`, increment a 4-bit binary counter (mod 16).
  - Convert binary to Gray code: `gray = bin ^ (bin >> 1)`.
  - Drive `g3` (MSB), `g2`, `g1`, `g0` (LSB) with the Gray-coded output.
  - `rstb` low (active-low reset) resets counter to 0.
- **Output**: use `transition()` only. No `idt` or current domain.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `gray_counter_4b.va` via `ahdl_include`
- Provides vdd=1.8V, vss=0V
- Generates clock and enable signals
- Saves signals: `clk`, `rstb`, `g3`, `g2`, `g1`, `g0`
- Runs transient for ~2us (at least 16 clock cycles)

## Deliverable

Two files:
1. `gray_counter_4b.va` - the Verilog-A behavioral model
2. `tb_gray_counter_4b.scs` - the Spectre testbench

Expected behavior:
- Only ONE bit should change between consecutive states
- Gray code sequence: 0000→0001→0011→0010→0110→0111→0101→0100→1100→...
- Counter should wrap around correctly
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `CLK`: input electrical
- `EN`: input electrical
- `RSTB`: input electrical
- `G3`: output electrical
- `G2`: output electrical
- `G1`: output electrical
- `G0`: output electrical
