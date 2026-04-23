Write a Verilog-A module named `not_gate`.

# Task: not_gate_smoke

## Objective

Create a NOT gate (inverter) behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `not_gate`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `a`, `y`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - `y` is HIGH when `a` is LOW (below threshold)
  - `y` is LOW when `a` is HIGH (above threshold)
  - Threshold at `vth` for input level detection
  - Output level: HIGH = V(vdd), LOW = V(vss)
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `not_gate.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Generates input 'a' as 50MHz square wave (period=20ns)
- Saves signals: `a`, `y`
- Runs transient for 200ns

## Deliverable

Two files:
1. `not_gate.va` - the Verilog-A behavioral model
2. `tb_not_gate.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `A`: input electrical
- `Y`: output electrical
