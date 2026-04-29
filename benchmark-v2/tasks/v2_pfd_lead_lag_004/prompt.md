Write a pure Verilog-A module named `v2_pfd_lead_lag_004`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Perturb event-order pulse generation using lead/lag aliases and optional lock indication.

Public interface:
- Inputs: `phase_a`, `phase_b`, `vdd`, `vss`.
- Outputs: `raise_pulse`, `lower_pulse`.
Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
