Write a pure Verilog-A module named `v2_ext_threshold_detector_025`.

Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.
The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.

Mechanism intent: Convert a sensor level into a digital-like voltage decision using threshold behavior.

Public interface:
- Inputs: `sensor_reading`, `vdd`, `vss`.
- Outputs: `trip_flag`.
Behavior: produce a voltage-domain decision level from a threshold crossing; this is a behavioral threshold detector, not an analog gain buffer.

The testbench should exercise the observable behavior and save every public input/output used by the checker.
