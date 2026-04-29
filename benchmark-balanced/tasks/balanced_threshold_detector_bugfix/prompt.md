The following Verilog-A module named `balanced_threshold_detector` has a behavioral bug. Fix it without changing the public interface.

```verilog-a
`include "constants.vams"
`include "disciplines.vams"

module balanced_threshold_detector(sense_level, vdd, vss, decision_level);
    input sense_level, vdd, vss;
    output decision_level;
    electrical sense_level, vdd, vss, decision_level;
    parameter real threshold = 0.45;
    parameter real tr = 40p;
    real out_t;

    analog begin
        out_t = (V(sense_level) < threshold) ? V(vdd) : V(vss);
        V(decision_level) <+ transition(out_t, 0.0, tr, tr);
    end
endmodule
```

Return exactly one fixed Verilog-A file named `dut.va`.

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
