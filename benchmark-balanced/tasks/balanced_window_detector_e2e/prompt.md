Write a pure Verilog-A module named `balanced_window_detector` and a minimal Spectre/EVAS testbench.

Return two files: `dut.va` and `tb_ref.scs`.

Core function: window detector.
Behavioral intent: Classify a sensor voltage into below-window, inside-window, and above-window flags.

Public interface:
- Inputs: `sensor_level, vdd, vss`.
- Outputs: `inside_window, below_window, above_window`.

Compatibility requirements:
- Use voltage-domain electrical ports only.
- Be compatible with real Cadence Spectre.
- Declare port direction and electrical discipline separately.
- Drive output targets with `transition(...)`.
- Do not use current contributions, `ddt()`, or `idt()`.

Public evaluation contract:
- The checker reads the saved public input/output waveform columns.
- The task should exercise all required observable behavior, including low/high or below/inside/above regions where applicable.
