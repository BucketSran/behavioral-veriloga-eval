Write a pure Verilog-A module named `v2_adc_dac_not_raw_follower_5b_010`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require sampled decision bits and one held reconstructed level from the same quantized state; do not let the reconstruction continuously follow the raw input.

Public interface:
- Inputs: `sense_level`, `cadence`, `clear_n`, `vdd`, `vss`.
- Outputs: `q4, q3, q2, q1, q0`, `held_level`, `settled`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
