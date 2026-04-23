Write a Verilog-A module named `xor_phase_detector`.

# Task: xor_pd_smoke

## Objective

Create an XOR Phase Detector behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `xor_phase_detector`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `ref`, `div`, `pd_out`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 50p)
- **Behavior**:
  - `pd_out` is HIGH when `ref` and `div` are at **different** logic levels (XOR logic).
  - Updates on every edge of both `ref` and `div`.
  - Average `pd_out` duty cycle is proportional to phase difference.
  - Output HIGH = V(vdd), LOW = V(vss) - read dynamically.
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `xor_phase_detector.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Generates two clocks (ref and div) with phase offset
- Saves signals: `ref`, `div`, `pd_out`
- Runs transient for ~200ns

## Deliverable

Two files:
1. `xor_phase_detector.va` - the Verilog-A behavioral model
2. `tb_xor_phase_detector.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `REF`: input electrical
- `DIV`: input electrical
- `PD_OUT`: output electrical
