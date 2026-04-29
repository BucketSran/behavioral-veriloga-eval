Write a pure Verilog-A module named `v2_binary_dac_not_thermometer_6b_014`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require binary-weighted reconstruction and explicitly reject thermometer or unary active-count behavior.

Public interface:
- Inputs: `scale0, scale1, scale2, scale3, scale4, scale5`, `vdd`, `vss`.
- Outputs: `recon_value`.
Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
