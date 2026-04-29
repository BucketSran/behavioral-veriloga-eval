The following Verilog-A module named `balanced_analog_limiter` has a behavioral bug. Fix it without changing the public interface.

```verilog-a
`include "constants.vams"
`include "disciplines.vams"

module balanced_analog_limiter(raw_level, vdd, vss, limited_level);
    input raw_level, vdd, vss;
    output limited_level;
    electrical raw_level, vdd, vss, limited_level;
    parameter real vlo = 0.18;
    parameter real vhi = 0.72;
    parameter real tr = 40p;
    real y;

    analog begin
        y = V(raw_level);

        V(limited_level) <+ transition(y, 0.0, tr, tr);
    end
endmodule
```

Return exactly one fixed Verilog-A file named `dut.va`.

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
