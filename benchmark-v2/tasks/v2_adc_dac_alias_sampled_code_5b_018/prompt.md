Write a pure Verilog-A module named `v2_adc_dac_alias_sampled_code_5b_018`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Perturb the sampled quantize/reconstruct interface with aliased names and width changes.

Public interface:
- Inputs: `observed_level`, `advance_edge`, `clear_n`, `vdd`, `vss`.
- Outputs: `mark4, mark3, mark2, mark1, mark0`, `drive_estimate`.
Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
