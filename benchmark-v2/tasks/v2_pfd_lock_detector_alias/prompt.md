Write a pure Verilog-A module named `v2_pfd_lock_detector_alias`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Add a late lock indication to event-order pulses using aliased signal names.

Public interface:
- Inputs: `early_event`, `late_event`, `vdd`, `vss`.
- Outputs: `raise_pulse`, `lower_pulse`, `locked`.
Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
