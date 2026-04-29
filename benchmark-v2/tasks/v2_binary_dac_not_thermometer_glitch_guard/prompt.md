Write a pure Verilog-A module named `v2_binary_dac_not_thermometer_glitch_guard`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require binary-weighted reconstruction with a guard output and reject thermometer active-count coding.

Public interface:
- Inputs: `weight0, weight1, weight2, weight3`, `vdd`, `vss`.
- Outputs: `analog_sum`, `glitch_guard`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
