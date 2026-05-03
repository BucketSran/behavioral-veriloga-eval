Write a Verilog-A module named `simultaneous_event_order_ref`.

# Task: simultaneous_event_order_smoke

## Objective

Write a Verilog-A model where an absolute timer event and a true rising `cross()` event occur in a controlled, deterministic order, and the final plateau level reveals that order.

This task intentionally avoids exact-threshold touch and same-time race semantics:

- The timer events should occur at 10 ns, 30 ns, 50 ns, and 70 ns.
- The `ref` waveform must rise through the crossing threshold shortly after each timer event, not merely touch the threshold and return.
- A stable reference setup is `V(ref)` pulsing from 0 V to 0.9 V with `vth=0.45 V`, `rise=50 ps`, and timer events at the pulse delay; the true rising `cross(V(ref)-vth,+1)` then occurs about 25 ps after each timer.
- Do not use a PWL waveform whose peak is exactly equal to the threshold; that creates an exact-touch ambiguity rather than a true crossing.
- Do not rely on two same-time event blocks writing the same variable in an unspecified queue order.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref`: input electrical
- `out`: output electrical

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `ref`.
- The four settled output plateaus in 12-18 ns, 32-38 ns, 52-58 ns, and 72-78 ns should form a roughly evenly spaced increasing ramp, reflecting timer-then-cross ordering on each cycle.
