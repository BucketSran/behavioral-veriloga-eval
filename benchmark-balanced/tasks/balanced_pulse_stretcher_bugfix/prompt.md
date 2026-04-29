The following Verilog-A module named `balanced_pulse_stretcher` has a behavioral bug. Fix it without changing the public interface.

```verilog-a
`include "constants.vams"
`include "disciplines.vams"

module balanced_pulse_stretcher(event_in, vdd, vss, stretched_pulse);
    input event_in, vdd, vss;
    output stretched_pulse;
    electrical event_in, vdd, vss, stretched_pulse;
    parameter real vth = 0.45;
    parameter real tr = 40p;

    analog begin
        V(stretched_pulse) <+ transition((V(event_in) >= vth) ? V(vdd) : V(vss), 0.0, tr, tr);
    end
endmodule
```

Return exactly one fixed Verilog-A file named `dut.va`.

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
