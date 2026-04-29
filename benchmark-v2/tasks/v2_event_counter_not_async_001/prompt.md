Write a pure Verilog-A module named `v2_event_counter_not_async_001`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require synchronous counted-event behavior; reject Gray-code or asynchronous toggle shortcuts when binary state is requested.

Public interface:
- Inputs: `sample_event`, `clear_n`, `vdd`, `vss`.
- Outputs: `slow_event`.
Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
