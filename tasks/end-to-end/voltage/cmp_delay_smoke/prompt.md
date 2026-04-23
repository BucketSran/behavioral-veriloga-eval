Write a Verilog-A module named `cmp_delay`.

# Task: cmp_delay_smoke

## Objective

Create a clocked comparator behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench, then run a smoke simulation.

## Specification

- **Module name**: `cmp_delay`
- **Ports** (all `electrical`, exactly as named): `clk`, `vinn`, `vinp`, `out_n`, `out_p`, `lp`, `lm`, `vss`, `vdd`
- **Behavior**:
  - Detect the rising edge of `clk`.
  - Compare `vinp` and `vinn`.
  - Drive `out_p`/`out_n` to rail-referenced logic outputs using `transition()`.
  - The positive-output decision must still resolve HIGH in all four positive-polarity phases.
  - The effective decision delay should grow monotonically as `|vinp - vinn|` shrinks from `10 mV` to `0.01 mV`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `cmp_delay.va` via `ahdl_include`
- Provides VDD=0.9V, VSS=0V
- Generates a 1GHz clock with 50% duty cycle
- Creates differential input with 4 phases spanning 3 decades of |vinp-vinn|:
  - Phase 1 (0-4ns): diff=+10mV (vinp > vinn)
  - Phase 2 (4-8ns): diff=+1mV
  - Phase 3 (8-12ns): diff=+0.1mV
  - Phase 4 (12-16ns): diff=+0.01mV
- Saves signals: `clk`, `vinp`, `vinn`, `out_p`, `out_n`
- Runs transient for 16ns

## Deliverable

Two files:
1. `cmp_delay.va` - the Verilog-A behavioral model
2. `tb_cmp_delay.scs` - the Spectre testbench

Expected behavior:
- Comparator output (out_p) should go high in each phase
- clk-to-output delay should INCREASE as differential input shrinks:
  - Phase 0 (diff=10mV): shortest delay
  - Phase 1 (diff=1mV): longer delay
  - Phase 2 (diff=0.1mV): even longer delay
  - Phase 3 (diff=0.01mV): longest delay
- Delay sequence must be monotonically increasing
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
