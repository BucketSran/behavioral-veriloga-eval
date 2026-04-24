Write a Verilog-A module named `simultaneous_event_order_ref`.

# Task: simultaneous_event_order_smoke

## Objective

Write a Verilog-A model where an absolute timer event and a `cross()` event happen at the same nominal times, and the final plateau level reveals the execution order.

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
