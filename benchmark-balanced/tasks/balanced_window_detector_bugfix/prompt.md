The following Verilog-A module named `balanced_window_detector` has a behavioral bug. Fix it without changing the public interface.

```verilog-a
`include "constants.vams"
`include "disciplines.vams"

module balanced_window_detector(sensor_level, vdd, vss, inside_window, below_window, above_window);
    input sensor_level, vdd, vss;
    output inside_window, below_window, above_window;
    electrical sensor_level, vdd, vss, inside_window, below_window, above_window;
    parameter real lo = 0.25;
    parameter real hi = 0.65;
    parameter real tr = 40p;
    real inside_t;
    real below_t;
    real above_t;

    analog begin
        below_t = (V(sensor_level) > hi) ? V(vdd) : V(vss);
        above_t = (V(sensor_level) < lo) ? V(vdd) : V(vss);
        inside_t = (V(sensor_level) >= lo && V(sensor_level) <= hi) ? V(vdd) : V(vss);
        V(inside_window) <+ transition(inside_t, 0.0, tr, tr);
        V(below_window) <+ transition(below_t, 0.0, tr, tr);
        V(above_window) <+ transition(above_t, 0.0, tr, tr);
    end
endmodule
```

Return exactly one fixed Verilog-A file named `dut.va`.

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
