Write a Verilog-A module named `and_gate`.

# Task: and_gate_smoke

## Objective

Create an AND gate behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `and_gate`
- **Ports** (all `electrical`, exactly as named): `a`, `b`, `y`
- **Parameters**: `vdd` (real, default 1.8), `tedge` (real, default 10p)
- **Behavior**:
  - `y` is HIGH when both `a` AND `b` are HIGH (above vdd/2)
  - `y` is LOW otherwise
  - Output HIGH = vdd, LOW = 0
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `and_gate.va` via `ahdl_include`
- Tests all 4 input combinations: (0,0), (0,1), (1,0), (1,1)
- Each combination for 2ns, total 8ns run
- Saves signals: `a`, `b`, `y`

## Deliverable

Two files:
1. `and_gate.va` - the Verilog-A behavioral model
2. `tb_and_gate.scs` - the Spectre testbench

Ports:
- `A`: input electrical
- `B`: input electrical
- `Y`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=8n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `a`, `b`, `y`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `a`, `b`.
