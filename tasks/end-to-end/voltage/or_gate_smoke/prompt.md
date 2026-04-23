Write a Verilog-A module named `or_gate`.

# Task: or_gate_smoke

## Objective

Create an OR gate behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `or_gate`
- **Ports** (all `electrical`, exactly as named): `a`, `b`, `y`
- **Parameters**: `vdd` (real, default 1.8), `tedge` (real, default 10p)
- **Behavior**:
  - `y` is HIGH when either `a` OR `b` is HIGH (above vdd/2)
  - `y` is LOW only when both inputs are LOW
  - Output HIGH = vdd, LOW = 0
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `or_gate.va` via `ahdl_include`
- Tests all 4 input combinations: (0,0), (0,1), (1,0), (1,1)
- Each combination for 2ns, total 8ns run
- Saves signals: `a`, `b`, `y`

## Deliverable

Two files:
1. `or_gate.va` - the Verilog-A behavioral model
2. `tb_or_gate.scs` - the Spectre testbench

Ports:
- `A`: input electrical
- `B`: input electrical
- `Y`: output electrical
