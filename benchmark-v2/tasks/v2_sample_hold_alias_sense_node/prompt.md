Write a pure Verilog-A module named `v2_sample_hold_alias_sense_node`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Rename input to sense_node and clock to capture_strobe while requiring held output between strobes.

Public interface:
- Inputs: `sense_node`, `capture`, `vdd`, `vss`.
- Outputs: `latched_level`.
Behavior: sample only at capture events and hold between events. Do not build a continuous follower.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
