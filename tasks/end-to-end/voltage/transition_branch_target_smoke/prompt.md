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
