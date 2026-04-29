Write a Verilog-A module named `mux_4to1`.

# Task: mux_4to1_smoke

## Objective

Create a 4-to-1 Multiplexer behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `mux_4to1`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `d3`, `d2`, `d1`, `d0`, `sel1`, `sel0`, `y`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Combinational: output `y` passes the selected input.
  - Selection: `SEL = {sel1, sel0}`: 00→d0, 01→d1, 10→d2, 11→d3.
  - Updates whenever any input changes.
- **Output**: use `transition()`. No `idt` or current-domain constructs.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `mux_4to1.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Sets data inputs to distinctive voltages: d0=0.1V, d1=0.3V, d2=0.6V, d3=0.8V
- Walks through all 4 selection cases (00, 01, 10, 11) with 100ns each
- Saves signals: `d0`, `d1`, `d2`, `d3`, `sel1`, `sel0`, `y`
- Runs transient for 420ns

## Deliverable

Two files:
1. `mux_4to1.va` - the Verilog-A behavioral model
2. `tb_mux_4to1.scs` - the Spectre testbench

Expected behavior:
- When sel0=0, sel1=0: y should output d0 value (~0.1V in test)
- When sel0=1, sel1=0: y should output d1 value (~0.3V in test)
- When sel0=0, sel1=1: y should output d2 value (~0.6V in test)
- When sel0=1, sel1=1: y should output d3 value (~0.8V in test)


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=420n maxstep=1n errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `d0`, `d1`, `d2`, `d3`, `sel1`, `sel0`, `y`, `time`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `d0`, `d1`, `d2`, `d3`, `sel1`, `sel0`.
