Write a pure Verilog-A module named `v2_binary_dac_alias_weighted_5b`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Use weighted input names and a 5-bit binary reconstruction target.

Public interface:
- Inputs: `weight0, weight1, weight2, weight3, weight4`, `vdd`, `vss`.
- Outputs: `analog_sum`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
