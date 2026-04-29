Write a pure Verilog-A module named `v2_ext_limiter_model_003`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Model a bounded analog transfer that follows midrange input but clamps outside lower and upper limits.

Public interface:
- Inputs: `raw_level`, `vdd`, `vss`.
- Outputs: `limited_level`.
Behavior: pass the input through an analog limiter with lower and upper clamps; do not emit an unconstrained follower.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
