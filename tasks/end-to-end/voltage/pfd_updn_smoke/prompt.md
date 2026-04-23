Write a Verilog-A module named `pfd_updn`.

# Task: pfd_updn_smoke

## Objective

Create a Phase-Frequency Detector (PFD) behavioral model with UP/DN outputs in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `pfd_updn`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `ref`, `div`, `up`, `dn`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 50p)
- **Behavior**:
  - Rising edge of `ref` sets `up` high.
  - Rising edge of `div` sets `dn` high.
  - When both `up` and `dn` are high, both are immediately reset to 0 (combinational reset).
  - Output HIGH = V(vdd), LOW = V(vss) - read dynamically.
- **Output**: use `transition()` only.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `pfd_updn.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Generates two clocks (ref and div) with phase offset
- Saves signals: `ref`, `div`, `up`, `dn`
- Runs transient for ~200ns

## Deliverable

Two files:
1. `pfd_updn.va` - the Verilog-A behavioral model
2. `tb_pfd_updn.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `REF`: input electrical
- `DIV`: input electrical
- `UP`: output electrical
- `DN`: output electrical
