Write a pure Verilog-A module named `v2_dwa_window_size_hop`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Change active window size during run and verify pointer advance equals prior active count.

Public interface:
- Inputs: `advance`, `clear_n`, `qty0`, `qty1`, `qty2`, `vdd`, `vss`.
- Outputs: `cell0, cell1, cell2, cell3, cell4, cell5, cell6, cell7`.
Behavior: rotate a contiguous active-cell window on each advance event; do not randomize or scramble the selection.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
