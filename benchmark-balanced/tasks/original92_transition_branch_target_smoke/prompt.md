Write a Verilog-A module named `transition_branch_target_ref`.

# Task: transition_branch_target_smoke

## Objective

Write a Verilog-A model that updates a transition-driven output target inside a conditional branch on each clock edge.

## Specification

- **Module name**: `transition_branch_target_ref`
- **Ports**: `mode`, `clk`, `out`, `VDD`, `VSS` - all `electrical`
- **Behavior**:
  - On each rising edge of `clk`, set the target HIGH when `mode` is HIGH, otherwise LOW.
  - Drive `out` using `transition(target_q, ...)`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `mode`: input electrical
- `clk`: input electrical
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
tran tran stop=90n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `mode`, `clk`, `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `mode`, `clk`.
