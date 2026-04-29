Write a pure Verilog-A module named `v2_dwa_circular_cursor_008`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Describe rotating unit-cell selection with cursor/window wording and wraparound checks.

Public interface:
- Inputs: `advance`, `clear_n`, `qty2_0, qty2_1, qty2_2`, `vdd`, `vss`.
- Outputs: `cell0, cell1, cell2, cell3, cell4, cell5, cell6, cell7`.
Behavior: rotate a contiguous active-cell window on each advance event; do not randomize or scramble the selection.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
