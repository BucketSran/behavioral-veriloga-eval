Write a pure Verilog-A module named `v2_adc_dac_calibrated_chain_settled`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Compose sampled code/reconstruction with an offset-search settled flag; final output must use calibrated offset after search.

Public interface:
- Inputs: `external_drive`, `cadence`, `clear_n`, `vdd`, `vss`.
- Outputs: `q3, q2, q1, q0`, `reconstructed_level`, `settled`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
