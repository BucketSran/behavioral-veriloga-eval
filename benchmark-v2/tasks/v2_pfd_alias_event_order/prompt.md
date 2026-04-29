Write a pure Verilog-A module named `v2_pfd_alias_event_order`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Rename ref/div to early_event and late_event and outputs to accelerate/retard pulses.

Public interface:
- Inputs: `early_event`, `late_event`, `vdd`, `vss`.
- Outputs: `raise_pulse`, `lower_pulse`.
Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
