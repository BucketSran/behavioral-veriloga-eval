Write a pure Verilog-A module named `v2_ext_limiter_model_007`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Model a bounded analog transfer that follows midrange input but clamps outside lower and upper limits.

Public interface:
- Inputs: `unbounded_signal`, `vdd`, `vss`.
- Outputs: `clamped_level`.
Behavior: pass the input through an analog limiter with lower and upper clamps; do not emit an unconstrained follower.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
