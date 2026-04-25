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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=4n maxstep=5p
```

Required public waveform columns in `tran.csv`:

- `time`, `out_p`, `out_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `gnd`, `clk`, `vinp`, `vinn`.
