Write a Verilog-A module named `edge_triggered_latch`.

# Task: dff_rst_p2p5

## Objective

Create a single-bit storage element behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench. The element captures an input value on a rising edge and holds it, with a priority override that forces the output low.

## Specification

- **Module name**: `edge_triggered_latch`
- **Ports** (all `electrical`, exactly as named):
  `supply_hi`, `supply_lo`, `sample_in`, `strobe`, `force_low`, `state`, `state_n`
- **Parameters**: `tedge` (real, default 50p)
- **Behavior**:
  - On rising edge of `strobe`:
    - If `force_low` is HIGH, `state` goes LOW (priority override)
    - Otherwise, `state` samples `sample_in`
  - `state_n` is always the complement of `state`
  - Threshold at `(supply_hi - supply_lo)/2` for level detection
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `edge_triggered_latch.va` via `ahdl_include`
- Provides supply_hi=0.9V, supply_lo=0V
- Generates strobe and input signals for sample_in, force_low
- Saves signals: `strobe`, `sample_in`, `force_low`, `state`, `state_n`
- Runs transient for ~50ns

## Deliverable

Two files:
1. `edge_triggered_latch.va` - the Verilog-A behavioral model
2. `tb_edge_triggered_latch.scs` - the Spectre testbench

Expected behavior:
- state follows sample_in on rising strobe edge when force_low is low
- force_low=1 forces state=0 regardless of sample_in
- state_n is always the logical complement of state

Ports:
- `SUPPLY_HI`: inout electrical
- `SUPPLY_LO`: inout electrical
- `SAMPLE_IN`: input electrical
- `STROBE`: input electrical
- `FORCE_LOW`: input electrical
- `STATE`: output electrical
- `STATE_N`: output electrical

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=50n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `strobe`, `sample_in`, `force_low`, `state`, `state_n`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- The `force_low` input must be asserted only for explicit priority-override
  checks, then deasserted early enough and kept deasserted through the
  post-override checking window.
- The `strobe` input must provide enough valid rising edges after `force_low`
  is released for the checker to sample settled outputs.
- The `sample_in` input must provide both high and low values at different
  strobe edges, including during the override window.
- Sequential outputs are sampled shortly after strobe edges, so drive outputs
  with stable held state variables and `transition()` targets.
- Public stimulus nodes used by the reference harness include: `supply_hi`,
  `supply_lo`, `strobe`, `sample_in`, `force_low`.
