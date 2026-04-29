Create only a Spectre/EVAS testbench for the core function below.
The DUT Verilog-A model will be provided by the evaluator.

Core function family: analog-events.
Balanced task-form completion derived from original task: `cross_interval_163p333_smoke`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

Write a Verilog-A module named `cross_interval_163p333_ref`.

# Task: cross_interval_163p333_smoke

## Objective

Write a Verilog-A event-time interval probe that records the elapsed time between two rising `cross()` events.

## Specification

- **Module name**: `cross_interval_163p333_ref`
- **Ports**: `VDD`, `VSS`, `a`, `b`, `delay_out`, `seen_out` - all `electrical`
- **Behavior**:
  - Wait for a rising `cross()` on input `a` at threshold `0.45 V`; record `t_a = $abstime`.
  - Wait for a rising `cross()` on input `b` at threshold `0.45 V`; record `t_b = $abstime`.
  - Output the measured interval `(t_b - t_a)` scaled as `delay_out = VDD * delay_ps / 200`, where `delay_ps` is in ps.
  - Drive `seen_out` HIGH after both crossings have been observed.
  - The reference testbench places the two crossing centers `163.333 ps` apart.

## Constraints

- .., +1))` and `$abstime` inside the event bodies.
- ..)` for outputs.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, `idt()`, or matrix/current-domain constructs.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `a`: input electrical
- `b`: input electrical
- `delay_out`: output electrical
- `seen_out`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=12n maxstep=5p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `delay_out`, `seen_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `a`, `b`.
