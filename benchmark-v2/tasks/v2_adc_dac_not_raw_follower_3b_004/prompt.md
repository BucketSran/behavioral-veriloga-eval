Write a pure Verilog-A module named `v2_adc_dac_not_raw_follower_3b_004`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require sampled decision bits and one held reconstructed level from the same quantized state; do not let the reconstruction continuously follow the raw input.

Public interface:
- Inputs: `analog_sample`, `strobe`, `clear_n`, `vdd`, `vss`.
- Outputs: `level2, level1, level0`, `latched_level`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
