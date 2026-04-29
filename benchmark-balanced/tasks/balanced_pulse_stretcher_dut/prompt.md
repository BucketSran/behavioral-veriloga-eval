Write only the pure Verilog-A DUT module named `balanced_pulse_stretcher`.

Do not include a testbench. The evaluator will use a fixed public harness.

Core function: event pulse stretcher.
Behavioral intent: Convert each rising input event into a finite-width output pulse and return low afterwards.

Public interface:
- Inputs: `event_in, vdd, vss`.
- Outputs: `stretched_pulse`.

Compatibility requirements:
- Use voltage-domain electrical ports only.
- Be compatible with real Cadence Spectre.
- Declare port direction and electrical discipline separately.
- Drive output targets with `transition(...)`.
- Do not use current contributions, `ddt()`, or `idt()`.

Public evaluation contract:
- The checker reads the saved public input/output waveform columns.
- The task should exercise all required observable behavior, including low/high or below/inside/above regions where applicable.
