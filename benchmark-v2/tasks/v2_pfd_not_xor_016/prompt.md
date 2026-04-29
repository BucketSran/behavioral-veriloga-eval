Write a pure Verilog-A module named `v2_pfd_not_xor_016`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Generate event-order pulses with internal state and reset timing; a stateless XOR phase detector is forbidden.

Public interface:
- Inputs: `lead_edge`, `lag_edge`, `vdd`, `vss`.
- Outputs: `raise_pulse`, `lower_pulse`.
Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
