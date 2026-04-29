Write a pure Verilog-A module named `v2_adc_dac_keywordless_settled_4b`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Describe the sampled decision and reconstructed held level without ADC/DAC wording.

Public interface:
- Inputs: `sense_value`, `cadence`, `clear_n`, `vdd`, `vss`.
- Outputs: `dec3, dec2, dec1, dec0`, `estimate_level`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
