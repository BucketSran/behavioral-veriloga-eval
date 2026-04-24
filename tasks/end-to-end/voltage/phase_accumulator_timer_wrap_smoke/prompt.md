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
