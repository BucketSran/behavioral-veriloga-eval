Write a Verilog-A module named `phase_accumulator_timer_wrap_ref`.

# Task: phase_accumulator_timer_wrap_smoke

## Objective

Write a Verilog-A phase accumulator that advances on an absolute timer, wraps manually at phase 1.0, and derives both a phase monitor and a clock output from that wrapped state.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `clk_out`: output electrical
- `phase_out`: output electrical

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
tran tran stop=75n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `clk_out`, `phase_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`.
