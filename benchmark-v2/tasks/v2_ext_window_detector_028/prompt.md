Write a pure Verilog-A module named `v2_ext_window_detector_028`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Classify a sensor voltage into below/inside/above window flags.

Public interface:
- Inputs: `measured_voltage`, `vdd`, `vss`.
- Outputs: `inside_window`, `below_window`, `above_window`.
Behavior: classify whether the sensor level is below, inside, or above a voltage window with mutually consistent flags.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
