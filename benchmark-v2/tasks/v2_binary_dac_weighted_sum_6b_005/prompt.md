Write a pure Verilog-A module named `v2_binary_dac_weighted_sum_6b_005`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Perturb a binary-weighted analog reconstruction task with width and naming changes.

Public interface:
- Inputs: `input0, input1, input2, input3, input4, input5`, `vdd`, `vss`.
- Outputs: `recon_value`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
