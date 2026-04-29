Write a pure Verilog-A module named `v2_divider_alias_odd_ratio_phase`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Describe an odd-ratio event divider with renamed event input and tick output.

Public interface:
- Inputs: `advance`, `clear_n`, `vdd`, `vss`.
- Outputs: `tick_out`.
Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
