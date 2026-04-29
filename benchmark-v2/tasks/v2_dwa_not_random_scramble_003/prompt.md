Write a pure Verilog-A module named `v2_dwa_not_random_scramble_003`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Use a deterministic rotating contiguous unit-cell window; random scramble or static selection is forbidden.

Public interface:
- Inputs: `selection_event`, `release_n`, `qty0_0, qty0_1, qty0_2`, `vdd`, `vss`.
- Outputs: `unit0, unit1, unit2, unit3, unit4, unit5, unit6, unit7`.
Behavior: rotate a contiguous active-cell window on each advance event; do not randomize or scramble the selection.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
