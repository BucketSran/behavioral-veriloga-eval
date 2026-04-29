Write a pure Verilog-A module named `v2_adc_dac_alias_sampled_code_5b`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Rename input, clock, output, and decision bits while preserving sampled-code reconstruction.

Public interface:
- Inputs: `measured_level`, `sample_clock`, `clear_n`, `vdd`, `vss`.
- Outputs: `bit4, bit3, bit2, bit1, bit0`, `held_level`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
