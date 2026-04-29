Write a pure Verilog-A module named `v2_counter_not_gray_code_binary_alias`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Require observable binary counter state and explicitly reject Gray-code one-bit-change behavior.

Public interface:
- Inputs: `advance`, `clear_n`, `vdd`, `vss`.
- Outputs: `tick_out, cnt0, cnt1, cnt2, cnt3`.
Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
