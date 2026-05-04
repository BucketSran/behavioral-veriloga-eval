Write a Verilog-A module named `event_divider_with_pulse`.

# Task: clk_divider_p4p5p6

## Objective

Create a behavioral module that performs two coordinated functions on a periodic
binary event input: a slower toggling output and a completion pulse output.

## Specification

- **Module name**: `event_divider_with_pulse`
- **Ports** (all `electrical`, exactly as named):
  `cadence`, `clear`, `toggled`, `tick`
- **Parameters**: `vth` (real, default 0.6), `vdd` (real, default 1.2),
  `tedge` (real, default 80p)
- **Behavior**:
  - `cadence` receives a periodic binary signal. Each rising transition of
    `cadence` is a significant event.
  - `clear` is a control signal (active low) that restores the module to its
    initial state. When `clear` is low, all outputs are forced to low and
    internal state is reset.
  - `toggled` is the first output. After `clear` is released, every **fifth**
    rising transition of `cadence` must cause `toggled` to complete one full
    cycle (one low-to-high edge followed later by one high-to-low edge). The
    split is 2 cadence cycles high and 3 cadence cycles low.
  - `tick` is the second output. It produces a short pulse: `tick` goes high
    for exactly one `cadence` period at the moment the divide cycle completes
    (when the internal counter wraps to zero). At all other times `tick` is low.
  - Both outputs must use `transition()` and stable held-state variables.
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

Constraints:

- Do NOT implement the counting logic with a Gray-coded state machine.
- The `tick` pulse is NOT a PWM modulator — its width does not vary with input.
- Do NOT use `@(timer(...))` or `@(delay(...))` to schedule the `tick` pulse
  width. The pulse must be derived from cadence edge counts.
- Every complete divide cycle must produce one `tick` pulse — no skipping or
  swallowing cycles.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `event_divider_with_pulse.va` via `ahdl_include`
- Provides `cadence` (periodic pulse source) and `clear` (reset)
- Saves signals: `cadence`, `clear`, `toggled`, `tick`
- Runs transient for ~400ns (enough for several complete divide cycles)

## Deliverable

Two files:
1. `event_divider_with_pulse.va` - the Verilog-A behavioral model
2. `tb_event_divider_with_pulse.scs` - the Spectre testbench

Expected behavior:
- toggled divides cadence by 5, with a 2-high/3-low pattern
- tick fires a one-cycle pulse each time the divide cycle wraps

Ports:
- `CADENCE`: input electrical
- `CLEAR`: input electrical
- `TOGGLED`: output electrical
- `TICK`: output electrical

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=400n maxstep=1n
```

Required public waveform columns in `tran.csv`:

- `cadence`, `toggled`, `tick`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- The `clear` input must be asserted only for startup, then deasserted early
  enough and kept deasserted through the post-reset checking window.
- The `cadence` input must provide enough valid edges after `clear` is released
  for the checker to sample settled outputs on both `toggled` and `tick`.
- Sequential outputs are sampled shortly after `cadence` edges, so drive outputs
  with stable held state variables and `transition()` targets.
- The `tick` output must be a clean pulse: exactly one cadence period wide, no
  glitches or partial pulses.
- Public stimulus nodes used by the reference harness include: `cadence`,
  `clear`.
