Write a Verilog-A module named `pfd_updn`.

# Task: pfd_deadzone_smoke

## Objective

Create a phase-frequency detector behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench. The UP/DN outputs must remain well-behaved even with very small phase offsets.

## Specification

- **Module name**: `pfd_updn`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `ref`, `div`, `up`, `dn`
- **Parameters**:
  - `vth` (real, default `0.45`)
  - `tedge` (real, default `20p`)
- **Behavior**:
  - Rising edge of `ref` sets `up` high.
  - Rising edge of `div` sets `dn` high.
  - When both states are high, reset both to 0.
  - For small phase offsets, pulses should remain short (no sustained UP/DN overlap).
  - Output HIGH = V(vdd), LOW = V(vss) - read dynamically.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `pfd_updn.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Generates ref and div clocks with small phase offsets (~ps level)
- Saves signals: `ref`, `div`, `up`, `dn`
- Runs transient to show deadzone behavior

## Deliverable

Two files:
1. `pfd_updn.va` - the Verilog-A behavioral model
2. `tb_pfd_updn.scs` - the Spectre testbench

Expected behavior:
- PFD should generate pulses even for small phase differences
- No deadzone where small phase error produces no output
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `REF`: input electrical
- `DIV`: input electrical
- `UP`: output electrical
- `DN`: output electrical
