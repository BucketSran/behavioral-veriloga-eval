Write a pure Verilog-A module named `v2_adc_dac_alias_shared_state_3b_offset`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Use 3-bit decision outputs with aliased input/output names and require one shared sampled state for code and reconstruction.

Public interface:
- Inputs: `measured_level`, `sample_clock`, `clear_n`, `vdd`, `vss`.
- Outputs: `bit2, bit1, bit0`, `held_level`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
