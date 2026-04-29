Write a pure Verilog-A module named `v2_pfd_not_xor_detector`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Explicitly require separate UP/DN event pulses and reject duty-cycle XOR phase comparison.

Public interface:
- Inputs: `early_event`, `late_event`, `vdd`, `vss`.
- Outputs: `raise_pulse`, `lower_pulse`.
Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
