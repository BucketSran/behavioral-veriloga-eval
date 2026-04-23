Write a Verilog-A module named `sample_hold`.

# Task: sample_hold_smoke

## Objective

Create a Sample-and-Hold (S&H) circuit behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `sample_hold`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `in`, `clk`, `out`
- **Parameters**:
  - `vth` (real, default 0.45): logic threshold in volts
  - `tedge` (real, default 100p): output transition time in seconds
- **Behavior**:
  - On the **rising edge** of `clk` (when `V(clk)` crosses `vth` upward), sample `V(in)` and hold it.
  - `V(out)` reflects the held value via `transition()`.
  - Between clock edges, `V(out)` remains constant.
- **Output**: use `transition()` — do NOT use `idt()`, `ddt()`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `sample_hold.va` via `ahdl_include`
- Provides vdd=1.8V, vss=0V
- Generates clock and varying input signal
- Saves signals: `in`, `clk`, `out`
- Runs transient for ~1us

## Deliverable

Two files:
1. `sample_hold.va` - the Verilog-A behavioral model
2. `tb_sample_hold.scs` - the Spectre testbench

Expected behavior:
- When sample=high: output tracks input
- When sample=low: output holds last sampled value
- Transition between sample/hold should be clean
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `IN`: input electrical
- `CLK`: input electrical
- `OUT`: output electrical
