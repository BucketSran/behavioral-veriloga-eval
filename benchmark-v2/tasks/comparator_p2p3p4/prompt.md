Write a Verilog-A module named `differential_detector`.

# Task: comparator_p2p3p4

## Objective

Create a behavioral module with two analog sense inputs and one binary output
that continuously indicates which sense input is at a higher potential.

## Specification

- **Module name**: `differential_detector`
- **Ports** (all `electrical`, exactly as named):
  `supply_hi`, `supply_lo`, `sense_plus`, `sense_minus`, `decision`
- **Parameters**: `tedge` (real, default 100p)
- **Behavior**:
  - `decision` is HIGH when the potential at `sense_plus` exceeds the potential
    at `sense_minus`; LOW otherwise.
  - The output updates continuously — not only on clock edges.
  - Output HIGH = V(supply_hi), LOW = V(supply_lo) — read dynamically from the
    supply ports.
  - The output transitions should have finite edge time (use `transition()`).
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

Constraints:

- This is NOT a StrongArm latch or dynamic regenerative latch.
- This is NOT a clocked sampling circuit — the output updates continuously as
  the input relationship changes.
- Do NOT add hysteresis.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `differential_detector.va` via `ahdl_include`
- Provides supply_hi=0.9V, supply_lo=0V
- Drives `sense_plus` with a rising voltage, `sense_minus` at a fixed reference
- Saves signals: `sense_plus`, `sense_minus`, `decision`
- Runs transient for ~30ns

## Deliverable

Two files:
1. `differential_detector.va` - the Verilog-A behavioral model
2. `tb_differential_detector.scs` - the Spectre testbench

Expected behavior:
- Output flips from LOW to HIGH when sense_plus rises above sense_minus
- Output stays HIGH while sense_plus > sense_minus
- Output is supply-referenced (not fixed-voltage logic levels)

Ports:
- `SUPPLY_HI`: inout electrical
- `SUPPLY_LO`: inout electrical
- `SENSE_PLUS`: input electrical
- `SENSE_MINUS`: input electrical
- `DECISION`: output electrical

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=30n maxstep=0.5n
```

Required public waveform columns in `tran.csv`:

- `sense_plus`, `sense_minus`, `decision`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- Inputs should settle and cross each other within the simulation window so the
  checker can observe a clear LOW→HIGH transition.
- Sequential outputs are driven with `transition()` targets.
- Public stimulus nodes used by the reference harness include: `supply_hi`,
  `supply_lo`, `sense_plus`, `sense_minus`.
