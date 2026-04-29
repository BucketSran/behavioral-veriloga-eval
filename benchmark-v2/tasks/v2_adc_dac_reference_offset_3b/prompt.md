Write a pure Verilog-A module named `v2_adc_dac_reference_offset_3b`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Use shifted reference endpoints and checker tolerance around code-centered reconstruction.

Public interface:
- Inputs: `external_drive`, `cadence`, `clear_n`, `vdd`, `vss`.
- Outputs: `q2, q1, q0`, `reconstructed_level`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
