Write a pure Verilog-A module named `v2_sample_hold_latched_level_015`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Perturb event-captured held-level behavior using renamed sense/capture/output roles.

Public interface:
- Inputs: `sense_level`, `cadence`, `vdd`, `vss`.
- Outputs: `remembered_level`.
Behavior: sample only at capture events and hold between events. Do not build a continuous follower.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
