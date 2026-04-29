Given a voltage-domain DUT module named `balanced_window_detector`, generate only a Spectre/EVAS testbench.

The DUT file will be available as `dut.va`; include it with `ahdl_include "dut.va"` and instantiate by positional ports.

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
