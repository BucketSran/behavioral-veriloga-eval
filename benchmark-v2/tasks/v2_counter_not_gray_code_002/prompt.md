Write a pure Verilog-A module named `v2_counter_not_gray_code_002`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require synchronous counted-event behavior; reject Gray-code or asynchronous toggle shortcuts when binary state is requested.

Public interface:
- Inputs: `capture_tick`, `clear_n`, `vdd`, `vss`.
- Outputs: `divided_tick, cnt2_0, cnt2_1, cnt2_2, cnt2_3`.
Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
