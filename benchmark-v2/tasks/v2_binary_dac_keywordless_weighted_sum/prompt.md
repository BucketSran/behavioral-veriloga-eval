Write a pure Verilog-A module named `v2_binary_dac_keywordless_weighted_sum`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Describe a clocked weighted sum of electrical decision lines without saying DAC, binary, or converter.

Public interface:
- Inputs: `weight0, weight1, weight2, weight3`, `vdd`, `vss`.
- Outputs: `analog_sum`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
