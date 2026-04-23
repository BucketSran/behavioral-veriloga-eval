Write a Verilog-A module named `cmp_strongarm`.

# Task: cmp_strongarm_smoke

## Objective

Create a clocked StrongARM-style comparator behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `cmp_strongarm`
- **Ports** (all `electrical`, exactly as named): `clk`, `vinn`, `vinp`, `out_n`, `out_p`, `lp`, `lm`, `vss`, `vdd`
- **Behavior**:
  - Detect the rising edge of `clk`.
  - When `vinp > vinn`, drive `out_p` HIGH and `out_n` LOW.
  - When `vinp < vinn`, drive `out_p` LOW and `out_n` HIGH.
  - Outputs should show finite transitions and toggling when input polarity changes.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `cmp_strongarm.va` via `ahdl_include`
- Provides VDD=0.9V, VSS=0V
- Generates a clock with ~500MHz frequency
- Creates differential input that changes polarity (vinp > vinn then vinp < vinn)
- Saves signals: `clk`, `vinp`, `vinn`, `out_p`, `out_n`
- Runs transient for ~4ns

## Deliverable

Two files:
1. `cmp_strongarm.va` - the Verilog-A behavioral model
2. `tb_cmp_strongarm.scs` - the Spectre testbench

Expected behavior:
- Output should toggle on each clock edge when input difference is sufficient
- Output should be valid after clock edge with some delay
Ports:
- `CLK`: input electrical
- `VINN`: input electrical
- `VINP`: input electrical
- `DCMPN`: output electrical
- `DCMPP`: output electrical
- `LP`: output electrical
- `LM`: output electrical
- `VSS`: inout electrical
- `VDD`: inout electrical
