Write a Verilog-A module named `track_and_freeze`.

Create a voltage-domain behavioral module that, on a rising transition of a
command input, captures the instantaneous value of an analog input and freezes
the output at that captured level until the next command transition.

Behavioral intent:

- `sample_cmd` receives a binary signal. Each rising transition of `sample_cmd`
  (when its voltage crosses the logic threshold upward) is an active capture
  event. At that moment, the instantaneous voltage on `analog_in` is captured.
- `held_value` is the output. It must be driven to the captured level via
  `transition()`. Between command edges, `held_value` must remain constant at
  the last captured level.
- `supply_hi` and `supply_lo` are the power supply rails. The output must be
  able to swing within the supply range.
- The output must be driven with `transition()`; do not use `idt()`, `ddt()`,
  or `I() <+`.

Ports:
- `supply_hi`: inout electrical
- `supply_lo`: inout electrical
- `analog_in`: input electrical
- `sample_cmd`: input electrical
- `held_value`: output electrical

Parameters:
- `vth` (real, default 0.45): logic threshold in volts
- `tedge` (real, default 100p): output transition time in seconds

Constraints:

- This is NOT a continuous follower (buffer) — the output must remain frozen
  between command edges.
- This is NOT an integrator or a signal tracker with slewing between captures.
- Do NOT add aperture delay or droop behavior.

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=1u maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `analog_in`, `sample_cmd`, `held_value`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- The `sample_cmd` input must provide a periodic pulse with both high and low
  phases, so that the checker can observe both capture and freeze intervals.
- The `analog_in` input must provide a time-varying signal that changes
  measurably between `sample_cmd` rising edges, so that correct capture
  behavior is distinguishable from a constant output.
- Output transitions must be driven with `transition()` to avoid instantaneous
  step changes that may cause simulator convergence issues.
- Public stimulus nodes used by the reference harness include: `analog_in`,
  `sample_cmd`.
