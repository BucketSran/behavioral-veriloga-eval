Write only the pure Verilog-A DUT module named `balanced_analog_limiter`.

Do not include a testbench. The evaluator will use a fixed public harness.

Core function: analog limiter.
Behavioral intent: Model a bounded analog transfer that follows the input in the middle range and clamps outside limits.

Public interface:
- Inputs: `raw_level, vdd, vss`.
- Outputs: `limited_level`.

Compatibility requirements:
- Use voltage-domain electrical ports only.
- Be compatible with real Cadence Spectre.
- Declare port direction and electrical discipline separately.
- Drive output targets with `transition(...)`.
- Do not use current contributions, `ddt()`, or `idt()`.

Public evaluation contract:
- The checker reads the saved public input/output waveform columns.
- The task should exercise all required observable behavior, including low/high or below/inside/above regions where applicable.
