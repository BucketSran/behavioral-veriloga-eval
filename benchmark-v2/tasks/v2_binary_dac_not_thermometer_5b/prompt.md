Write a pure Verilog-A module named `v2_binary_dac_not_thermometer_5b`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Explicitly reject thermometer/unary active-count coding; each input line has binary place value.

Public interface:
- Inputs: `weight0, weight1, weight2, weight3, weight4`, `vdd`, `vss`.
- Outputs: `analog_sum`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
