Write a pure Verilog-A module named `v2_ext_pulse_stretcher_029`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Convert each rising event into a finite-width voltage pulse and return low after the pulse window.

Public interface:
- Inputs: `arrival_mark`, `vdd`, `vss`.
- Outputs: `one_shot_level`.
Behavior: convert each rising input event into a finite-width voltage pulse, then return low.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
