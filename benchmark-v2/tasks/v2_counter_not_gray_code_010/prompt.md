Write a pure Verilog-A module named `v2_counter_not_gray_code_010`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require synchronous counted-event behavior; reject Gray-code or asynchronous toggle shortcuts when binary state is requested.

Public interface:
- Inputs: `cadence`, `clear_n`, `vdd`, `vss`.
- Outputs: `divided_tick, cnt1_0, cnt1_1, cnt1_2, cnt1_3`.
Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
