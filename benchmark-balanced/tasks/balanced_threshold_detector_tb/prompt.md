Given a voltage-domain DUT module named `balanced_threshold_detector`, generate only a Spectre/EVAS testbench.

The DUT file will be available as `dut.va`; include it with `ahdl_include "dut.va"` and instantiate by positional ports.

Core function: threshold detector.
Behavioral intent: Convert a single sensor voltage into a rail-referenced decision level using threshold behavior.

Public interface:
- Inputs: `sense_level, vdd, vss`.
- Outputs: `decision_level`.

Compatibility requirements:
- Use voltage-domain electrical ports only.
- Be compatible with real Cadence Spectre.
- Declare port direction and electrical discipline separately.
- Drive output targets with `transition(...)`.
- Do not use current contributions, `ddt()`, or `idt()`.

Public evaluation contract:
- The checker reads the saved public input/output waveform columns.
- The task should exercise all required observable behavior, including low/high or below/inside/above regions where applicable.
