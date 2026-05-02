Write a Verilog-A module named `event_divider`.

Create a voltage-domain behavioral module that responds to a periodic binary event
on one port and produces a slower toggling output on another port.

Behavioral intent:

- `cadence` receives a periodic binary signal that alternates between low and high.
  Each rising transition of `cadence` is a significant event.
- `clear` is a control signal (active low) that restores the module to its initial
  internal state. When `clear` is low, the output must be forced to low and internal
  counting must restart.
- `toggled` is the output. After `clear` is released (returns high), every fourth
  rising transition of `cadence` must cause `toggled` to complete one full cycle
  (one low-to-high edge followed later by one high-to-low edge). The high and low
  durations of `toggled` should be approximately equal.
- The output must be driven with stable held-state variables and `transition()`;
  do not use glitchy combinational expressions.

Ports:
- `cadence`: input electrical
- `clear`: input electrical
- `toggled`: output electrical

Constraints:

- Do NOT implement this with a Gray-coded state machine.
- Do NOT use `@(timer(...))` or `@(delay(...))` to schedule output transitions.
- The `clear` signal must be sampled on `cadence` rising edges, not asynchronously
  applied to the output directly.

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=300n maxstep=1n
```

Required public waveform columns in `tran.csv`:

- `cadence_in`, `toggled`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- The `clear`-like input must be asserted only for startup/explicit reset checks,
  then deasserted early enough and kept deasserted through the post-reset
  checking window.
- The `cadence`-like input must provide enough valid events after `clear` is
  released for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after `cadence` edges, so drive outputs
  with stable held state variables and `transition()` targets.
- Public stimulus nodes used by the reference harness include: `cadence_in`,
  `clear`.
